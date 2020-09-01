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
        self.detail_account_info_event_loop = QEventLoop()
        self.tr_opt10080_info_event_loop = QEventLoop()
        self.not_account_info_event_loop = QEventLoop()
        self.detail_account_mystock_info_event_loop = QEventLoop()
        self.tr_sell_opt10081_info_event_loop = QEventLoop()

        self.today = get_today_by_format('%Y%m%d')

        self.screen_start_stop_real = "1000"
        self.buy_screen_meme_stock = "3000"
        self.sell_screen_meme_stock = "3100"
        self.buy_screen_real_stock = "6000"
        self.screen_etf_stock = "4020"
        self.screen_opt10080_info = "4030"

        self.max_hold_stock_count = 6
        self.max_buy_amount_by_stock = 50000

        self.analysis_search_timer1 = QTimer()
        self.analysis_search_timer2 = QTimer()
        self.system_off_check_timer = QTimer()
        self.hold_stock_check_timer = QTimer()

        self.current_hold_stock_count = 0

        self.current_hold_etf_stock_dict = {}

        self.today_buy_etf_stock_dict = {}
        self.target_etf_stock_dict = {}
        self.analysis_goal_etf_stock_dict = {}
        self.analysis_goal_etf_stock_list = []
        self.goal_buy_search_stock_code = ''
        self.search_stock_code = []

        self.analysis_sell_etf_stock_list = []
        self.sell_search_stock_code = ''

        self.short_trade_target_stock_dict = {}
        self.short_trade_stock_order_dict = {}
        self.set_short_trade_stock_info()

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF DAY TRADE START")

        self.detail_account_info()
        QTest.qWait(5000)

        self.detail_account_mystock()
        QTest.qWait(5000)
        self.current_hold_stock_count = len(self.current_hold_etf_stock_dict.keys())

        self.get_search_goal_price_etf()
        QTest.qWait(5000)

        if self.current_hold_stock_count > 0:
            self.loop_check_sell_hold_etf()

        self.loop_analysis_buy_etf()
        self.loop_system_off()

        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

        if len(self.short_trade_target_stock_dict.keys()) > 0:
            self.loop_analysis_short_trade_buy_etf()

    def loop_check_sell_hold_etf(self):
        self.hold_stock_check_timer.stop()
        self.hold_stock_check_timer = default_q_timer_setting()
        self.hold_stock_check_timer.timeout.connect(self.check_sell_hold_etf)

    def check_sell_hold_etf(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        self.hold_stock_check_timer.stop()
        if (self.today + '150000') < currentDate:
            return
        self.loop_sell_hold_etf_stock()

    def loop_sell_hold_etf_stock(self):
        self.logging.logger.info('loop_sell_hold_etf_stock')
        self.sell_search_stock_code = ''
        self.analysis_sell_etf_stock_list = []
        for key in self.current_hold_etf_stock_dict.keys():
            self.analysis_sell_etf_stock_list.append(copy.deepcopy(self.current_hold_etf_stock_dict[key]))
        self.hold_stock_check_timer = default_q_timer_setting(300)
        self.hold_stock_check_timer.timeout.connect(self.daily_candle_sell_point_check)

    def daily_candle_sell_point_check(self):
        if len(self.analysis_sell_etf_stock_list) == 0:
            self.logging.logger.info("analysis_sell_etf_stock_list nothing")
            self.hold_stock_check_timer.stop()
            return

        self.get_sell_next_search_etf_stock_code(len(self.analysis_sell_etf_stock_list))

        code = self.sell_search_stock_code
        self.logging.logger.info("analysis_sell_etf_stock_list loop > %s " % code)

        self.get_sell_opt10081_info(code)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        target_dict = self.current_hold_etf_stock_dict

        max_profit_sell_point = self.get_max_profit_sell_case(code, target_dict)
        if bool(max_profit_sell_point):
            self.hold_stock_check_timer.stop()
            quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            self.logging.logger.info("max_profit_sell_point break >> %s" % code)
            self.sell_send_order(code, self.sell_screen_meme_stock, quantity)
            del self.current_hold_etf_stock_dict[code]

        stop_loss_sell_point = self.get_stop_loss_sell_point(code, target_dict)
        if bool(stop_loss_sell_point):
            self.hold_stock_check_timer.stop()
            quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            self.logging.logger.info("stop_loss_sell_point break >> %s" % code)
            self.sell_send_order(code, self.sell_screen_meme_stock, quantity)
            del self.current_hold_etf_stock_dict[code]

        ma20_line_sell_point = self.get_ma20_line_sell_point(code, target_dict)
        if bool(ma20_line_sell_point):
            self.hold_stock_check_timer.stop()
            quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            self.logging.logger.info("ma20_line_sell_point break >> %s" % code)
            self.sell_send_order(code, self.sell_screen_meme_stock, quantity)
            del self.current_hold_etf_stock_dict[code]

        self.logging.logger.info('daily_candle_sell_point_check end')

    def set_short_trade_stock_info(self):
        self.short_trade_target_stock_dict.update({'122630': {"row": []}})
        self.short_trade_target_stock_dict.update({'252670': {"row": []}})
        self.short_trade_target_stock_dict.update({'233740': {"row": []}})
        self.short_trade_target_stock_dict.update({'251340': {"row": []}})

    def loop_analysis_short_trade_buy_etf(self):
        result = True
        while result:
            result = self.analysis_short_trade_candle_info()

    def loop_analysis_buy_etf(self):
        self.analysis_search_timer1 = default_q_timer_setting(60)
        self.analysis_search_timer1.timeout.connect(self.loop_other_target_buy_etf_stock)

    def analysis_short_trade_candle_info(self):
        short_trade_stock_order_list = list(self.short_trade_stock_order_dict.keys())
        for code in self.short_trade_target_stock_dict.keys():

            loop_sleep = QEventLoop()
            QTimer.singleShot(4 * 1000, loop_sleep.quit)
            loop_sleep.exec_()

            currentDate = get_today_by_format('%Y%m%d%H%M%S')
            if (self.today + '145900') < currentDate:
                for order_code in short_trade_stock_order_list:
                    self.logging.logger.info('short_trade time over sell send order: %s' % order_code)

                    self.sell_send_order(code, self.sell_screen_meme_stock, self.short_trade_stock_order_dict[order_code][self.customType.HOLDING_QUANTITY])
                return False

            if code in short_trade_stock_order_list:
                self.get_opt10080_info(code)

                self.logging.logger.info('loop short_trade_stock_order_list: %s' % code)
                if self.short_trade_stock_order_dict[code][self.customType.ORDER_STATUS] == 'wait':
                    tightening_time = self.short_trade_stock_order_dict[code][self.customType.TIGHTENING_TIME]
                    buy_after_tic_rows = [x for x in self.short_trade_target_stock_dict[code]["row"] if x[self.customType.TIGHTENING_TIME] > tightening_time]
                    if len(buy_after_tic_rows) > 0:
                        self.logging.logger.info('not_concluded_account: %s' % buy_after_tic_rows)
                        self.not_concluded_account()
                        continue

                if self.short_trade_stock_order_dict[code][self.customType.ORDER_STATUS] == self.customType.BALANCE:
                    rows = self.short_trade_target_stock_dict[code]["row"]
                    first_tic = rows[0]
                    current_price = first_tic[self.customType.CURRENT_PRICE]
                    buy_price = self.short_trade_stock_order_dict[code][self.customType.PURCHASE_PRICE]
                    if self.short_trade_max_profit_case(code, current_price, buy_price):
                        self.logging.logger.info('short_trade_max_profit_case: %s / %s' % (current_price, buy_price))
                        self.sell_send_order(code, self.sell_screen_meme_stock, self.short_trade_stock_order_dict[code][self.customType.HOLDING_QUANTITY])
                        del self.short_trade_stock_order_dict[code]
                        continue

                    create_moving_average_gap_line(code, self.short_trade_target_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)

                    short_trade_sell_point = self.short_trade_sell_case(code)
                    if bool(short_trade_sell_point):
                        self.logging.logger.info('short_trade_sell_point: %s' % short_trade_sell_point)
                        self.sell_send_order(code, self.sell_screen_meme_stock, self.short_trade_stock_order_dict[code][self.customType.HOLDING_QUANTITY])
                        del self.short_trade_stock_order_dict[code]
                        continue
            else:
                if (self.today + '143100') < currentDate:
                    continue

                self.get_opt10080_info(code)

                self.logging.logger.info('loop short_trade_target_stock_dict: %s' % code)
                create_moving_average_gap_line(code, self.short_trade_target_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
                create_moving_average_gap_line(code, self.short_trade_target_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
                create_moving_average_gap_line(code, self.short_trade_target_stock_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
                create_moving_average_gap_line(code, self.short_trade_target_stock_dict, "row", self.customType.CURRENT_PRICE, "ma60", 60)
                create_moving_average_gap_line(code, self.short_trade_target_stock_dict, "row", self.customType.CURRENT_PRICE, "ma120", 120)

                rows = self.short_trade_target_stock_dict[code]["row"]
                short_trade_buy_point = self.get_conform_short_trade_buy_case(code, rows)

                if bool(short_trade_buy_point):
                    limit_price = short_trade_buy_point[self.customType.CURRENT_PRICE]
                    result = self.max_buy_amount_by_stock / limit_price
                    quantity = int(result)
                    if quantity >= 1:
                        self.logging.logger.info("short_trade_buy_point break")
                        self.short_trade_stock_order_dict.update({code: {self.customType.TIGHTENING_TIME: currentDate, self.customType.PURCHASE_PRICE: limit_price,
                                                                         self.customType.HOLDING_QUANTITY: quantity, self.customType.ORDER_STATUS: "wait"}})
                        self.send_order_limit_stock_price(code, quantity, limit_price)

        return True

    def get_conform_short_trade_buy_case(self, code, rows):
        if len(rows) < 10:
            return {}

        analysis_rows = rows[:10]
        compare_rows = analysis_rows[:3]

        first_tic = compare_rows[0]
        second_tic = compare_rows[1]
        third_tic = compare_rows[2]
        ma_field_list = ["ma20", "ma5", "ma10", "ma60", "ma120"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("short_trade_buy_case analysis_rows > [%s] >> %s " % (code, compare_rows))

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

        last_price_list = [item["ma5"] for item in compare_rows]
        inverselist = last_price_list[::-1]
        if not is_increase_trend(inverselist):
            self.logging.logger.info("is_increase_trend check> [%s]  " % code)
            return {}

        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s]" % code)
                return {}

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 0.99:
            self.logging.logger.info("first_tic max gap with ma20 check > [%s]" % code)
            return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s]" % code)
            return {}

        if second_tic[self.customType.LOWEST_PRICE] < second_tic["ma20"] < second_tic[self.customType.HIGHEST_PRICE] or third_tic[self.customType.LOWEST_PRICE] < third_tic["ma20"] < third_tic[self.customType.HIGHEST_PRICE]:
            pass
        else:
            self.logging.logger.info("second_tic or third_tic position check > [%s] " % code)
            return {}

        self.logging.logger.info("short_trade_buy_case check> [%s] >> %s" % (code, first_tic))
        return copy.deepcopy(first_tic)

    def short_trade_sell_case(self, code):
        rows = self.short_trade_target_stock_dict[code]["row"]
        first_tic = rows[0]
        if first_tic["ma20"] == '':
            return {}

        self.logging.logger.info("short_trade_sell_case first_tic > [%s] >> %s " % (code, first_tic))
        current_price = first_tic[self.customType.CURRENT_PRICE]
        buy_price = self.short_trade_stock_order_dict[code][self.customType.PURCHASE_PRICE]
        first_tic_ma20 = first_tic["ma20"]
        if current_price < buy_price:
            if first_tic_ma20 >= current_price:
                return copy.deepcopy(first_tic)

        tightening_time = self.short_trade_stock_order_dict[code][self.customType.TIGHTENING_TIME]

        buy_after_tic_rows = [x for x in rows if x[self.customType.TIGHTENING_TIME] > tightening_time]
        if len(buy_after_tic_rows) > 0:

            max_highest_price = max([item[self.customType.HIGHEST_PRICE] for item in buy_after_tic_rows])

            goni_price = buy_price + ((max_highest_price - buy_price) / 2)
            if goni_price >= buy_price + 15:
                if buy_price + 5 > first_tic_ma20:
                    std_price = goni_price
                else:
                    if first_tic_ma20 < goni_price:
                        std_price = goni_price
                    else:
                        std_price = first_tic_ma20
            else:
                std_price = first_tic_ma20

            if std_price >= current_price:
                return copy.deepcopy(first_tic)

        return {}

    def short_trade_max_profit_case(self, code, current_price, buy_price):

        if current_price > buy_price:
            profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
            if profit_rate > 2:
                self.logging.logger.info("short_trade_max_profit_case check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, profit_rate))
                return True
        return False

    def get_ma20_line_sell_point(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        first_tic = analysis_rows[0]
        current_price = first_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        ma20_price = first_tic["ma20"]

        if buy_price > current_price:
            if ma20_price > current_price:
                self.logging.logger.info("loss ma20_price check > [%s] >> %s / %s" % (code, current_price, ma20_price))
                return copy.deepcopy(first_tic)
        else:
            if (ma20_price - 5) > current_price:
                self.logging.logger.info("profit ma20_price check > [%s] >> %s / %s" % (code, current_price, ma20_price))
                return copy.deepcopy(first_tic)
        return {}

    def get_stop_loss_sell_point(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        first_tic = analysis_rows[0]
        current_price = first_tic[self.customType.CURRENT_PRICE]
        highest_price = first_tic[self.customType.HIGHEST_PRICE]

        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]

        stop_rate = 11
        loss_rate = 10

        if current_price > buy_price:
            highest_price_profit_rate = round((highest_price - buy_price) / buy_price * 100, 2)
            if highest_price > current_price and highest_price_profit_rate >= stop_rate:
                profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
                if profit_rate <= loss_rate:
                    self.logging.logger.info("stop_loss_profit check > [%s] >> %s / %s / %s / %s" % (code, current_price, buy_price, highest_price_profit_rate, profit_rate))
                    return copy.deepcopy(first_tic)
        return {}

    def get_max_profit_sell_case(self, code, target_dict):

        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        first_tic = analysis_rows[0]
        current_price = first_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]

        if current_price > buy_price:
            profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
            if profit_rate > 15:
                self.logging.logger.info("max_profit check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, profit_rate))
                return copy.deepcopy(first_tic)
        return {}

    def get_opt10080_info(self, code):
        self.tr_opt10080_info(code)

    def loop_other_target_buy_etf_stock(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '100000') <= currentDate <= (self.today + '101000') or (self.today + '110000') <= currentDate <= (self.today + '111000') or (self.today + '120000') <= currentDate <= (self.today + '121000') :
            self.analysis_search_timer1.stop()
            self.goal_buy_search_stock_code = ''
            self.analysis_goal_etf_stock_list = []
            self.search_stock_code = []
            for key in self.target_etf_stock_dict.keys():
                if key not in self.current_hold_etf_stock_dict.keys() and key not in self.today_buy_etf_stock_dict.keys():
                    self.analysis_goal_etf_stock_list.append(copy.deepcopy(self.target_etf_stock_dict[key]))
            self.analysis_search_timer2 = default_q_timer_setting(5)
            self.analysis_search_timer2.timeout.connect(self.other_target_candle_analysis_check)
            self.analysis_search_timer1.start()

    def other_target_candle_analysis_check(self):
        if self.current_hold_stock_count == self.max_hold_stock_count:
            self.logging.logger.info("max buy stock")
            self.analysis_search_timer2.stop()
            return

        if len(self.analysis_goal_etf_stock_list) == 0:
            self.logging.logger.info("other_target_candle_analysis nothing")
            self.analysis_search_timer2.stop()
            return

        self.get_next_search_etf_stock_code(len(self.analysis_goal_etf_stock_list))

        code = self.goal_buy_search_stock_code
        self.logging.logger.info("other_target_candle_analysis_check loop > %s " % code)
        self.search_stock_code.append(code)

        self.get_opt10081_info_all(code)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
        rows = self.target_etf_stock_dict[code]["row"]
        buy_point = self.get_conform_hammer_case(code, rows)

        if bool(buy_point):
            if self.current_hold_stock_count < self.max_hold_stock_count:
                quantity = math.trunc(self.max_buy_amount_by_stock / buy_point[self.customType.CURRENT_PRICE])
                if quantity >= 1:
                    self.logging.logger.info("conform_hammer_case buy_point break >> %s" % code)
                    self.current_hold_stock_count = self.current_hold_stock_count + 1
                    self.market_price_send_order(code, quantity)

        if len(self.search_stock_code) == len(self.analysis_goal_etf_stock_list):
            self.logging.logger.info("other_target_candle_analysis_check end")
            self.analysis_search_timer2.stop()
            return

    def get_default_price_info(self):
        self.read_target_etf_file()
        QTest.qWait(5000)

        self.get_all_etf_info()
        QTest.qWait(5000)

    def get_search_goal_price_etf(self):
        self.get_default_price_info()
        # self.get_goal_price_etf()
        # self.create_analysis_target_etf_file()
        # QTest.qWait(5000)
        self.screen_number_setting(self.target_etf_stock_dict)

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)

    def get_opt10081_info(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MODIFIED_SHARE_PRICE, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exec_()

    def get_opt10081_info_all(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MODIFIED_SHARE_PRICE, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10081_all", "opt10081", 0, self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exec_()

    def get_conform_hammer_case(self, code, rows):

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]

        first_tic = analysis_rows[0]
        ma_field_list = ["ma20", "ma5", "ma10"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("hammer_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        if first_tic["ma5"] >= first_tic["ma20"]:
            pass
        else:
            self.logging.logger.info("is regular arrangement check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic))
                return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s] >> %s " % (code, first_tic))
            return {}


        return copy.deepcopy(first_tic)

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

    def tr_opt10080_info(self, code, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TIC_RANGE, "3분")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MODIFIED_SHARE_PRICE, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10080", "opt10080", sPrevNext, self.screen_opt10080_info)

        self.tr_opt10080_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0"):
        self.logging.logger.info("not_concluded_account")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_etf_stock)

        self.not_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_mystock")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00018, "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_mystock_info_event_loop.exec_()

    def get_sell_opt10081_info(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MODIFIED_SHARE_PRICE, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_sell_opt10081", "opt10081", 0, self.screen_etf_stock)
        self.tr_sell_opt10081_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

        elif sRQName == "tr_opt10081":
            self.trdata_slot_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081_all":
            self.trdata_slot_opt10081_all(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10080":
            self.trdata_slot_opt10080(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "실시간미체결요청":
            self.trdata_slot_opt10075(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPW00018:
            self.trdata_slot_opw00018(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_sell_opt10081":
            self.trdata_slot_sell_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_sell_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.current_hold_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_sell_opt10081_info_event_loop.exit()

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

    def trdata_slot_opt10075(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(rows):
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_CODE)
            order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.ORDER_NO)
            order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.ORDER_CLASSIFICATION)

            code = code.strip()
            order_no = int(order_no.strip())
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            if order_gubun == self.customType.BUY:
                if code in self.short_trade_stock_order_dict.keys() and self.short_trade_stock_order_dict[code][self.customType.ORDER_STATUS] == 'wait':
                    order_success = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [self.customType.BUY_CANCLE, self.buy_screen_real_stock, self.account_num, 3, code, 0, 0,
                         self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], order_no]
                    )

                    if order_success == 0:
                        self.logging.logger.debug(self.logType.CANCLE_ORDER_BUY_SUCCESS_LOG)
                        del self.short_trade_stock_order_dict[code]
                    else:
                        self.logging.logger.debug(self.logType.CANCLE_ORDER_BUY_FAIL_LOG)

        self.not_account_info_event_loop.exit()

    def trdata_slot_opt10080(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info('trdata_slot_opt10080 > [%s][%s]' % (sScrNo, sRQName))
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        new_rows = []
        cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

        for i in range(cnt):
            a = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.CURRENT_PRICE)
            a = abs(int(a.strip()))
            b = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            b = abs(int(b.strip()))
            c = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TIGHTENING_TIME)
            c = c.strip()
            d = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.START_PRICE)
            d = abs(int(d.strip()))
            e = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HIGHEST_PRICE)
            e = abs(int(e.strip()))
            f = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LOWEST_PRICE)
            f = abs(int(f.strip()))

            row = {self.customType.CURRENT_PRICE: a, self.customType.VOLUME: b, self.customType.TIGHTENING_TIME: c, self.customType.START_PRICE: d, self.customType.HIGHEST_PRICE: e,
                   self.customType.LOWEST_PRICE: f, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.short_trade_target_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_opt10080_info)
        self.tr_opt10080_info_event_loop.exit()

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

    def trdata_slot_opt10081(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, "ma20": '', "ma5": '', "ma10": ''}
            new_rows.append(row)

        self.analysis_goal_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exit()

    def trdata_slot_opt10081_all(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, "ma20": '', "ma5": '', "ma10": ''}
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
                    if stock_code not in self.short_trade_target_stock_dict.keys():
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
                    self.analysis_goal_etf_stock_dict.update({code: {self.customType.STOCK_CODE: code, self.customType.GOAL_PRICE: goal_stock_price, "row": []}})

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

    def send_order_limit_stock_price(self, code, quantity, limit_stock_price):
        self.logging.logger.info("send_order_limit_stock_price > %s " % code)
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, self.buy_screen_real_stock, self.account_num, 1, code, quantity, limit_stock_price,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

        if order_success == 0:
            self.logging.logger.info(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity, limit_stock_price, self.purchased_deposit))
            self.line.notification(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity, limit_stock_price, self.purchased_deposit))
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)

    def send_order_market_off_price_stock_price(self, code, quantity):
        self.logging.logger.info("send_order_market_price_stock_price > %s " % code)
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, self.buy_screen_real_stock, self.account_num, 1, code, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_OFF_TIME_LAST_PRICE], ""])

        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_BUY_SUCCESS_LOG)
            self.line.notification(self.logType.ORDER_BUY_SUCCESS_LOG)
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)

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
                pass
            else:
                if sCode not in self.today_buy_etf_stock_dict.keys():
                    self.today_buy_etf_stock_dict.update({sCode: {self.customType.PURCHASE_PRICE: buy_price,
                                                                  self.customType.TIGHTENING_TIME: get_today_by_format('%Y%m%d%H%M%S'),
                                                                  self.customType.TOTAL_PURCHASE_PRICE: total_buy_price}})
                if sCode in self.short_trade_stock_order_dict.keys():
                    if holding_quantity > 0:
                        self.short_trade_stock_order_dict[sCode].update({self.customType.ORDER_STATUS: self.customType.BALANCE})
                        self.short_trade_stock_order_dict[sCode].update({self.customType.TIGHTENING_TIME: get_today_by_format('%Y%m%d%H%M%S')})
                        self.short_trade_stock_order_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price})
                        self.short_trade_stock_order_dict[sCode].update({self.customType.TOTAL_PURCHASE_PRICE: total_buy_price})

    def call_exit(self):
        self.logging.logger.info("시스템 종료")
        sys.exit()

    def loop_system_off(self):
        self.system_off_check_timer = default_q_timer_setting(60)
        self.system_off_check_timer.timeout.connect(self.check_system_off_time)

    def check_system_off_time(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '160000') < currentDate:
            self.system_off_check_timer.stop()
            self.call_exit()

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
