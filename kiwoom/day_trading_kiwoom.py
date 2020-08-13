import sys

from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


def default_q_timer_setting(second=3.8):
    timer2 = QTimer()
    timer2.start(1000 * second)
    return timer2


class DayTradingKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF DayTradingKiwoom() class start.")
        self.line.notification("ETF DayTradingKiwoom() class start.")

        self.etf_info_event_loop = QEventLoop()
        self.tr_opt10081_info_event_loop = QEventLoop()
        self.tr_sell_opt10081_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_mystock_info_event_loop = QEventLoop()

        self.today = get_today_by_format('%Y%m%d')

        self.screen_start_stop_real = "1000"
        self.buy_screen_meme_stock = "3000"
        self.sell_screen_meme_stock = "3100"
        self.buy_screen_real_stock = "6000"
        self.screen_etf_stock = "4020"

        self.max_hold_stock_count = 6
        self.max_buy_amount_by_stock = 50000

        self.hold_stock_check_timer = QTimer()
        self.analysis_search_timer = QTimer()

        self.current_hold_stock_count = 0
        self.status = "WAIT"

        self.today_buy_etf_stock_dict = {}
        self.target_etf_stock_dict = {}
        self.current_hold_etf_stock_dict = {}
        self.miraeasset_hold_etf_stock_dict = {}
        self.analysis_goal_etf_stock_dict = {}
        self.analysis_goal_etf_stock_list = []
        self.analysis_sell_etf_stock_list = []
        self.goal_buy_search_stock_code = ''
        self.sell_search_stock_code = ''
        self.search_stock_code = []

        self.trace_stock_dict = {}
        self.set_trace_stock_info()

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF DAY TRADE START")

        self.detail_account_info()
        QTest.qWait(5000)

        self.detail_account_mystock()
        self.set_miraeasset_stock_info()
        self.current_hold_stock_count = len(self.current_hold_etf_stock_dict.keys())

        if self.current_hold_stock_count < self.max_hold_stock_count:
            self.get_search_goal_price_etf()
            self.loop_analysis_buy_etf()

        if self.current_hold_stock_count > 0 or len(self.miraeasset_hold_etf_stock_dict.keys()) > 0:
            self.loop_check_sell_hold_etf()

        self.trace_stock_real_reg()

    def set_trace_stock_info(self):
        self.trace_stock_dict.update({'008370': {"name": "원풍", "sell_std_price": 4250, "buy_std_price": 4100, "noti_count": 0, "noti_type": "buy"}})
        self.trace_stock_dict.update({'100220': {"name": "비상교육", "sell_std_price": 7150, "buy_std_price": 6980, "noti_count": 0, "noti_type": "buy"}})

    def trace_stock_real_reg(self):
        for code in self.trace_stock_dict.keys():
            self.logging.logger.info("trace_stock_real_reg >> %s" % code)
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.buy_screen_real_stock, code, fids, "1")

    def set_miraeasset_stock_info(self):
        self.miraeasset_hold_etf_stock_dict.update({'161510': {self.customType.STOCK_CODE: '161510',
                                                               self.customType.STOCK_NAME: 'ARIRANG 고배당주',
                                                               self.customType.HOLDING_QUANTITY: 10,
                                                               self.customType.PURCHASE_PRICE: 9475,
                                                               "row": []}})

    def loop_check_sell_hold_etf(self):
        self.hold_stock_check_timer.stop()
        self.hold_stock_check_timer = default_q_timer_setting()
        self.hold_stock_check_timer.timeout.connect(self.check_sell_hold_etf)

    def check_sell_hold_etf(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        self.hold_stock_check_timer.stop()
        if (self.today + '150000') < currentDate:
            return
        self.loop_last_price_sell_all_etf_stock()

    def loop_last_price_sell_all_etf_stock(self):
        self.logging.logger.info('loop_last_price_sell_all_etf_stock')
        self.sell_search_stock_code = ''
        self.analysis_sell_etf_stock_list = []
        for key in self.current_hold_etf_stock_dict.keys():
            if key not in self.today_buy_etf_stock_dict.keys():
                self.analysis_sell_etf_stock_list.append(copy.deepcopy(self.current_hold_etf_stock_dict[key]))
        for key in self.miraeasset_hold_etf_stock_dict.keys():
            self.analysis_sell_etf_stock_list.append(copy.deepcopy(self.miraeasset_hold_etf_stock_dict[key]))
        self.hold_stock_check_timer = default_q_timer_setting(120)
        self.hold_stock_check_timer.timeout.connect(self.last_candle_hammer_sell_check)

    def last_candle_hammer_sell_check(self):
        if len(self.analysis_sell_etf_stock_list) == 0:
            self.logging.logger.info("analysis_sell_etf_stock_list nothing")
            self.hold_stock_check_timer.stop()
            return

        self.get_sell_next_search_etf_stock_code(len(self.analysis_sell_etf_stock_list))

        code = self.sell_search_stock_code
        self.logging.logger.info("analysis_sell_etf_stock_list loop > %s " % code)

        if code in self.miraeasset_hold_etf_stock_dict.keys():
            self.get_opt10081_info_mirae(code)
            create_moving_average_gap_line(code, self.miraeasset_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
            max_profit_sell_point = self.get_max_profit_sell_case(code, self.miraeasset_hold_etf_stock_dict)
        else:
            self.get_sell_opt10081_info(code)
            create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
            max_profit_sell_point = self.get_max_profit_sell_case(code, self.current_hold_etf_stock_dict)

        if bool(max_profit_sell_point):
            if code in self.miraeasset_hold_etf_stock_dict.keys():
                self.line.notification("miraeasset etf sell point - max profit", "[TRACE]")
            else:
                self.hold_stock_check_timer.stop()
                quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
                self.logging.logger.info("max_profit_sell_point break >> %s" % code)
                self.current_hold_etf_stock_dict[code].update({"sell": "full"})
                self.sell_send_order(code, self.sell_screen_meme_stock, quantity)

        if code in self.miraeasset_hold_etf_stock_dict.keys():
            full_sell_point = self.get_sell_case(code, "ma10", self.miraeasset_hold_etf_stock_dict)
        else:
            full_sell_point = self.get_sell_case(code, "ma10", self.current_hold_etf_stock_dict)
        if bool(full_sell_point):
            if code in self.miraeasset_hold_etf_stock_dict.keys():
                self.line.notification("miraeasset etf sell point - ma10", "[TRACE]")
            else:
                self.hold_stock_check_timer.stop()
                quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
                self.logging.logger.info("full_sell_point break >> %s" % code)
                self.current_hold_etf_stock_dict[code].update({"sell": "full"})
                self.sell_send_order(code, self.sell_screen_meme_stock, quantity)

        self.logging.logger.info('last_candle_hammer_sell_check end')

    def loop_analysis_buy_etf(self):
        self.analysis_search_timer = default_q_timer_setting(60)
        self.analysis_search_timer.timeout.connect(self.analysis_day_candle_info)

    def analysis_day_candle_info(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')

        # self.logging.logger.info('analysis_day_candle_info >> %s' % len(self.analysis_goal_etf_stock_dict.keys()))
        if (self.today + '150000') <= currentDate and len(self.analysis_goal_etf_stock_dict.keys()) > 0:
            self.analysis_search_timer.stop()
            if self.current_hold_stock_count < self.max_hold_stock_count:
                self.loop_last_price_buy_goal_etf_stock()
            else:
                self.call_exit()
                return

        if (self.today + '160000') < currentDate:
            self.call_exit()
            return

    def loop_other_target_buy_etf_stock(self):
        self.logging.logger.info('loop_other_target_buy_etf_stock')
        self.goal_buy_search_stock_code = ''
        self.analysis_goal_etf_stock_list = []
        self.search_stock_code = []
        for key in self.target_etf_stock_dict.keys():
            if key not in self.analysis_goal_etf_stock_dict:
                self.analysis_goal_etf_stock_list.append(copy.deepcopy(self.target_etf_stock_dict[key]))
        self.analysis_search_timer = default_q_timer_setting(30)
        self.analysis_search_timer.timeout.connect(self.last_target_candle_hammer_check)

    def last_target_candle_hammer_check(self):
        self.logging.logger.info('other_target_candle_hammer_check')
        if self.current_hold_stock_count == self.max_hold_stock_count:
            self.logging.logger.info("max_hold_stock_count over")
            self.analysis_search_timer.stop()
            self.loop_check_sell_hold_etf()
        if len(self.analysis_goal_etf_stock_list) == 0:
            self.logging.logger.info("market off time day trade target nothing")
            self.analysis_search_timer.stop()
            self.loop_check_sell_hold_etf()
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '160000') < currentDate:
            self.logging.logger.info("market off time day trade over")
            self.analysis_search_timer.stop()
            self.call_exit()

        self.get_next_search_etf_stock_code(len(self.analysis_goal_etf_stock_list))

        code = self.goal_buy_search_stock_code
        self.logging.logger.info("analysis_goal_etf_stock_list loop > %s " % code)
        self.search_stock_code.append(code)

        self.get_opt10081_info_all(code)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        rows = self.target_etf_stock_dict[code]["row"]
        last_price_buy_point = self.get_conform_hammer_case(code, rows)

        if bool(last_price_buy_point):
            quantity = math.trunc(self.max_buy_amount_by_stock / last_price_buy_point[self.customType.CURRENT_PRICE])
            if quantity >= 1:
                self.logging.logger.info("last_price_buy_point break >> %s" % code)
                self.current_hold_stock_count = self.current_hold_stock_count + 1
                self.market_price_send_order(code, quantity)

        if len(self.search_stock_code) == len(self.analysis_goal_etf_stock_list):
            self.logging.logger.info("market price trade all search end")
            self.analysis_search_timer.stop()
            self.call_exit()

        self.logging.logger.info('other_target_candle_hammer_check end')

    def loop_last_price_buy_goal_etf_stock(self):
        self.logging.logger.info('loop_last_price_buy_goal_etf_stock')
        self.goal_buy_search_stock_code = ''
        self.analysis_goal_etf_stock_list = []
        self.search_stock_code = []
        for key in self.analysis_goal_etf_stock_dict.keys():
            self.analysis_goal_etf_stock_list.append(copy.deepcopy(self.analysis_goal_etf_stock_dict[key]))
        self.analysis_search_timer = default_q_timer_setting(30)
        self.analysis_search_timer.timeout.connect(self.last_candle_hammer_check)

    def last_candle_hammer_check(self):
        self.logging.logger.info('goal_etf_last_candle_hammer_check')
        if self.current_hold_stock_count == self.max_hold_stock_count:
            self.logging.logger.info("max_hold_stock_count over")
            self.analysis_search_timer.stop()
            self.loop_check_sell_hold_etf()
        if len(self.analysis_goal_etf_stock_list) == 0:
            self.logging.logger.info("market off time day trade target nothing")
            self.analysis_search_timer.stop()
            self.loop_check_sell_hold_etf()
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '160000') < currentDate:
            self.logging.logger.info("market off time day trade over")
            self.analysis_search_timer.stop()
            self.call_exit()

        self.get_next_search_etf_stock_code(len(self.analysis_goal_etf_stock_list))

        code = self.goal_buy_search_stock_code
        self.logging.logger.info("analysis_goal_etf_stock_list loop > %s " % code)
        self.search_stock_code.append(code)

        self.get_opt10081_info(code)
        create_moving_average_gap_line(code, self.analysis_goal_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.analysis_goal_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        rows = self.analysis_goal_etf_stock_dict[code]["row"]
        last_price_buy_point = self.get_conform_hammer_case(code, rows)

        if bool(last_price_buy_point):
            quantity = math.trunc(self.max_buy_amount_by_stock / last_price_buy_point[self.customType.CURRENT_PRICE])
            if quantity >= 1:
                self.logging.logger.info("goal_etf_last_price_buy_point break >> %s" % code)
                self.current_hold_stock_count = self.current_hold_stock_count + 1
                self.market_price_send_order(code, quantity)

        if len(self.search_stock_code) == len(self.analysis_goal_etf_stock_list):
            self.logging.logger.info("goal_etf market price trade search end")
            self.analysis_search_timer.stop()
            if self.current_hold_stock_count < self.max_hold_stock_count:
                self.loop_other_target_buy_etf_stock()
            else:
                self.call_exit()

        self.logging.logger.info('goal_etf_last_candle_hammer_check end')

    def get_search_goal_price_etf(self):
        self.read_target_etf_file()
        QTest.qWait(5000)

        self.get_all_etf_info()
        QTest.qWait(5000)
        self.get_goal_price_etf()
        self.create_analysis_target_etf_file()
        QTest.qWait(5000)
        self.screen_number_setting(self.target_etf_stock_dict)

        currentDate = get_today_by_format('%Y%m%d%H%M%S')

        if (self.today + '150000') > currentDate:
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                             self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

            self.stock_real_reg()

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)
                self.status = "END"

        elif sRealType == self.customType.STOCK_CONCLUSION:
            if sCode in self.trace_stock_dict.keys():
                current_stock_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
                current_stock_price = abs(int(current_stock_price.strip()))

                if current_stock_price >= self.trace_stock_dict[sCode]["sell_std_price"] and self.trace_stock_dict[sCode]["noti_type"] == "sell" and self.trace_stock_dict[sCode]["noti_count"] < 3:
                    self.line.notification("sell time [%s] >> %s / %s" % (self.trace_stock_dict[sCode]["name"], current_stock_price, self.trace_stock_dict[sCode]["sell_std_price"]), "[TRACE]")
                    self.trace_stock_dict[sCode]["noti_count"] = self.trace_stock_dict[sCode]["noti_count"] + 1

                if current_stock_price < self.trace_stock_dict[sCode]["buy_std_price"] and self.trace_stock_dict[sCode]["noti_type"] == "buy" and self.trace_stock_dict[sCode]["noti_count"] < 3:
                    self.line.notification("[TRACE] buy time [%s] >> %s / %s" % (self.trace_stock_dict[sCode]["name"], current_stock_price, self.trace_stock_dict[sCode]["buy_std_price"]), "[TRACE]")
                    self.trace_stock_dict[sCode]["noti_count"] = self.trace_stock_dict[sCode]["noti_count"] + 1

            if self.status == "SEARCH":
                currentDate = get_today_by_format('%Y%m%d%H%M%S')
                if sCode in self.target_etf_stock_dict.keys() and (self.today + '150000') > currentDate:
                    current_stock_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
                    current_stock_price = abs(int(current_stock_price.strip()))
                    # self.logging.logger.info('STOCK_CONCLUSION [%s]>> %s / %s' % (sCode, current_stock_price, self.target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]))
                    if sCode in self.target_etf_stock_dict.keys():
                        if sCode not in self.analysis_goal_etf_stock_dict.keys() and current_stock_price >= self.target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]:
                            self.logging.logger.info("pass goal price [%s] >> %s" % (sCode, self.target_etf_stock_dict[sCode]))
                            self.dynamicCall("SetRealRemove(QString, QString)", self.target_etf_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
                            self.analysis_goal_etf_stock_dict.update(
                                {sCode: {self.customType.STOCK_CODE: sCode, self.customType.GOAL_PRICE: self.target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]}})

                if (self.today + '150000') <= currentDate:
                    self.logging.logger.info("max time over stock conclusion realdata callback")
                    self.hold_stock_check_timer.stop()
                    if len(self.target_etf_stock_dict.keys()) > 0:
                        self.all_real_remove()

    def get_opt10081_info(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exec_()

    def get_opt10081_info_all(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081_all", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exec_()

    def get_sell_opt10081_info(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_sell_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_sell_opt10081_info_event_loop.exec_()

    def get_opt10081_info_mirae(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_sell_opt10081_mirae", "opt10081", 0, self.screen_etf_stock)
        self.tr_sell_opt10081_info_event_loop.exec_()

    def get_next_search_etf_stock_code(self, max_index=4):
        if self.goal_buy_search_stock_code == '':
            item = self.analysis_goal_etf_stock_list[0]
        else:
            index = next((index for (index, d) in enumerate(self.analysis_goal_etf_stock_list) if d[self.customType.STOCK_CODE] == self.goal_buy_search_stock_code), None)
            if index < 0 or index > max_index:
                self.logging.logger.info("not found next stock code > index:[%s] " % index)
                sys.exit()

            if index == len(self.analysis_goal_etf_stock_list) - 1:
                index = -1
            item = self.analysis_goal_etf_stock_list[index + 1]

        self.goal_buy_search_stock_code = item[self.customType.STOCK_CODE]

    def get_sell_next_search_etf_stock_code(self, max_index=4):
        if self.sell_search_stock_code == '':
            item = self.analysis_sell_etf_stock_list[0]
        else:
            index = next((index for (index, d) in enumerate(self.analysis_sell_etf_stock_list) if d[self.customType.STOCK_CODE] == self.sell_search_stock_code), None)
            if index < 0 or index > max_index:
                self.logging.logger.info("not found next stock code > index:[%s] " % index)
                sys.exit()

            if index == len(self.analysis_sell_etf_stock_list) - 1:
                index = -1
            item = self.analysis_sell_etf_stock_list[index + 1]

        self.sell_search_stock_code = item[self.customType.STOCK_CODE]

    def get_max_profit_sell_case(self, code, dict):
        self.logging.logger.info('get_max_profit_sell_case')

        rows = dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        first_tic = analysis_rows[0]
        current_price = first_tic[self.customType.CURRENT_PRICE]
        buy_price = dict[code][self.customType.PURCHASE_PRICE]

        if current_price > buy_price:
            profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
            if profit_rate >= 10:
                self.logging.logger.info("max_profit check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, profit_rate))
                return copy.deepcopy(first_tic)
        return {}

    def get_sell_case(self, code, field, dict):
        self.logging.logger.info('get_sell_case %s' % field)
        rows = dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        first_tic = analysis_rows[0]
        second_tic = analysis_rows[1]

        empty_gap_list = [x for x in analysis_rows if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("hammer_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        if second_tic[field] >= second_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("second_tic ma10 check > [%s] >> %s " % (code, second_tic))
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic ma10 check > [%s] >> %s " % (code, first_tic))
                return copy.deepcopy(first_tic)

        return {}

    def get_conform_hammer_case(self, code, rows):

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]

        first_tic = analysis_rows[0]
        ma_field_list = ["ma20", "ma5"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("hammer_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        last_price_list = [item[self.customType.CURRENT_PRICE] for item in analysis_rows]
        inverselist = last_price_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend check> [%s] >> %s / %s  " % (code, first_tic["일자"], inverselist))
            return {}

        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic))
                return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s] >> %s " % (code, first_tic))
            return {}

        first_tic_body = first_tic[self.customType.CURRENT_PRICE] - first_tic[self.customType.START_PRICE]
        first_tic_head_tail = first_tic[self.customType.HIGHEST_PRICE] - first_tic[self.customType.CURRENT_PRICE]
        if first_tic_body * 0.05 < first_tic_head_tail:
            self.logging.logger.info("first_tic hammer candle check > [%s] >> %s " % (code, first_tic))
            return {}

        return copy.deepcopy(first_tic)

    def all_real_remove(self):
        self.logging.logger.info('all_real_remove')
        for code in self.target_etf_stock_dict.keys():
            self.dynamicCall("SetRealRemove(QString, QString)", self.target_etf_stock_dict[code][self.customType.SCREEN_NUMBER], code)

    def get_all_etf_info(self):
        self.logging.logger.info('get_all_etf_info_opt10001')
        code_list = list(set(list(self.target_etf_stock_dict.keys())))
        for code in code_list:
            QTest.qWait(3800)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.new_chejan_slot)

    def detail_account_info(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_info")
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_mystock")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00018, "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_mystock_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081":
            self.trdata_slot_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_sell_opt10081":
            self.trdata_slot_sell_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081_all":
            self.trdata_slot_opt10081_all(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_sell_opt10081_mirae":
            self.trdata_slot_sell_mirae_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPW00018:
            self.trdata_slot_opw00018(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opw00018(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)  # 최대 20개 카운트
        for i in range(rows):
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_NUMBER)
            code = code.strip()[1:]

            code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_NAME)
            code_nm = code_nm.strip()
            stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HOLDING_QUANTITY)
            buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.PURCHASE_PRICE)
            learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.YIELD)
            current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.CURRENT_PRICE)
            total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.PURCHASE_AMOUNT)
            possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.AMOUNT_OF_TRADING_AVAILABLE)

            self.logging.logger.info(self.logType.OPW00018_DETAIL_LOG % (code, code_nm, stock_quantity, buy_price, learn_rate, current_price))

            if code in self.current_hold_etf_stock_dict:
                pass
            else:
                self.current_hold_etf_stock_dict[code] = {}

            stock_quantity = int(stock_quantity.strip())
            buy_price = int(buy_price.strip())
            learn_rate = float(learn_rate.strip())
            current_price = int(current_price.strip())
            total_chegual_price = int(total_chegual_price.strip())
            possible_quantity = int(possible_quantity.strip())

            self.current_hold_etf_stock_dict[code].update({self.customType.STOCK_CODE: code})
            self.current_hold_etf_stock_dict[code].update({self.customType.STOCK_NAME: code_nm})
            self.current_hold_etf_stock_dict[code].update({self.customType.HOLDING_QUANTITY: stock_quantity})
            self.current_hold_etf_stock_dict[code].update({self.customType.PURCHASE_PRICE: buy_price})
            self.current_hold_etf_stock_dict[code].update({self.customType.YIELD: learn_rate})
            self.current_hold_etf_stock_dict[code].update({self.customType.CURRENT_PRICE: current_price})
            self.current_hold_etf_stock_dict[code].update({self.customType.PURCHASE_AMOUNT: total_chegual_price})
            self.current_hold_etf_stock_dict[code].update({self.customType.AMOUNT_OF_TRADING_AVAILABLE: possible_quantity})
            self.current_hold_etf_stock_dict[code].update({"row": []})

            self.line.notification(self.logType.OWN_STOCK_LOG % self.current_hold_etf_stock_dict[code])

        if sPrevNext == "2":
            self.detail_account_mystock(sPrevNext="2")
        else:
            self.stop_screen_cancel(self.screen_my_info)
            self.detail_account_mystock_info_event_loop.exit()

    def trdata_slot_opw00001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.DEPOSIT)
        self.deposit = int(deposit)
        buy_possible_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.AVAILABLE_AMOUNT)
        self.buy_possible_deposit = int(buy_possible_deposit)
        self.buy_possible_deposit = math.trunc(self.buy_possible_deposit / 2)

        self.logging.logger.info(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        self.line.notification(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)

        self.stop_screen_cancel(self.screen_my_info)
        self.detail_account_info_event_loop.exit()

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.START_PRICE)
        current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        highest_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.HIGHEST_PRICE)
        if code in self.target_etf_stock_dict.keys():
            self.target_etf_stock_dict[code].update({self.customType.STOCK_CODE: code})
            self.target_etf_stock_dict[code].update({self.customType.START_PRICE: abs(int(start_price.strip()))})
            self.target_etf_stock_dict[code].update({self.customType.CURRENT_PRICE: abs(int(current_price.strip()))})
            self.target_etf_stock_dict[code].update({self.customType.HIGHEST_PRICE: abs(int(highest_price.strip()))})

        self.etf_info_event_loop.exit()

    def trdata_slot_sell_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        if stock_code not in self.current_hold_etf_stock_dict.keys():
            self.current_hold_etf_stock_dict.update({stock_code: {"row": []}})

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.current_hold_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_sell_opt10081_info_event_loop.exit()

    def trdata_slot_sell_mirae_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        if stock_code not in self.miraeasset_hold_etf_stock_dict.keys():
            self.miraeasset_hold_etf_stock_dict.update({stock_code: {"row": []}})

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.miraeasset_hold_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_sell_opt10081_info_event_loop.exit()

    def trdata_slot_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        if stock_code not in self.analysis_goal_etf_stock_dict.keys():
            self.analysis_goal_etf_stock_dict.update({stock_code: {"row": []}})

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.analysis_goal_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exit()

    def trdata_slot_opt10081_all(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        if stock_code not in self.target_etf_stock_dict.keys():
            self.target_etf_stock_dict.update({stock_code: {"row": []}})

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.target_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exit()

    def read_target_etf_file(self):
        self.logging.logger.info("read_target_etf_file")
        if os.path.exists(self.target_etf_file_path):
            f = open(self.target_etf_file_path, "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")

                    stock_code = ls[0]
                    stock_name = ls[1]
                    highest_stock_price = ls[2]
                    lowest_stock_price = ls[3]
                    last_stock_price = ls[4].rstrip('\n')
                    if stock_code not in self.current_hold_etf_stock_dict.keys():
                        self.target_etf_stock_dict.update({stock_code: {self.customType.STOCK_CODE: stock_code,
                                                                        self.customType.STOCK_NAME: stock_name,
                                                                        self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                        self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                        self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                        self.customType.GOAL_PRICE: '',
                                                                        "stat": '',
                                                                        "row": []}})
            f.close()

    def get_goal_price_etf(self):
        self.logging.logger.info("get_goal_price_etf")
        for code in self.target_etf_stock_dict.keys():
            value = self.target_etf_stock_dict[code]
            goal_stock_price = cal_goal_stock_price(value[self.customType.START_PRICE], value[self.customType.LAST_DAY_LAST_PRICE], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                                                    value[self.customType.LAST_DAY_LOWEST_PRICE])
            if goal_stock_price > 0:
                self.target_etf_stock_dict[code].update({self.customType.GOAL_PRICE: goal_stock_price})
                self.logging.logger.info("pass goal_price_priority_etf[%s] >> %s" % (code, self.target_etf_stock_dict[code]))
                if goal_stock_price <= value[self.customType.HIGHEST_PRICE]:
                    self.logging.logger.info("pass highest price [%s] >> %s" % (code, self.target_etf_stock_dict[code]))
                    self.analysis_goal_etf_stock_dict.update({code: {self.customType.STOCK_CODE: code, self.customType.GOAL_PRICE: goal_stock_price}})

            else:
                self.target_etf_stock_dict[code].update({"stat": "del"})

        for key in [key for key in self.target_etf_stock_dict if self.target_etf_stock_dict[key]["stat"] == "del"]: del self.target_etf_stock_dict[key]

    def screen_number_setting(self, cal_dict):
        self.logging.logger.info("screen_number_setting")

        cnt = 0
        temp_screen = int(self.buy_screen_real_stock)
        meme_screen = int(self.buy_screen_meme_stock)

        for code in cal_dict.keys():

            if (cnt % 20) == 0:
                temp_screen = int(temp_screen) + 1
                temp_screen = str(temp_screen)

            if (cnt % 20) == 0:
                meme_screen = int(meme_screen) + 1
                meme_screen = str(meme_screen)

            cal_dict[code].update({self.customType.SCREEN_NUMBER: str(temp_screen)})
            cal_dict[code].update({self.customType.MEME_SCREEN_NUMBER: str(meme_screen)})

            cnt += 1

    def stock_real_reg(self):
        self.logging.logger.info("stock_real_reg")
        for code in self.target_etf_stock_dict.keys():
            if self.target_etf_stock_dict[code][self.customType.GOAL_PRICE] > 0 and code not in self.analysis_goal_etf_stock_dict.keys():
                screen_num = self.target_etf_stock_dict[code][self.customType.SCREEN_NUMBER]
                fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
                self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

        self.status = "SEARCH"

    def market_price_send_order(self, code, quantity):
        self.logging.logger.info("[%s]add_send_order > %s " % (code, quantity))
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.send_order_market_price_stock_price(code, quantity)

    def send_order_market_price_stock_price(self, code, quantity):
        self.logging.logger.info("send_order_market_price_stock_price > %s / %s" % (code, quantity))
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, self.buy_screen_real_stock, self.account_num, 1, code, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_PRICE], ""])

        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_BUY_SUCCESS_LOG)
            self.line.notification(self.logType.ORDER_BUY_SUCCESS_LOG)
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)

    def sell_send_order(self, sCode, screen_number, quantity):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, screen_number, self.account_num, 2, sCode, quantity, 0, self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_PRICE],
             ""]
        )
        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_SELL_SUCCESS_LOG % sCode)
        else:
            self.logging.logger.info(self.logType.ORDER_SELL_FAIL_LOG % sCode)

        return order_success

    def new_chejan_slot(self, sGubun, nItemCnt, sFidList):
        if int(sGubun) == 0:
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.STOCK_CODE])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.STOCK_NAME])
            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.ORDER_STATUS])
            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.ORDER_CLASSIFICATION])
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.CONCLUSION_PRICE])
            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)
            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.TIGHTENING_AMOUNT])
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)
            self.logging.logger.info("new_chejan_slot order_status / order_gubun> %s / %s" % (order_status, order_gubun))

            if order_status == self.customType.CONCLUSION:
                self.logging.logger.info(self.logType.CONCLUSION_ORDER_STATUS_LOG % (order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))
                self.line.notification(self.logType.CONCLUSION_ORDER_STATUS_LOG % (order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))

        elif int(sGubun) == 1:  # 잔고

            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.STOCK_CODE])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.ORDER_EXECUTION][self.customType.STOCK_NAME])
            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.SELL_BUY_CLASSIFICATOIN])
            meme_gubun = self.realType.REALTYPE[self.customType.SELLING_CATEGORY][meme_gubun]
            holding_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.HOLDING_QUANTITY])
            holding_quantity = int(holding_quantity)

            available_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.AVAILABLE_QUANTITY])
            available_quantity = int(available_quantity)
            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.PURCHASE_UNIT_PRICE])
            buy_price = abs(int(buy_price))
            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.TOTAL_PURCHASE_PRICE])
            total_buy_price = int(total_buy_price)
            income_rate = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.PROFIT_AND_LOSS])

            self.logging.logger.info(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))
            self.line.notification(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))

            if meme_gubun == self.customType.SELL:
                if holding_quantity > 0:
                    self.current_hold_etf_stock_dict[sCode].update({self.customType.HOLDING_QUANTITY: holding_quantity})
                else:
                    del self.current_hold_etf_stock_dict[sCode]
                    self.check_sell_hold_etf()
            else:
                self.today_buy_etf_stock_dict.update({sCode: {}})

    def call_exit(self):
        self.logging.logger.info("시스템 종료")
        sys.exit()

    def create_analysis_target_etf_file(self):
        self.logging.logger.info("create_analysis_target_etf_file")
        nowDate = get_today_by_format('%Y-%m-%d')
        parent_path = self.sallAnalysisEtfFilePath
        if not os.path.isdir(parent_path):
            os.mkdir(parent_path)
        path = self.sallAnalysisEtfFilePath + '/' + 'target_etf_info' + '_' + nowDate + '.txt'

        for sCode in self.target_etf_stock_dict.keys():
            value = self.target_etf_stock_dict[sCode]
            f = open(path, "a", encoding="utf8")
            f.write("%s\t%s\n" %
                    (sCode, value))
            f.close()
