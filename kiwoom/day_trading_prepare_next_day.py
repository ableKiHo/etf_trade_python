import sys
import shutil

import numpy
from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from config.customType import CustomType
from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


class DayTradingPrepareNextDay(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF DayTradingPrepareNextDay() class start.")
        self.line.notification("ETF DayTradingPrepareNextDay() class start.")

        self.today = get_today_by_format('%Y%m%d')

        self.all_etc_info_event_loop = QEventLoop()
        self.etf_info_event_loop = QEventLoop()
        self.etf_day_info_event_loop = QEventLoop()
        self.tr_opt10080_info_event_loop = QEventLoop()

        self.screen_all_etf_stock = "4000"
        self.screen_etf_stock = "5000"
        self.screen_etf_day_stock = "4050"
        self.screen_opt10080_info = "4060"

        self.represent_keyword_dict = {self.customType.KOSPI: {}, self.customType.KOSDAQ: {}, '은행': {}, '반도체': {}, 'KRX300': {}, '200TR': {}, '200': {}, 'MSCI': {}, '헬스케어': {}, '고배당': {}}
        # self.recommand_keyword_list = ['TR', '고배당', 'TOP10', '저변동', '성장', '블루칩', '우선주', '배당성장']
        self.recommand_keyword_list = []

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
        self.file_rename_copy()
        self.file_delete()
        self.get_all_etf_stock()
        self.get_etf_stock_info()
        self.get_etf_daily_candle_info()

        QTest.qWait(5000)
        self.create_target_etf_stock_file()

        self.line.notification("시스템 종료")
        QTest.qWait(5000)
        sys.exit()

    def file_rename_copy(self):
        self.logging.logger.info("file_rename_copy")
        # self.target_etf_file_history_path
        if os.path.isfile(self.target_etf_file_path):
            shutil.copy(self.target_etf_file_path, self.target_etf_file_history_path + self.today + ".txt")
            self.logging.logger.info("move %s" % self.target_etf_file_history_path + self.today + ".txt")

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
            f = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            f = abs(int(f.strip()))

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c,
                   self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, self.customType.VOLUME: f,
                   "ma20": '', "ma5": '', "ma10": '', "ma60": '', "ma120": '', "ma3": '', "upper": '', "lower": '', "pb": '', "mfi10": ''}
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
            stock_type = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_TYPE)
            stock_type = stock_type.strip()
            last_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LAST_PRICE)
            last_price = last_price.strip()
            trace_sector_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TRACE_SECTOR_CODE)
            trace_sector_code = trace_sector_code.strip()
            trace_sector_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TRACE_SECTOR_NAME)
            trace_sector_name = trace_sector_name.strip()

            self.logging.logger.info(self.logType.OPT40004_STATUS_LOG % (code, code_nm, stock_type, trace_sector_code, trace_sector_name, volume))
            if abs(int(volume)) >= 10000 and abs(int(last_price)) <= 70000:
                for exclude in self.exclude_keywords:
                    if str_find(code_nm, exclude):
                        is_match_exclude = True
                        break
                if is_match_exclude is False:
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
        highest_stock_price = highest_stock_price.strip()
        lowest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.LOWEST_PRICE)
        lowest_stock_price = lowest_stock_price.strip()
        last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        last_stock_price = last_stock_price.strip()
        change_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.THE_DAY_BEFORE)
        change_price = change_price.strip()

        market_cap = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.MARTKET_CAP)
        market_cap = market_cap.strip()

        self.logging.logger.info(self.logType.OPT10001_STATUS_LOG % (code, highest_stock_price, lowest_stock_price, last_stock_price, change_price, market_cap))
        if int(market_cap) >= 120:
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
            create_flag = True
            if self.is_ma_line_analysis(sCode):
                self.logging.logger.info("pass is_ma_line_analysis %s " % sCode)

                for keyword in self.represent_keyword_dict.keys():
                    if value[self.customType.STOCK_NAME].find(keyword) >= 0 and bool(self.represent_keyword_dict[keyword]):
                        create_flag = False
                    elif value[self.customType.STOCK_NAME].find(keyword) >= 0 and not bool(self.represent_keyword_dict[keyword]):
                        self.represent_keyword_dict[keyword] = copy.deepcopy(value)

                if create_flag is True and sCode not in self.default_stock_list:
                    f = open(self.target_etf_file_path, "a", encoding="utf8")
                    f.write("%s\t%s\t%s\t%s\t%s\n" %
                            (sCode, value[self.customType.STOCK_NAME], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                             value[self.customType.LAST_DAY_LOWEST_PRICE], value[self.customType.LAST_DAY_LAST_PRICE]))
                    f.close()

                    for keyword in self.recommand_keyword_list:
                        if value[self.customType.STOCK_NAME].find(keyword) >= 0:
                            self.line.notification("OPEN API SUGGEST STOCK [%s][%s]" % (sCode, value[self.customType.STOCK_NAME]))

    def is_ma_line_analysis(self, code):
        buy_point = self.get_conform_ma_line_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_ma_line2_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_ma_line3_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_cable_tie_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_cable_tie2_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_cross_candle_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_cross_candle2_case(code)
        if not bool(buy_point):
            buy_point = self.get_pushup_candle_case(code)
        if not bool(buy_point):
            buy_point = self.get_conform_cable_tie3_case(code)
        return bool(buy_point)

    def get_pushup_candle_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 4:
            return {}
        analysis_rows = rows[:4]

        ma_field_list = ["ma3", "ma5", "ma10"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("pushup_candle_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]
        second_tic = analysis_rows[1]
        last_three_day_rows = analysis_rows[1:]

        # 3일동안 종가가 3일선 위에 위치
        # 어제와 오늘의 변동폭(고가-저가)이 오늘이 더 크다
        # 아래 꼬리가 달렸다
        # 3일선 5일선 10일선 정배열
        # 저가가 10일 선 위에 위치
        # 종가가 5일 선 위에 위치
        # 음봉
        # 3일선, 5일선, 10일선 상승중

        ma3_under_list = [x for x in last_three_day_rows if x["ma3"] > x[self.customType.CURRENT_PRICE]]
        if len(ma3_under_list) > 0:
            self.logging.logger.info("ma3_under_list check> [%s]" % code)
            return {}

        tail = first_tic[self.customType.CURRENT_PRICE] - first_tic[self.customType.LOWEST_PRICE]
        first_candle = first_tic[self.customType.HIGHEST_PRICE] - first_tic[self.customType.LOWEST_PRICE]
        second_candle = second_tic[self.customType.HIGHEST_PRICE] - second_tic[self.customType.LOWEST_PRICE]

        if second_candle > first_candle:
            self.logging.logger.info("first_candle range check> [%s]" % code)
            return {}

        if math.trunc((tail/first_candle) * 100) < 60:
            self.logging.logger.info("is pushup candle check> [%s]" % code)
            return {}

        if first_tic["ma3"] >= first_tic["ma5"] >= first_tic["ma10"]:
            pass
        else:
            self.logging.logger.info("is regular arrangement check> [%s]" % code)
            return {}

        if first_tic["ma10"] > first_tic[self.customType.LOWEST_PRICE]:
            self.logging.logger.info("lowest_price position check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        if first_tic["ma5"] > first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("current_price position check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        if first_tic[self.customType.CURRENT_PRICE] > first_tic[self.customType.START_PRICE]:
            self.logging.logger.info("start_price position check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        compare_rows = analysis_rows[:4]
        ma10_list = [item["ma10"] for item in compare_rows]
        ma10_inverselist = ma10_list[::-1]
        if not is_increase_trend(ma10_inverselist):
            self.logging.logger.info("is_increase_ma10 check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        ma5_list = [item["ma5"] for item in compare_rows]
        ma5_inverselist = ma5_list[::-1]
        if not is_increase_trend(ma5_inverselist):
            self.logging.logger.info("is_increase_ma5 check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        ma3_list = [item["ma3"] for item in compare_rows]
        ma3_inverselist = ma3_list[::-1]
        if not is_increase_trend(ma3_inverselist):
            self.logging.logger.info("is_increase_ma3 check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        return copy.deepcopy(first_tic)

    def get_conform_cross_candle2_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 4:
            return {}

        analysis_rows = rows[:4]

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("cross_candle2_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]
        
        # 20일선과 종가 간격 5%이내
        # 양봉
        # 종가가 20일선 위에 위치
        # 20일선 상승중
        # 저가가 2일선 아래에 위치 또는 저가와 20일선 간격체크
        # 망치

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 5.0:
            self.logging.logger.info("ma20_percent check> [%s]  " % code)
            return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s]" % code)
            return {}

        if first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
            self.logging.logger.info("first_tic current price position check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        compare_rows = analysis_rows[:3]
        ma20_list = [item["ma20"] for item in compare_rows]
        ma20_inverselist = ma20_list[::-1]
        if not is_increase_trend(ma20_inverselist):
            self.logging.logger.info("is_increase_ma20 check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        if first_tic[self.customType.LOWEST_PRICE] > first_tic["ma20"] and first_tic[self.customType.LOWEST_PRICE] - first_tic["ma20"] > first_tic[self.customType.CURRENT_PRICE] * 0.005:
            self.logging.logger.info("second_tic position check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if first_tic[self.customType.LOWEST_PRICE] < first_tic[self.customType.START_PRICE] <= first_tic[self.customType.CURRENT_PRICE]:
            if first_tic[self.customType.CURRENT_PRICE] <= first_tic[self.customType.HIGHEST_PRICE]:
                highest_gap = first_tic[self.customType.HIGHEST_PRICE] - first_tic[self.customType.CURRENT_PRICE]
                lowest_gap = first_tic[self.customType.START_PRICE] - first_tic[self.customType.LOWEST_PRICE]
                if lowest_gap >= highest_gap:
                    self.logging.logger.info("pass cross_candle2_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
                    return copy.deepcopy(first_tic)

        self.logging.logger.info("corss_candle check> [%s] >> %s" % (code, first_tic))
        return {}

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

        # 20일선과 종가 간격 5%이내
        # 20일선 상승중
        # 20일선이 종가 아래에 위치
        # 3일동내에 음봉만 존재
        # 망치 찾기

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 5.0:
            self.logging.logger.info("ma20_percent check> [%s]  " % code)
            return {}

        ma20_list = [item["ma20"] for item in analysis_rows]
        inverselist = ma20_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend ma20 check> [%s]  " % code)
            return {}

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
                    self.logging.logger.info("pass cross_candle_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
                    return copy.deepcopy(first_tic)

        self.logging.logger.info("corss_candle check> [%s] >> %s" % (code, first_tic))
        return {}

    def get_conform_cable_tie3_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 5:
            return {}

        analysis_rows = rows[:5]

        self.logging.logger.info("cable_tie3_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]
        second_tic = analysis_rows[1]
        ma_field_list = ["ma3", "ma5", "ma10", "ma20"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        # 양봉
        # 어제종가 보다 오늘 종가가 높음
        # 종가가 20일선 위에 위치
        # 3일선, 5일선, 10일선, 20일선 상승중
        # 3일선, 5일선, 10일선, 20일선 간격이 10 이하

        if first_tic[self.customType.START_PRICE] > first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s]" % code)
            return {}

        if second_tic[self.customType.CURRENT_PRICE] > first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic current_price check1 > [%s]" % code)
            return {}

        if first_tic["ma20"] > first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic current_price check2 > [%s]" % code)
            return {}

        ma20_list = [item["ma20"] for item in analysis_rows]
        ma20_inverselist = ma20_list[::-1]
        ma10_list = [item["ma10"] for item in analysis_rows]
        ma10_inverselist = ma10_list[::-1]
        ma5_list = [item["ma5"] for item in analysis_rows]
        ma5_inverselist = ma5_list[::-1]
        ma3_list = [item["ma3"] for item in analysis_rows]
        ma3_inverselist = ma3_list[::-1]
        if not is_increase_trend(ma20_inverselist) and not is_increase_trend(ma10_inverselist) and not is_increase_trend(ma5_inverselist) and not is_increase_trend(ma3_inverselist):
            self.logging.logger.info("ma_list_increases trend check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}
        ma_list = [first_tic["ma3"], first_tic["ma5"], first_tic["ma10"], first_tic["ma20"]]
        min_ma = min(ma_list)
        max_ma = max(ma_list)

        if (max_ma - min_ma) > 10:
            self.logging.logger.info("cable_tie3 check> [%s]" % code)
            return {}

        return copy.deepcopy(first_tic)

    def get_conform_cable_tie2_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 7:
            return {}

        analysis_rows = rows[:7]

        first_tic = analysis_rows[0]

        ma_field_list = ["ma20", "ma5", "ma10", "ma60", "ma120"]

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '' or x["ma5"] == '' or x["ma10"] == '' or x["ma60"] == '' or x["ma120"] == '']
        if len(empty_gap_list) > 0:
            return {}

        # 5일선, 10일선, 20일선, 60일선, 120일선이 종가 아래에 위치
        # 양봉
        # 종가와 5일선, 10일선, 20일선, 60일선, 120일선간격 체크

        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s]" % code)
                return {}

        self.logging.logger.info("cable_tie2_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s]" % code)
            return {}

        ma5_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma5"]) / first_tic["ma5"] * 100
        ma10_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma10"]) / first_tic["ma10"] * 100
        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        ma60_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma60"]) / first_tic["ma60"] * 100
        ma120_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma120"]) / first_tic["ma120"] * 100
        if ma120_percent >= ma5_percent:
            self.logging.logger.info("ma120_percent check > [%s]" % code)
            return {}

        percent_list = [abs(ma5_percent), abs(ma10_percent), abs(ma20_percent), abs(ma60_percent)]
        min_percent = min(percent_list)
        max_percent = max(percent_list)

        if (max_percent - min_percent) <= 0.5:
            self.logging.logger.info("ma5_percent check> [%s]" % code)
            return {}

        self.logging.logger.info("pass cable_tie2_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
        return copy.deepcopy(first_tic)

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

        # 종가가 120일선 위에 위치
        # 5일선 10일선 20일선 60일선이 25간격안에 위치
        # 종가 상승중
        # 20일선 상승중
        # 5일선이 20일선 보다 위에 있거나 10일선이 60일선 위에 위치

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
        gap = 25
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
        last_price_inverselist = last_price_list[::-1]
        if not is_increase_trend(last_price_inverselist):
            self.logging.logger.info("is_increase_trend check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}
        ma20_list = [item["ma20"] for item in compare_rows]
        ma20_inverselist = ma20_list[::-1]
        if not is_increase_trend(ma20_inverselist):
            self.logging.logger.info("ma20_list_trend check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if first_tic["ma5"] <= first_tic["ma20"] or first_tic["ma10"] <= first_tic["ma60"]:
            self.logging.logger.info("first_tic short line position check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        self.logging.logger.info("pass cable_tie_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
        return copy.deepcopy(first_tic)

    def get_conform_ma_line3_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 5:
            return {}
        analysis_rows = rows[:5]
        compare_rows = analysis_rows[:3]

        first_tic = compare_rows[0]
        ma_field_list = ["ma20", "ma5", "ma10"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("ma_line3_case analysis_rows > [%s] >> %s " % (code, compare_rows))

        # 종가가 5일선, 10일선, 20일선 위에 위치
        # 20일선 상승중
        # 5일선 상승중
        # 5일선, 10일선, 20일선 정배열
        # 5일선, 10일선 20일선과 종가의 간격
        
        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s]" % code)
                return {}

        ma20_list = [item["ma20"] for item in analysis_rows]
        ma20_inverselist = ma20_list[::-1]
        if not is_increase_trend(ma20_inverselist):
            self.logging.logger.info("is_increase_trend ma20 check> [%s]  " % code)
            return {}

        ma5_list = [item["ma5"] for item in analysis_rows]
        ma5_inverselist = ma5_list[::-1]
        if not is_increase_trend(ma5_inverselist):
            self.logging.logger.info("is_increase_trend ma5 check> [%s]  " % code)
            return {}

        if first_tic["ma5"] >= first_tic["ma10"] >= first_tic["ma20"]:
            pass
        else:
            self.logging.logger.info("is regular arrangement check> [%s]" % code)
            return {}

        ma5_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma5"]) / first_tic["ma5"] * 100
        if ma5_percent > 0.3:
            self.logging.logger.info("ma5_percent check> [%s]" % code)
            return {}
        ma10_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma10"]) / first_tic["ma10"] * 100
        if ma10_percent > 0.7:
            self.logging.logger.info("ma10_percent check> [%s]" % code)
            return {}
        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 1.0:
            self.logging.logger.info("ma20_percent check> [%s]" % code)
            return {}

        self.logging.logger.info("pass ma_line3_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
        return self.get_conform_bollingerband_point_case(code)

    def get_conform_ma_line2_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 5:
            return {}

        analysis_rows = rows[:5]
        compare_rows = analysis_rows[:2]

        first_tic = compare_rows[0]
        second_tic = compare_rows[1]
        ma_field_list = ["ma20", "ma5", "ma10"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("ma_line2_case analysis_rows > [%s] >> %s " % (code, compare_rows))

        # 20일선과 간격 5% 이내
        # 20일선 상승중
        # 5일선, 10일선 20일선 정배열
        # 종가 상승중
        # 종가가 5일선, 10일선, 20일선 위에 위치
        # 어제 또는 오늘 20일선이 저가와 고가 사이에 위치

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 5.0:
            self.logging.logger.info("ma20_percent check> [%s]  " % code)
            return {}

        ma20_list = [item["ma20"] for item in analysis_rows]
        inverselist = ma20_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend ma20 check> [%s]  " % code)
            return {}

        if first_tic["ma5"] >= first_tic["ma10"] >= first_tic["ma20"]:
            pass
        else:
            self.logging.logger.info("is regular arrangement check> [%s]" % code)
            return {}

        last_price_list = [item[self.customType.CURRENT_PRICE] for item in compare_rows]
        inverselist = last_price_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend check> [%s]  " % code)
            return {}

        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s]" % code)
                return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s]" % code)
            return {}

        if first_tic[self.customType.LOWEST_PRICE] < first_tic["ma20"] < first_tic[self.customType.HIGHEST_PRICE] or second_tic[self.customType.LOWEST_PRICE] < second_tic["ma20"] < second_tic[
            self.customType.HIGHEST_PRICE]:
            pass
        else:
            self.logging.logger.info("second_tic or third_tic position check > [%s] " % code)
            return {}

        self.logging.logger.info("pass ma_line2_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
        return self.get_conform_bollingerband_point_case(code)

    def get_conform_ma_line_case(self, code):

        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 5:
            return {}

        analysis_rows = rows[:5]
        compare_rows = rows[:2]

        first_tic = compare_rows[0]

        ma_field_list = ["ma20", "ma5", "ma10"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("ma_line_case analysis_rows > [%s] >> %s " % (code, analysis_rows))
        # 20일선과 거리가 5프로 이내
        # 20일선이 상증중
        # 5일선이 상승중
        # 양봉
        # 종가 상승중

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 5.0:
            self.logging.logger.info("ma20_percent check> [%s]  " % code)
            return {}

        ma20_list = [item["ma20"] for item in analysis_rows]
        inverselist = ma20_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend ma20 check> [%s]  " % code)
            return {}

        ma5_list = [item["ma5"] for item in analysis_rows]
        ma5_inverselist = ma5_list[::-1]
        if not is_increase_trend(ma5_inverselist):
            self.logging.logger.info("is_increase_trend ma5 check> [%s]  " % code)
            return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic black candle check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        if first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
            self.logging.logger.info("first_tic position check > [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        last_price_list = [item[self.customType.CURRENT_PRICE] for item in analysis_rows]
        inverselist = last_price_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend current check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}

        self.logging.logger.info("pass ma_line_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
        return self.get_conform_bollingerband_point_case(code)

    def get_conform_bollingerband_point_case(self, code):

        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        self.logging.logger.info("bollingerband_point_case analysis_rows > [%s] >> %s " % (code, analysis_rows))
        first_tic = analysis_rows[0]

        if first_tic["pb"] > 0.70 and first_tic["mfi10"] > 70 and first_tic["ma20"] <= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("pass bollingerband_point_case analysis_rows > [%s] [%s]" % (code, first_tic[self.customType.CURRENT_PRICE]))
            return copy.deepcopy(first_tic)

        return {}

    def get_etf_stock_info(self):
        copy_dict = copy.deepcopy(self.target_etf_stock_dict)
        for sCode in copy_dict.keys():
            QTest.qWait(5000)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
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
            create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma3", 3)

            create_bollingerband_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE)
            create_mfi(code, self.analysis_etf_target_dict, "row")

    def get_individual_etf_daily_candle_info(self, code):
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10080_info_event_loop.exec_()


def create_mfi(code, target_dict, orgin_field):
    customType = CustomType()

    gap = 10 + 1
    rows = target_dict[code][orgin_field]
    new_rows = sorted(rows, key=itemgetter("일자"), reverse=False)
    for i in range(len(new_rows)):

        max_ma_gap_len = i + gap
        if len(new_rows) < max_ma_gap_len:
            max_ma_gap_len = len(new_rows)
        ma_gap_list = copy.deepcopy(new_rows[i: max_ma_gap_len])
        if len(ma_gap_list) < gap:
            break

        for sub in ma_gap_list:
            sub["tp"] = (sub[customType.HIGHEST_PRICE] + sub[customType.LOWEST_PRICE] + sub[customType.CURRENT_PRICE]) / 3
            sub["pmf"] = 0
            sub["nmf"] = 0

        for s in range(len(ma_gap_list) - 1):
            ss = ma_gap_list[s]
            next_sub = ma_gap_list[s + 1]
            if ss["tp"] < next_sub["tp"]:
                next_sub["pmf"] = next_sub["tp"] * next_sub[customType.VOLUME]
                next_sub["nmf"] = 0
            else:
                next_sub["nmf"] = next_sub["tp"] * next_sub[customType.VOLUME]
                next_sub["pmf"] = 0

        row = new_rows[i+gap-1]
        sum_pmf = sum(item["pmf"] for item in ma_gap_list)
        sum_nmf = sum(item["nmf"] for item in ma_gap_list)
        if sum_nmf > 0:
            mfr = sum_pmf / sum_nmf
            row["mfi10"] = 100 - (100 / (1 + mfr))
        else:
            row["mfi10"] = 100.0

    target_dict[code][orgin_field] = sorted(new_rows, key=itemgetter("일자"), reverse=True)


def create_bollingerband_line(code, target_dict, origin_field, source_field):
    customType = CustomType()
    gap = 20
    rows = target_dict[code][origin_field]
    for i in range(len(rows)):
        max_ma_gap_len = i + gap
        if len(rows) < max_ma_gap_len:
            max_ma_gap_len = len(rows)
        ma_gap_list = copy.deepcopy(rows[i: max_ma_gap_len])
        if len(ma_gap_list) < gap:
            break

        for sub in ma_gap_list:
            sub["tp"] = (sub[customType.HIGHEST_PRICE] + sub[customType.LOWEST_PRICE] + sub[customType.CURRENT_PRICE]) / 3

        stddev = numpy.std([item["tp"] for item in ma_gap_list])

        row = rows[i]

        row["upper"] = numpy.mean([item["tp"] for item in ma_gap_list]) + (stddev * 2)
        row["lower"] = numpy.mean([item["tp"] for item in ma_gap_list]) - (stddev * 2)
        row["pb"] = (row[source_field] - row["lower"]) / (row["upper"] - row["lower"])