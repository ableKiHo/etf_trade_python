import os
import sys
from operator import itemgetter

import numpy as np

from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import create_moving_average_gap_line, is_increase_trend


class DayTradingPrepareNextDay(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF DayTradingPrepareNextDay() class start.")
        self.line.notification("ETF DayTradingPrepareNextDay() class start.")

        self.all_etc_info_event_loop = QEventLoop()
        self.etf_info_event_loop = QEventLoop()
        self.etf_day_info_event_loop = QEventLoop()
        self.tr_opt10080_info_event_loop = QEventLoop()

        self.screen_all_etf_stock = "4000"
        self.screen_etf_stock = "5000"
        self.screen_etf_day_stock = "4050"
        self.screen_opt10080_info = "4060"

        self.analysis_etf_target_dict = {}
        self.target_etf_stock_dict = {}
        self.target_etf_day_info_dict = []
        self.event_slots()

        self.line.notification("ETF DAY TRADE PREPARE AUTO TRADE START")
        self.prepare_next_day()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def prepare_next_day(self):
        self.logging.logger.info("prepare_next_day")
        self.file_delete()
        self.get_all_etf_stock()
        self.get_etf_stock_info()
        self.get_etf_daily_candle_info()

        QTest.qWait(5000)
        self.create_target_etf_stock_file()

        self.line.notification("시스템 종료")
        QTest.qWait(5000)
        sys.exit()

    def file_delete(self):
        self.logging.logger.info("file_delete")
        if os.path.isfile(self.target_etf_file_path):
            os.remove(self.target_etf_file_path)
            self.logging.logger.info("remove %s" % self.target_etf_file_path)

    def get_all_etf_stock(self, sPrevNext="0"):
        self.logging.logger.info("get_all_etf_stock")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TAXATION_TYPE, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.COMPARED_TO_NAV, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MANAGER, "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40004, "opt40004", sPrevNext, self.screen_all_etf_stock)

        self.all_etc_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPT40004:
            self.trdata_slot_opt40004(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081":
            self.trdata_slot_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        if stock_code not in self.analysis_etf_target_dict.keys():
            self.analysis_etf_target_dict.update({stock_code: {"row": []}})
        rows = self.analysis_etf_target_dict[stock_code]["row"]
        new_rows = []
        cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

        for i in range(cnt):
            a = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.CURRENT_PRICE)
            a = int(a.strip())
            c = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TIGHTENING_TIME)
            c = c.strip()

            row = {self.customType.CURRENT_PRICE: a, self.customType.TIGHTENING_TIME: c, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.insert(0, row)

        if len(rows) > 0:
            del rows[0]
            last_register_row = rows[0]
            for add in new_rows:
                if last_register_row[self.customType.TIGHTENING_TIME] < add[self.customType.TIGHTENING_TIME]:
                    rows.insert(0, add)
        else:
            rows = sorted(new_rows, key=itemgetter(self.customType.TIGHTENING_TIME), reverse=True)
        self.analysis_etf_target_dict[stock_code].update({"row": rows})

        self.stop_screen_cancel(self.screen_opt10080_info)
        self.tr_opt10080_info_event_loop.exit()

    def trdata_slot_opt40004(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(rows):
            volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            volume = volume.strip()
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_CODE)
            code = code.strip()
            last_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LAST_PRICE)
            last_price = last_price.strip()
            if int(volume) >= 50000 and int(last_price) <= 50000:

                if code not in self.target_etf_stock_dict:
                    self.target_etf_stock_dict[code] = {}

        if sPrevNext == "2":  # 다음페이지 존재
            self.get_all_etf_stock(sPrevNext="2")
        else:
            self.stop_screen_cancel(self.screen_all_etf_stock)
            self.all_etc_info_event_loop.exit()

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_NAME)
        highest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.HIGHEST_PRICE)
        lowest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.LOWEST_PRICE)
        last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        change_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.THE_DAY_BEFORE)
        current_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)

        market_cap = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.MARTKET_CAP)
        market_cap = market_cap.strip()

        self.logging.logger.info(self.logType.OPT10001_STATUS_LOG % (
            code, highest_stock_price.strip(), lowest_stock_price.strip(), last_stock_price.strip(), change_price.strip(), market_cap)
                                 )

        self.target_etf_stock_dict[code].update({self.customType.STOCK_NAME: code_nm})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_HIGHEST_PRICE: abs(int(highest_stock_price.strip()))})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LOWEST_PRICE: abs(int(lowest_stock_price.strip()))})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LAST_PRICE: abs(int(last_stock_price.strip()))})
        self.target_etf_stock_dict[code].update({self.customType.MARTKET_CAP: int(market_cap)})
        self.target_etf_stock_dict[code].update({self.customType.CURRENT_PRICE: abs(int(current_stock_price.strip()))})

        self.etf_info_event_loop.exit()

    def is_traget_etf_stock(self, value):
        return int(value[self.customType.MARTKET_CAP]) >= 65 and value[self.customType.CURRENT_PRICE] < 50000

    def create_target_etf_stock_file(self):
        self.logging.logger.info("create_target_etf_stock_file")
        for sCode in self.target_etf_stock_dict.keys():
            value = self.target_etf_stock_dict[sCode]
            if self.is_traget_etf_stock(value):
                if self.is_ma_line_analysis(sCode):

                    f = open(self.target_etf_file_path, "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %
                            (sCode, value[self.customType.STOCK_NAME], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                             value[self.customType.LAST_DAY_LOWEST_PRICE], value[self.customType.LAST_DAY_LAST_PRICE],
                             value[self.customType.THE_DAY_BEFORE_AVG], value[self.customType.THE_DAY_BEFORE_MAX],
                             value[self.customType.THE_DAY_BEFORE_MIN]))
                    f.close()

    def is_ma_line_analysis(self, code):
        ma_line_buy_point = self.get_conform_ma_line_case(code)
        return bool(ma_line_buy_point)

    def get_conform_ma_line_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]

        first_tic = analysis_rows[0]

        ma_field_list = ["ma20", "ma5", "ma10"]
        for field in ma_field_list:
            if first_tic[field] == '':
                return {}

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '' or x["ma5"] == '' or x["ma10"] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("analysis_rows > [%s] >> %s " % (code, analysis_rows))

        for field in ma_field_list:
            if first_tic[field] > first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic))
                return {}

        compare_rows = analysis_rows[1:]
        current_price_position_list = [(x, field) for x in compare_rows for field in ma_field_list if x[field] > x[self.customType.CURRENT_PRICE]]
        if len(current_price_position_list) > 0:
            self.logging.logger.info("lower_gap_list check> [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], current_price_position_list))
            return {}

        last_price_list = [item[self.customType.CURRENT_PRICE] for item in compare_rows]
        if not is_increase_trend(last_price_list):
            self.logging.logger.info("is_increase_trend check> [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], last_price_list))
            return {}

        return np.copy.deepcopy(first_tic)

    def get_etf_stock_info(self):
        for sCode in self.target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.logging.logger.info("get_etf_stock_info >> %s" % sCode)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def get_etf_daily_candle_info(self):
        for code in self.target_etf_stock_dict.keys():
            self.logging.logger.info("get_etf_stock_info >> %s" % code)
            self.get_individual_etf_daily_candle_info(code)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)

    def get_individual_etf_daily_candle_info(self, code):
        QTest.qWait(4000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.etf_info_event_loop.exec_()
