import sys

from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


class DayTradingPrepareNextDay(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF DayTradingPrepareNextDay() class start.")
        self.line.notification("ETF DayTradingPrepareNextDay() class start.")

        self.all_etc_info_event_loop = QEventLoop()
        self.etf_info_event_loop = QEventLoop()
        self.etf_day_info_event_loop = QEventLoop()
        self.tr_opt10080_info_event_loop = QEventLoop()
        self.sectors_info_event_loop = QEventLoop()

        self.screen_all_etf_stock = "4000"
        self.screen_etf_stock = "5000"
        self.screen_etf_day_stock = "4050"
        self.screen_opt10080_info = "4060"
        self.screen_sectors_etf_stock = "4100"

        self.main_sectors_dict = {}

        self.analysis_etf_target_dict = {}
        self.target_etf_stock_dict = {}
        self.exclude_target_etf_stock_dict = {}
        self.target_etf_day_info_dict = []
        self.event_slots()

        self.line.notification("ETF DAY TRADE PREPARE AUTO TRADE START")
        self.prepare_next_day()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def prepare_next_day(self):
        self.logging.logger.info("prepare_next_day")
        self.get_main_sectors_info()
        QTest.qWait(5000)
        self.file_delete()
        self.get_all_etf_stock()
        self.get_etf_stock_info()
        self.get_exclude_etf_stock_info()
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

    def get_main_sectors_info(self):
        secotrs_list = ['001', '101']
        for sectors_code in secotrs_list:
            QTest.qWait(5000)
            self.main_sectors_info(sectors_code)
            create_moving_average_gap_line(sectors_code, self.main_sectors_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
            create_moving_average_gap_line(sectors_code, self.main_sectors_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
            is_buy_secotrs_position(sectors_code, self.main_sectors_dict, "row", self.customType.HIGHEST_PRICE, "ma5")
            self.logging.logger.info("self.main_sectors_dict[%s] >> %s" % (sectors_code, self.main_sectors_dict[sectors_code]["is_available_position"]))

    def main_sectors_info(self, secotrs_code, sPrevNext="0"):
        self.logging.logger.info("main_sectors_info")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.SECTORS_CODE, secotrs_code)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt20006", "opt20006", sPrevNext, self.screen_sectors_etf_stock)

        self.sectors_info_event_loop.exec_()

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
        elif sRQName == "tr_opt10001":
            self.trdata_slot_exclude_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081":
            self.trdata_slot_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt20006":
            self.trdata_slot_opt20006(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opt20006(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        sectors_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.SECTORS_CODE)
        sectors_code = sectors_code.strip()

        if sectors_code not in self.main_sectors_dict.keys():
            self.main_sectors_dict.update({sectors_code: {"row": []}})

        new_rows = []
        cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        self.logging.logger.info("trdata_slot_opt20006 stock_code >> %s" % sectors_code)
        for i in range(cnt):
            a = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.CURRENT_PRICE)
            a = abs(int(a.strip()))
            b = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.START_PRICE)
            b = abs(int(b.strip()))
            c = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
            c = c.strip()
            d = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HIGHEST_PRICE)
            d = abs(int(d.strip()))
            e = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LOWEST_PRICE)
            e = abs(int(e.strip()))

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c,
                   self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e,
                   "ma20": '', "ma5": '', "ma10": '', "ma60": '', "ma120": ''}
            new_rows.append(row)

        self.main_sectors_dict[sectors_code].update({"row": new_rows})
        self.stop_screen_cancel(self.screen_sectors_etf_stock)
        self.sectors_info_event_loop.exit()

    def trdata_slot_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        if stock_code not in self.analysis_etf_target_dict.keys():
            self.analysis_etf_target_dict.update({stock_code: {"row": []}})
        new_rows = []
        cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(cnt):
            a = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.CURRENT_PRICE)
            a = abs(int(a.strip()))
            b = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.START_PRICE)
            b = abs(int(b.strip()))
            c = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
            c = c.strip()
            d = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HIGHEST_PRICE)
            d = abs(int(d.strip()))
            e = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LOWEST_PRICE)
            e = abs(int(e.strip()))

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c,
                   self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e,
                   "ma20": '', "ma5": '', "ma10": '', "ma60": '', "ma120": ''}
            new_rows.append(row)

        self.analysis_etf_target_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_opt10080_info_event_loop.exit()

    def trdata_slot_opt40004(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(rows):
            is_match_exclude = False
            volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            volume = volume.strip()
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_CODE)
            code = code.strip()
            code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_NAME)
            code_nm = code_nm.strip()
            last_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LAST_PRICE)
            last_price = last_price.strip()
            if abs(int(volume)) >= 50000 and abs(int(last_price)) <= 50000:
                for exclude in self.exclude_keywords:
                    if str_find(code_nm, exclude):
                        is_match_exclude = True
                        break
                if is_match_exclude is False:
                    if code not in self.target_etf_stock_dict:
                        self.target_etf_stock_dict[code] = {}

                if is_match_exclude is True:
                    if code not in self.exclude_target_etf_stock_dict:
                        self.exclude_target_etf_stock_dict[code] = {}

        if sPrevNext == "2":  # 다음페이지 존재
            self.get_all_etf_stock(sPrevNext="2")
        else:
            self.stop_screen_cancel(self.screen_all_etf_stock)
            self.all_etc_info_event_loop.exit()

    def trdata_slot_exclude_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_NAME)
        highest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.HIGHEST_PRICE)
        lowest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.LOWEST_PRICE)
        last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        change_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.THE_DAY_BEFORE)
        change_price = change_price.strip()

        market_cap = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.MARTKET_CAP)
        market_cap = market_cap.strip()

        self.logging.logger.info(self.logType.OPT10001_STATUS_LOG % (
            code, highest_stock_price.strip(), lowest_stock_price.strip(), last_stock_price.strip(), change_price, market_cap)
                                 )
        if int(market_cap) >= 80 and int(change_price) > 0:
            self.exclude_target_etf_stock_dict[code].update({self.customType.STOCK_NAME: code_nm.strip()})
            self.exclude_target_etf_stock_dict[code].update({self.customType.LAST_DAY_HIGHEST_PRICE: abs(int(highest_stock_price.strip()))})
            self.exclude_target_etf_stock_dict[code].update({self.customType.LAST_DAY_LOWEST_PRICE: abs(int(lowest_stock_price.strip()))})
            self.exclude_target_etf_stock_dict[code].update({self.customType.LAST_DAY_LAST_PRICE: abs(int(last_stock_price.strip()))})
            self.exclude_target_etf_stock_dict[code].update({self.customType.MARTKET_CAP: int(market_cap)})
        else:
            del self.exclude_target_etf_stock_dict[code]

        self.etf_info_event_loop.exit()

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_NAME)
        highest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.HIGHEST_PRICE)
        lowest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.LOWEST_PRICE)
        last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        change_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.THE_DAY_BEFORE)
        change_price = change_price.strip()

        market_cap = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.MARTKET_CAP)
        market_cap = market_cap.strip()

        self.logging.logger.info(self.logType.OPT10001_STATUS_LOG % (
            code, highest_stock_price.strip(), lowest_stock_price.strip(), last_stock_price.strip(), change_price, market_cap)
                                 )
        if int(market_cap) >= 80 and int(change_price) > 0:
            self.target_etf_stock_dict[code].update({self.customType.STOCK_NAME: code_nm.strip()})
            self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_HIGHEST_PRICE: abs(int(highest_stock_price.strip()))})
            self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LOWEST_PRICE: abs(int(lowest_stock_price.strip()))})
            self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LAST_PRICE: abs(int(last_stock_price.strip()))})
            self.target_etf_stock_dict[code].update({self.customType.MARTKET_CAP: int(market_cap)})
        else:
            del self.target_etf_stock_dict[code]

        self.etf_info_event_loop.exit()

    def create_target_etf_stock_file(self):
        self.logging.logger.info("create_target_etf_stock_file")
        for sCode in self.target_etf_stock_dict.keys():
            value = self.target_etf_stock_dict[sCode]
            if value[self.customType.STOCK_NAME].find(self.customType.INVERSE) >= 0:
                continue

            if value[self.customType.STOCK_NAME].find(self.customType.KOSDAQ) >= 0:
                if not self.main_sectors_dict['101']['is_available_position']:
                    continue
            else:
                if not self.main_sectors_dict['001']['is_available_position']:
                    continue

            if self.is_ma_line_analysis(sCode):
                self.logging.logger.info("pass is_ma_line_analysis %s " % sCode)
                f = open(self.target_etf_file_path, "a", encoding="utf8")
                f.write("%s\t%s\t%s\t%s\t%s\n" %
                        (sCode, value[self.customType.STOCK_NAME], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                         value[self.customType.LAST_DAY_LOWEST_PRICE], value[self.customType.LAST_DAY_LAST_PRICE]))
                f.close()
        for sCode in self.exclude_target_etf_stock_dict.keys():
            value = self.exclude_target_etf_stock_dict[sCode]

            if self.is_ma_line_analysis(sCode):
                self.logging.logger.info("pass is_ma_line_analysis %s " % sCode)
                f = open(self.target_etf_file_path, "a", encoding="utf8")
                f.write("%s\t%s\t%s\t%s\t%s\n" %
                        (sCode, value[self.customType.STOCK_NAME], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                         value[self.customType.LAST_DAY_LOWEST_PRICE], value[self.customType.LAST_DAY_LAST_PRICE]))
                f.close()

    def is_ma_line_analysis(self, code):
        ma_line_buy_point = self.get_conform_ma_line_case(code)
        if not bool(ma_line_buy_point):
            ma_line_buy_point = self.get_conform_cable_tie_case(code)
        if not bool(ma_line_buy_point):
            ma_line_buy_point = self.get_conform_cross_candle_case(code)
        return bool(ma_line_buy_point)

    def get_conform_cross_candle_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 4:
            return {}

        analysis_rows = rows[:4]

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("corss_candle_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]

        if first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
            self.logging.logger.info("first_tic current price position check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        black_candle_compare_rows = analysis_rows[1:]
        black_candle_list = [x for x in black_candle_compare_rows if x[self.customType.START_PRICE] < x[self.customType.CURRENT_PRICE]]
        if len(black_candle_list) > 0:
            self.logging.logger.info("3days black candle check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if first_tic[self.customType.LOWEST_PRICE] < first_tic[self.customType.START_PRICE] <= first_tic[self.customType.CURRENT_PRICE]:
            if first_tic[self.customType.CURRENT_PRICE] <= first_tic[self.customType.HIGHEST_PRICE]:
                highest_gap = first_tic[self.customType.HIGHEST_PRICE] - first_tic[self.customType.CURRENT_PRICE]
                lowest_gap = first_tic[self.customType.START_PRICE] - first_tic[self.customType.LOWEST_PRICE]
                if lowest_gap >= highest_gap:
                    return copy.deepcopy(first_tic)

        self.logging.logger.info("corss_candle check> [%s] >> %s" % (code, first_tic))
        return {}

    def get_conform_cable_tie_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 7:
            return {}

        analysis_rows = rows[:7]

        first_tic = analysis_rows[0]

        ma_field_list = ["ma20", "ma5", "ma10", "ma60", "ma120"]

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '' or x["ma5"] == '' or x["ma10"] == '' or x["ma60"] == '' or x["ma120"] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("cable_tie_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        ma120_line_up_list = [x for x in analysis_rows if x["ma120"] > x[self.customType.CURRENT_PRICE]]
        if len(ma120_line_up_list) > 0:
            self.logging.logger.info("ma120_line_up_list check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        compare_rows = analysis_rows[1:4]
        max_ma5 = max([item["ma5"] for item in compare_rows])
        min_ma5 = min([item["ma5"] for item in compare_rows])
        max_ma10 = max([item["ma10"] for item in compare_rows])
        min_ma10 = min([item["ma10"] for item in compare_rows])
        max_ma20 = max([item["ma20"] for item in compare_rows])
        min_ma20 = min([item["ma20"] for item in compare_rows])
        max_ma60 = max([item["ma60"] for item in compare_rows])
        min_ma60 = min([item["ma60"] for item in compare_rows])
        max_list = [max_ma5, max_ma10, max_ma20, max_ma60]
        min_list = [min_ma5, min_ma10, min_ma20, min_ma60]
        max_value = max(max_list)
        min_value = min(min_list)
        gap = 20
        if max_value - min_value > gap:
            self.logging.logger.info("cable_tie range check > [%s] >> %s / %s / %s" % (code, first_tic["일자"], max_value, min_value))
            return {}

        for field in ma_field_list:
            if first_tic[field] > first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic["일자"]))
                return {}

        ma120_min_value_list = [x for x in analysis_rows if x["ma120"] > max_value]
        if len(ma120_min_value_list) > 0:
            self.logging.logger.info("ma120_line min_value check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        compare_rows = analysis_rows[:3]
        last_price_list = [item[self.customType.CURRENT_PRICE] for item in compare_rows]
        if not is_increase_trend(last_price_list):
            self.logging.logger.info("is_increase_trend check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}
        ma5_list = [item["ma5"] for item in compare_rows]
        if not is_increase_trend(ma5_list):
            self.logging.logger.info("ma5_list_trend check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}
        ma10_list = [item["ma10"] for item in compare_rows]
        if not is_increase_trend(ma10_list):
            self.logging.logger.info("ma10_list_trend check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if first_tic["ma5"] <= first_tic["ma20"] or first_tic["ma10"] <= first_tic["ma60"]:
            self.logging.logger.info("first_tic short line position check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        return copy.deepcopy(first_tic)

    def get_conform_ma_line_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:2]

        first_tic = analysis_rows[0]
        second_tic = analysis_rows[1]

        ma_field_list = ["ma20", "ma5"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("ma_line_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic black candle check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if first_tic[self.customType.LOWEST_PRICE] > first_tic["ma20"] or first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
            self.logging.logger.info("first_tic position check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if second_tic[self.customType.LOWEST_PRICE] > second_tic["ma20"]:
            self.logging.logger.info("second_tic position check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        last_price_list = [item[self.customType.CURRENT_PRICE] for item in analysis_rows]
        inverselist = last_price_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend current check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        return copy.deepcopy(first_tic)

    def get_etf_stock_info(self):
        copy_dict = copy.deepcopy(self.target_etf_stock_dict)
        for sCode in copy_dict.keys():
            QTest.qWait(5000)
            self.logging.logger.info("get_etf_stock_info >> %s" % sCode)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def get_exclude_etf_stock_info(self):
        copy_dict = copy.deepcopy(self.exclude_target_etf_stock_dict)
        for sCode in copy_dict.keys():
            QTest.qWait(5000)
            self.logging.logger.info("get_exclude_etf_stock_info >> %s" % sCode)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10001", "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def get_etf_daily_candle_info(self):
        for code in self.target_etf_stock_dict.keys():
            self.logging.logger.info("get_etf_daily_candle_info >> %s" % code)
            self.get_individual_etf_daily_candle_info(code)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma60", 60)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma120", 120)
        for code in self.exclude_target_etf_stock_dict.keys():
            self.get_individual_etf_daily_candle_info(code)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma60", 60)
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma120", 120)

    def get_individual_etf_daily_candle_info(self, code):
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10080_info_event_loop.exec_()
