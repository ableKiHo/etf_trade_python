import sys
import shutil

from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

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

        self.represent_keyword_dict = {self.customType.KOSPI: {}, self.customType.KOSDAQ: {}, '반도체': {}, 'KRX300': {}, '200TR': {}, '200': {}}
        self.recommand_keyword_list = ['TR', '고배당', 'TOP10', '저변동', '성장', '블루칩', '우선주', '배당성장']

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
            stock_type = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_TYPE)
            stock_type = stock_type.strip()
            last_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LAST_PRICE)
            last_price = last_price.strip()
            trace_sector_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TRACE_SECTOR_CODE)
            trace_sector_code = trace_sector_code.strip()
            trace_sector_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TRACE_SECTOR_NAME)
            trace_sector_name = trace_sector_name.strip()

            self.logging.logger.info(self.logType.OPT40004_STATUS_LOG % (code, code_nm, stock_type, trace_sector_code, trace_sector_name, volume))
            if abs(int(volume)) >= 10000 and abs(int(last_price)) <= 50000:
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
        if int(market_cap) >= 60:
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
        return bool(buy_point)

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

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 1.99:
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

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 1.99:
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
        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s]" % code)
                return {}

        self.logging.logger.info("cable_tie_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        compare_rows = analysis_rows[:3]
        ma5_list = [item["ma5"] for item in compare_rows]
        ma5_inverselist = ma5_list[::-1]
        if not is_increase_trend(ma5_inverselist):
            self.logging.logger.info("ma5_list_trend check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}
        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s]" % code)
            return {}

        ma5_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma5"]) / first_tic["ma5"] * 100
        ma10_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma10"]) / first_tic["ma10"] * 100
        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        ma60_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma60"]) / first_tic["ma60"] * 100
        ma120_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma120"]) / first_tic["ma120"] * 100
        percent_list = [ma5_percent, ma10_percent, ma20_percent, ma60_percent, ma120_percent]
        if max(percent_list) > 0.99:
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
        last_price_inverselist = last_price_list[::-1]
        if not is_increase_trend(last_price_inverselist):
            self.logging.logger.info("is_increase_trend check> [%s] >> %s  " % (code, first_tic["일자"]))
            return {}
        ma5_list = [item["ma5"] for item in compare_rows]
        ma5_inverselist = ma5_list[::-1]
        if not is_increase_trend(ma5_inverselist):
            self.logging.logger.info("ma5_list_trend check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}
        ma10_list = [item["ma10"] for item in compare_rows]
        ma10_inverselist = ma10_list[::-1]
        if not is_increase_trend(ma10_inverselist):
            self.logging.logger.info("ma10_list_trend check> [%s] >> %s " % (code, first_tic["일자"]))
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
        return copy.deepcopy(first_tic)

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

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 1.99:
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
        return copy.deepcopy(first_tic)

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

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 1.99:
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
        return copy.deepcopy(first_tic)

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

    def get_individual_etf_daily_candle_info(self, code):
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10080_info_event_loop.exec_()
