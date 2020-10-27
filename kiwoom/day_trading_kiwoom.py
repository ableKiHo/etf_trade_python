import sys

from PyQt5.QtCore import QTimer, QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


def default_q_timer_setting(second=3.8):
    timer2 = QTimer()
    timer2.start(1000 * second)
    return timer2


def reset(second=3.5):
    loop = QEventLoop()
    QTimer.singleShot(1000 * second, loop.quit)  # msec
    loop.exec_()


class DayTradingKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF DayTradingKiwoom() class start.")
        self.line.notification("ETF DayTradingKiwoom() class start.")

        self.etf_info_event_loop = QEventLoop()
        self.tr_opt10081_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_mystock_info_event_loop = QEventLoop()
        self.tr_sell_opt10081_info_event_loop = QEventLoop()
        self.not_account_info_event_loop = QEventLoop()

        self.today = get_today_by_format('%Y%m%d')

        self.screen_start_stop_real = "1000"
        self.buy_screen_meme_stock = "3000"
        self.sell_screen_meme_stock = "3100"
        self.buy_screen_real_stock = "6000"
        self.screen_etf_stock = "4020"
        self.screen_opt10080_info = "4030"
        self.screen_sell_opt10081_info = "4040"

        self.max_hold_stock_count = 0
        self.max_buy_amount_by_stock = 50000
        self.max_invest_amount = 300000
        self.total_invest_amount = 0
        self.total_inverse_amount = 0

        self.analysis_search_timer1 = QTimer()
        self.analysis_search_timer2 = QTimer()
        self.system_off_check_timer = QTimer()
        self.hold_stock_check_timer = QTimer()
        self.cancle_check_timer = QTimer()

        self.analysis_goni_timer1 = QTimer()
        self.analysis_goni_timer2 = QTimer()

        self.current_hold_stock_count = 0

        self.current_hold_etf_stock_dict = {}

        self.total_cal_target_etf_stock_dict = {}
        self.today_buy_etf_stock_dict = {}
        self.target_etf_stock_dict = {}
        self.analysis_goal_etf_stock_dict = {}
        self.analysis_goal_etf_stock_list = []
        self.goal_buy_search_stock_code = ''
        self.search_stock_code = []
        self.sell_receive_stock_code = []

        self.analysis_sell_etf_stock_list = []
        self.sell_search_stock_code = ''
        self.sell_search_stock_code_list = []

        self.analysis_goni_etf_stock_list = []
        self.goni_search_stock_code = ''
        self.goni_search_stock_code_list = []

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF DAY TRADE START")

        self.detail_account_info()
        QTest.qWait(5000)

        self.detail_account_mystock()
        QTest.qWait(5000)
        self.init_stock_values()

        self.get_search_goal_price_etf()
        QTest.qWait(5000)

        self.loop_analysis_buy_etf()
        self.loop_system_off()
        self.loop_sell_hold_etf_stock()
        # self.loop_cancle_buy_etf()
        self.loop_goni_hold_etf_stock()

        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

    def current_hold_stock_real_reg(self):
        for code in self.current_hold_etf_stock_dict.keys():
            screen_num = self.current_hold_etf_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.logging.logger.info("current_hold_stock_real_reg >> %s %s" % (code, screen_num))
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def init_stock_values(self):
        self.current_hold_stock_count = len(self.current_hold_etf_stock_dict.keys())
        if self.current_hold_stock_count == 6:
            self.max_hold_stock_count = self.current_hold_stock_count
            return

        able_addbuy_stock_count = int((self.max_invest_amount - self.total_invest_amount) / self.max_buy_amount_by_stock)
        if able_addbuy_stock_count > 0:
            self.max_hold_stock_count = self.current_hold_stock_count + able_addbuy_stock_count
        else:
            self.max_hold_stock_count = self.current_hold_stock_count

        self.screen_number_setting(self.current_hold_etf_stock_dict)

    def loop_cancle_buy_etf(self):
        self.cancle_check_timer = default_q_timer_setting(120)
        self.cancle_check_timer.timeout.connect(self.cancle_buy_etf)

    def cancle_buy_etf(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '105700') <= currentDate <= (self.today + '110000'):
            pass
        elif (self.today + '115700') <= currentDate <= (self.today + '120000'):
            pass
        elif (self.today + '125700') <= currentDate <= (self.today + '130000'):
            pass
        else:
            return

        self.not_concluded_account()

    def loop_goni_hold_etf_stock(self):
        self.analysis_goni_timer1 = default_q_timer_setting(60)
        self.analysis_goni_timer1.timeout.connect(self.analysis_goni_hold_etf_stock)

    def analysis_goni_hold_etf_stock(self):

        self.analysis_goni_timer1.stop()
        self.logging.logger.info('loop_goni_hold_etf_stock')
        self.sell_search_stock_code_list = []
        self.sell_search_stock_code = ''
        self.analysis_sell_etf_stock_list = []
        for key in self.current_hold_etf_stock_dict.keys():
            if key not in self.sell_receive_stock_code:
                self.analysis_sell_etf_stock_list.append(copy.deepcopy(self.current_hold_etf_stock_dict[key]))

        self.analysis_goni_timer2 = default_q_timer_setting(4)
        self.analysis_goni_timer2.timeout.connect(self.daily_candle_goni_point_check)

    def realtime_stop_loss_sell(self, code):
        quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
        self.logging.logger.info("realtime_stop_loss_sell_point break >> %s" % code)
        self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
        self.sell_receive_stock_code.append(code)

    def daily_candle_goni_point_check(self):
        if len(self.analysis_sell_etf_stock_list) == 0:
            self.logging.logger.info("analysis_sell_etf_stock_list nothing")
            self.analysis_goni_timer2.stop()
            return

        self.get_sell_next_search_etf_stock_code(len(self.analysis_sell_etf_stock_list))

        code = self.sell_search_stock_code
        self.logging.logger.info("daily_candle_goni_point_check loop > %s " % code)
        self.sell_search_stock_code_list.append(code)

        self.get_sell_opt10081_info(code)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)

        # realtime_stop_loss_sell_point = self.get_realtime_stop_loss_sell_point(code, self.current_hold_etf_stock_dict)
        # if bool(realtime_stop_loss_sell_point):
        #     self.analysis_goni_timer2.stop()
        #     quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
        #     self.logging.logger.info("realtime_stop_loss_sell_point break >> %s" % code)
        #     self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
        #     self.sell_receive_stock_code.append(code)
        #     return

        # goni_sell_point = self.get_stop_goni_sell_point(code, self.current_hold_etf_stock_dict)
        # if bool(goni_sell_point):
        #     self.analysis_goni_timer2.stop()
        #     quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
        #     self.logging.logger.info("stop_goni_sell_point break >> %s" % code)
        #     self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
        #     self.sell_receive_stock_code.append(code)
        #     return

        if len(self.sell_search_stock_code_list) == len(self.analysis_sell_etf_stock_list):
            self.logging.logger.info("daily_candle_goni_point_check end")
            self.analysis_goni_timer2.stop()
            #self.analysis_goni_timer1.start()
            self.current_hold_stock_real_reg()

    def loop_sell_hold_etf_stock(self):
        self.hold_stock_check_timer = default_q_timer_setting(120)
        self.hold_stock_check_timer.timeout.connect(self.analysis_hold_etf_stock)

    def analysis_hold_etf_stock(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '150000') <= currentDate <= (self.today + '150500'):
            pass
        else:
            return
        self.hold_stock_check_timer.stop()
        self.logging.logger.info('loop_sell_hold_etf_stock')
        self.sell_search_stock_code_list = []
        self.sell_search_stock_code = ''
        self.analysis_sell_etf_stock_list = []
        for key in self.current_hold_etf_stock_dict.keys():
            self.analysis_sell_etf_stock_list.append(copy.deepcopy(self.current_hold_etf_stock_dict[key]))

        self.hold_stock_check_timer = default_q_timer_setting(4)
        self.hold_stock_check_timer.timeout.connect(self.daily_candle_sell_point_check)

    def daily_candle_sell_point_check(self):
        if len(self.analysis_sell_etf_stock_list) == 0:
            self.logging.logger.info("analysis_sell_etf_stock_list nothing")
            self.hold_stock_check_timer.stop()
            return

        self.get_sell_next_search_etf_stock_code(len(self.analysis_sell_etf_stock_list))

        code = self.sell_search_stock_code
        self.logging.logger.info("analysis_sell_etf_stock_list loop > %s " % code)
        self.sell_search_stock_code_list.append(code)

        self.get_sell_opt10081_info(code)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma3", 3)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)

        if code not in self.default_stock_list:

            # max_loss_sell_point = self.get_max_loss_sell_case(code, self.current_hold_etf_stock_dict)
            # if bool(max_loss_sell_point):
            #     self.hold_stock_check_timer.stop()
            #     quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            #     self.logging.logger.info("max_loss_sell_point break >> %s" % code)
            #     self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
            #     self.sell_receive_stock_code.append(code)
            #     return

            add_buy_point = self.get_conform_add_stock_buy_case(code, self.current_hold_etf_stock_dict)
            if bool(add_buy_point):
                self.logging.logger.info("conform_add_stock_buy_case buy_point break >> %s" % code)
                limit_price = add_buy_point[self.customType.CURRENT_PRICE] - 10
                self.total_invest_amount = self.total_invest_amount + limit_price
                self.send_order_limit_stock_price(code, 1, limit_price)

            # under_ma20_line = self.get_under_ma20_line(code, self.current_hold_etf_stock_dict)
            # if bool(under_ma20_line):
            #     self.hold_stock_check_timer.stop()
            #     quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            #     self.logging.logger.info("under_ma20_line_sell_point break >> %s" % code)
            #     self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
            #     del self.current_hold_etf_stock_dict[code]
            #     return
            #
            # maintain_under_ma5_line = self.get_maintain_under_ma5_line(code, self.current_hold_etf_stock_dict)
            # if bool(maintain_under_ma5_line):
            #     self.hold_stock_check_timer.stop()
            #     quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            #     quantity = int(quantity / 2)
            #     if quantity > 1:
            #         self.logging.logger.info("maintain_under_ma5_line_sell_point break >> %s" % code)
            #         self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
            #     return

            # maintain_under_one_percent = self.get_maintain_under_one_percent(code, self.current_hold_etf_stock_dict)
            # if bool(maintain_under_one_percent):
            #     self.hold_stock_check_timer.stop()
            #     quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            #     self.logging.logger.info("maintain_under_one_percent_sell_point break >> %s" % code)
            #     self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
            #     del self.current_hold_etf_stock_dict[code]
            #     return
        else:
            default_stock_under_ma3_line = self.get_default_stock_under_ma3_line(code, self.current_hold_etf_stock_dict)
            if bool(default_stock_under_ma3_line):
                self.hold_stock_check_timer.stop()
                quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
                self.logging.logger.info("default_stock_under_ma3_line_sell_point break >> %s" % code)
                self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
                self.sell_receive_stock_code.append(code)
                return

        max_profit_sell_point = self.get_max_profit_sell_case(code, self.current_hold_etf_stock_dict)
        if bool(max_profit_sell_point):
            self.hold_stock_check_timer.stop()
            quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            self.logging.logger.info("max_profit_sell_point break >> %s" % code)
            self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
            self.sell_receive_stock_code.append(code)
            return

        stop_rate_list = [11, 8, 6]
        for stop_rate in stop_rate_list:
            stop_loss_sell_point = self.get_stop_loss_sell_point(code, self.current_hold_etf_stock_dict, stop_rate)
            if bool(stop_loss_sell_point):
                self.hold_stock_check_timer.stop()
                quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
                self.logging.logger.info("stop_loss_sell_point break >> %s" % code)
                self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
                self.sell_receive_stock_code.append(code)
                return

        big_loss_sell_point = self.get_stop_big_loss_sell_point(code, self.current_hold_etf_stock_dict)
        if bool(big_loss_sell_point):
            self.hold_stock_check_timer.stop()
            quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
            self.logging.logger.info("stop_big_loss_sell_point break >> %s" % code)
            self.sell_send_order_favorable_limit_price(code, self.sell_screen_meme_stock, quantity)
            self.sell_receive_stock_code.append(code)
            return

        if len(self.sell_search_stock_code_list) == len(self.analysis_sell_etf_stock_list):
            self.logging.logger.info("daily_candle_sell_point_check end")
            self.hold_stock_check_timer.stop()
            self.current_hold_stock_real_reg()

    def loop_analysis_buy_etf(self):
        self.analysis_search_timer1 = default_q_timer_setting(60)
        self.analysis_search_timer1.timeout.connect(self.loop_other_target_buy_etf_stock)

    def get_add_buy_point(self, code, target_dict, target_field, target_amount):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]

        empty_gap_list = [x for x in analysis_rows if x[target_field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("sell_point analysis_rows > [%s] >> %s " % (code, analysis_rows))
        today_tic = analysis_rows[0]
        yesterday_tic = analysis_rows[1]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        total_chegual_price = target_dict[code][self.customType.PURCHASE_AMOUNT]
        if total_chegual_price <= target_amount and buy_price > current_price:
            if yesterday_tic[target_field] > yesterday_tic[self.customType.CURRENT_PRICE] and today_tic[target_field] <= current_price:
                self.logging.logger.info("today current price pass to ma5 line check > [%s] >> %s " % (code, today_tic))
                return copy.deepcopy(today_tic)

        return {}

    def get_realtime_stop_loss_sell_point(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        buy_after_rows = [x for x in rows if x[self.customType.DATE] > target_dict[code][self.customType.DATE]]
        if len(buy_after_rows) < 1:
            return {}

        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        profit_rate = round((current_price - buy_price) / buy_price * 100, 2)

        highest_list = [item[self.customType.HIGHEST_PRICE] for item in buy_after_rows]
        max_highest_price = max(highest_list)
        highest_profit_rate = round((max_highest_price - buy_price) / buy_price * 100, 2)

        if buy_price < current_price:
            if profit_rate > 15.0:
                self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)

            if 7.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 5.55:
                self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)

            if 5.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 3.55:
                self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)

            if 3.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 2.55:
                self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)

            if 2.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 2.05:
                self.logging.logger.info("goni_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)

            if 2.0 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 1.55:
                self.logging.logger.info("goni_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)

            if 1.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 1.05:
                self.logging.logger.info("goni_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)
        return {}

    def get_min_stop_loss_sell_point(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        buy_after_rows = [x for x in rows if x[self.customType.DATE] > target_dict[code][self.customType.DATE]]
        if len(buy_after_rows) < 1:
            return {}

        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        profit_rate = round((current_price - buy_price) / buy_price * 100, 2)

        highest_list = [item[self.customType.HIGHEST_PRICE] for item in buy_after_rows]
        max_highest_price = max(highest_list)
        highest_profit_rate = round((max_highest_price - buy_price) / buy_price * 100, 2)

        if buy_price < current_price < today_tic["ma5"]:
            if 1.1 <= highest_profit_rate < 2.0 and profit_rate < 1.1:
                self.logging.logger.info("min_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (code, current_price, profit_rate, highest_profit_rate))
                return copy.deepcopy(today_tic)
        return {}

    def get_maintain_under_one_percent(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        buy_after_rows = [x for x in rows if x[self.customType.DATE] > target_dict[code][self.customType.DATE]]
        if len(buy_after_rows) < 8:
            return {}

        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        profit_rate = round((current_price - buy_price) / buy_price * 100, 2)

        if buy_price < current_price < today_tic["ma5"]:
            if 0.5 <= profit_rate < 1.0:
                self.logging.logger.info("maintain_under_one_percent check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, profit_rate))
                return copy.deepcopy(today_tic)

        return {}

    def get_stop_goni_sell_point(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        buy_after_rows = [x for x in rows if x[self.customType.DATE] > target_dict[code][self.customType.DATE]]
        if len(buy_after_rows) < 1:
            return {}

        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        profit_rate = round((current_price - buy_price) / buy_price * 100, 2)

        highest_list = [item[self.customType.HIGHEST_PRICE] for item in buy_after_rows]
        half_plus_price = get_plus_sell_std_price(buy_price, max(highest_list))

        max_highest_price = max(highest_list)
        highest_profit_rate = round((max_highest_price - buy_price) / buy_price * 100, 2)
        if highest_profit_rate < 2.0:
            return {}

        if buy_price < current_price:
            if 1 < profit_rate and half_plus_price > current_price:
                self.logging.logger.info("stop_half_plus_price check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, half_plus_price))
                return copy.deepcopy(today_tic)

        return {}

    def get_stop_big_loss_sell_point(self, code, target_dict):
        big_loss_rate = 2.5
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]
        last_day_tic = analysis_rows[1]

        current_price = today_tic[self.customType.CURRENT_PRICE]
        last_day_highest_price = last_day_tic[self.customType.HIGHEST_PRICE]

        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
        if current_price > buy_price:
            if 1 < profit_rate and today_tic["ma20"] > current_price:
                self.logging.logger.info("stop_big_loss ma7 check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, today_tic["ma20"]))
                return copy.deepcopy(today_tic)
            else:
                last_day_price_profit_rate = round((last_day_highest_price - buy_price) / buy_price * 100, 2)
                if last_day_highest_price > current_price:

                    if 1 < profit_rate < (last_day_price_profit_rate - big_loss_rate) and today_tic["ma5"] > current_price:
                        self.logging.logger.info(
                            "stop_big_loss rate check > [%s] >> %s / %s / %s / %s / %s " % (code, current_price, buy_price, today_tic["ma5"], last_day_price_profit_rate, profit_rate))
                        return copy.deepcopy(today_tic)

        return {}

    def get_stop_loss_sell_point(self, code, target_dict, stop_rate):

        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        buy_after_rows = [x for x in rows if x[self.customType.DATE] > target_dict[code][self.customType.DATE]]
        if len(buy_after_rows) < 1:
            return {}

        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]

        current_price = today_tic[self.customType.CURRENT_PRICE]

        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]
        profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
        highest_list = [item[self.customType.HIGHEST_PRICE] for item in buy_after_rows]
        max_highest_price = max(highest_list)
        highest_profit_rate = round((max_highest_price - buy_price) / buy_price * 100, 2)

        if current_price > buy_price:
            if highest_profit_rate >= stop_rate and highest_profit_rate > profit_rate and profit_rate <= stop_rate + 0.1 and today_tic["ma5"] > current_price:
                self.logging.logger.info("stop_loss_profit check > [%s] >> %s / %s / %s / %s / %s " % (code, current_price, buy_price, today_tic["ma5"], highest_profit_rate, profit_rate))
                return copy.deepcopy(today_tic)
        return {}

    def get_add_buy_case(self, code):

        rows = self.current_hold_etf_stock_dict[code]["row"]
        buy_point = self.get_conform_default_stock_buy_case(code, rows)

        if bool(buy_point):
            self.logging.logger.info("default_stock_candle_analysis buy_point break >> %s" % code)
            limit_price = buy_point[self.customType.CURRENT_PRICE] - 10
            self.total_inverse_amount = self.total_inverse_amount + limit_price
            self.send_order_limit_stock_price(code, 1, limit_price)

    def get_max_loss_sell_case(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        first_tic = analysis_rows[0]
        current_price = first_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]

        if current_price < buy_price:
            profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
            if profit_rate <= -8:
                self.logging.logger.info("max_loss check > [%s] >> %s / %s / %s" % (code, current_price, buy_price, profit_rate))
                return copy.deepcopy(first_tic)
        return {}

    def get_under_ma20_line(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 2:
            return {}
        analysis_rows = rows[:2]
        today_tic = analysis_rows[0]
        last_day_tic = analysis_rows[1]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]

        if last_day_tic[self.customType.CURRENT_PRICE] > last_day_tic["ma20"]:
            return {}

        if current_price < buy_price and current_price < today_tic["ma20"] and current_price < today_tic["ma5"]:
            self.logging.logger.info("loss and under_ma20_line check > [%s] >> %s / %s " % (code, current_price, buy_price))
            return copy.deepcopy(today_tic)
        return {}

    def get_default_stock_under_ma3_line(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 3:
            return {}
        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]

        if buy_price < current_price < today_tic["ma3"]:
            self.logging.logger.info("maintain_under_ma5_line check > [%s] >> %s / %s " % (code, current_price, buy_price))
            return copy.deepcopy(today_tic)

        return {}

    def get_maintain_under_ma5_line(self, code, target_dict):
        rows = target_dict[code]["row"]
        if len(rows) < 3:
            return {}
        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        last_day_tic = analysis_rows[1]
        a_couple_of_days_ago_tic = analysis_rows[2]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        buy_price = target_dict[code][self.customType.PURCHASE_PRICE]

        if buy_price > current_price > today_tic["ma20"]:
            if a_couple_of_days_ago_tic[self.customType.CURRENT_PRICE] > a_couple_of_days_ago_tic["ma5"]:
                if last_day_tic[self.customType.CURRENT_PRICE] < last_day_tic["ma5"] and today_tic[self.customType.CURRENT_PRICE] < today_tic["ma5"]:
                    self.logging.logger.info("maintain_under_ma5_line check > [%s] >> %s / %s " % (code, current_price, buy_price))
                    return copy.deepcopy(today_tic)
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

    def loop_other_target_buy_etf_stock(self):
        self.analysis_search_timer1.start(1000 * 60)
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '100100') <= currentDate <= (self.today + '100500'):
            pass
        elif (self.today + '110100') <= currentDate <= (self.today + '110500'):
            pass
        elif (self.today + '120100') <= currentDate <= (self.today + '120500'):
            pass
        else:
            return
        self.logging.logger.info("analysis target etf")
        self.analysis_search_timer1.stop()
        self.goal_buy_search_stock_code = ''
        self.analysis_goal_etf_stock_list = []
        self.search_stock_code = []

        for key in self.target_etf_stock_dict.keys():
            if key not in self.default_stock_list:
                self.analysis_goal_etf_stock_list.append(copy.deepcopy(self.target_etf_stock_dict[key]))

        self.analysis_search_timer2 = default_q_timer_setting(5)
        self.analysis_search_timer2.timeout.connect(self.other_target_candle_analysis_check)

    def other_target_candle_analysis_check(self):
        if self.current_hold_stock_count == self.max_hold_stock_count:
            self.logging.logger.info("max buy stock")
            self.analysis_search_timer2.stop()
            self.analysis_search_timer1.start(1000 * 300)
            self.default_stock_candle_analysis_check()
            return

        # self.logging.logger.info("self.analysis_goal_etf_stock_list>> %s" % self.analysis_goal_etf_stock_list)
        if len(self.analysis_goal_etf_stock_list) == 0:
            self.logging.logger.info("other_target_candle_analysis nothing")
            self.analysis_search_timer2.stop()
            self.analysis_search_timer1.start(1000 * 300)
            self.default_stock_candle_analysis_check()
            return

        self.get_next_search_etf_stock_code(len(self.analysis_goal_etf_stock_list))

        code = self.goal_buy_search_stock_code
        self.logging.logger.info("other_target_candle_analysis_check loop [%s]> %s " % (code, self.target_etf_stock_dict[code]))
        self.search_stock_code.append(code)

        self.get_opt10081_info_all(code)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        rows = self.target_etf_stock_dict[code]["row"]

        if code not in self.current_hold_etf_stock_dict.keys():

            buy_point = self.get_conform_buy_case(code, rows)

            if bool(buy_point):
                if self.current_hold_stock_count < self.max_hold_stock_count and code not in self.today_buy_etf_stock_dict.keys():
                    limit_price = buy_point[self.customType.CURRENT_PRICE] - 10
                    quantity = math.trunc((self.max_buy_amount_by_stock / limit_price) / 2)
                    if quantity >= 1:
                        self.logging.logger.info("conform_buy_case buy_point break >> %s" % code)
                        self.current_hold_stock_count = self.current_hold_stock_count + 1
                        self.send_order_limit_stock_price(code, quantity, limit_price)

        if len(self.search_stock_code) == len(self.analysis_goal_etf_stock_list):
            self.logging.logger.info("other_target_candle_analysis_check end")
            self.analysis_search_timer2.stop()
            self.analysis_search_timer1.start(1000 * 300)
            self.default_stock_candle_analysis_check()
            return

    def default_stock_candle_analysis_check(self):

        for code in self.default_stock_list:
            self.get_opt10081_info_all(code)
            create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma3", 3)

            rows = self.target_etf_stock_dict[code]["row"]
            buy_point = self.get_conform_default_stock_buy_case(code, rows)

            if bool(buy_point):
                self.logging.logger.info("default_stock_candle_analysis buy_point break >> %s" % code)
                limit_price = buy_point[self.customType.CURRENT_PRICE] - 10
                self.total_inverse_amount = self.total_inverse_amount + limit_price
                self.send_order_limit_stock_price(code, 1, limit_price)
            reset()
        self.current_hold_stock_real_reg()

    def get_conform_add_stock_buy_case(self, code, target_dict):
        rows = target_dict[code]["row"]

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]
        total_chegual_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_AMOUNT]

        if purchase_price < current_price:
            self.logging.logger.info("purchase_price check> [%s] purchase_price:[%s] current_price:[%s]" % (code, purchase_price, current_price))
            return {}

        today_ma3 = today_tic["ma3"]
        if today_ma3 > current_price:
            self.logging.logger.info("ma3_position check> [%s] today_ma3:[%s] current_price:[%s]" % (code, today_ma3, current_price))
            return {}

        if code in self.current_hold_etf_stock_dict.keys():

            if self.max_invest_amount < self.total_invest_amount + current_price and (self.max_buy_amount_by_stock * 2) < total_chegual_price + current_price:
                self.logging.logger.info(
                    "max_buy_amount check> [%s] total_chegual_price:[%s] current_price:[%s] total_chegual_price:[%s]" % (code, self.total_invest_amount, current_price, total_chegual_price))
                return {}

        return copy.deepcopy(today_tic)

    def get_conform_default_stock_buy_case(self, code, rows):
        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]
        total_chegual_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_AMOUNT]

        if purchase_price < current_price:
            self.logging.logger.info("purchase_price check> [%s] purchase_price:[%s] current_price:[%s]" % (code, purchase_price, current_price))
            return {}

        today_ma3 = today_tic["ma3"]
        if today_ma3 > current_price:
            self.logging.logger.info("ma3_position check> [%s] today_ma3:[%s] current_price:[%s]" % (code, today_ma3, current_price))
            return {}

        if code in self.current_hold_etf_stock_dict.keys():
            if (self.max_buy_amount_by_stock * 2) < total_chegual_price + current_price:
                self.logging.logger.info("max_buy_amount check> [%s] total_chegual_price:[%s] current_price:[%s]" % (code, total_chegual_price, current_price))
                return {}

        return copy.deepcopy(today_tic)

    def get_default_price_info(self):
        self.read_target_etf_file()
        QTest.qWait(5000)
        self.read_hold_etf_file()

        self.get_all_etf_info()
        QTest.qWait(5000)

    def get_search_goal_price_etf(self):
        self.get_default_price_info()
        self.screen_number_setting(self.target_etf_stock_dict)

    def comm_real_data(self, sCode, sRealType, sRealData):
        b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
        b = abs(int(b.strip()))
        a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.TIGHTENING_TIME])  # 151524

        g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.VOLUME])
        g = abs(int(g.strip()))

        i = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.HIGHEST_PRICE])
        i = abs(int(i.strip()))

        j = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.START_PRICE])
        j = abs(int(j.strip()))

        k = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.LOWEST_PRICE])
        k = abs(int(k.strip()))

        if sCode not in self.total_cal_target_etf_stock_dict.keys():
            self.total_cal_target_etf_stock_dict.update({sCode: {}})

        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.TIGHTENING_TIME: a})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE: b})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.VOLUME: g})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.HIGHEST_PRICE: i})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.START_PRICE: j})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.LOWEST_PRICE: k})

        current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        if self.customType.SELL_STD_HIGHEST_PRICE in self.total_cal_target_etf_stock_dict:
            if current_stock_price > self.total_cal_target_etf_stock_dict[self.customType.SELL_STD_HIGHEST_PRICE]:
                self.logging.logger.info("changed sell std highest price >> %s" % current_stock_price)
                self.total_cal_target_etf_stock_dict.update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
        else:
            self.total_cal_target_etf_stock_dict.update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)
                self.analysis_search_timer1.stop()
        elif sRealType == self.customType.STOCK_CONCLUSION:
            if sCode in self.current_hold_etf_stock_dict.keys():
                self.comm_real_data(sCode, sRealType, sRealData)

                realdata_stock = self.total_cal_target_etf_stock_dict[sCode]
                realdata_std_higest_price = self.total_cal_target_etf_stock_dict[self.customType.SELL_STD_HIGHEST_PRICE]
                current_price = realdata_stock[self.customType.CURRENT_PRICE]
                current_hold_stock = self.current_hold_etf_stock_dict[sCode]
                buy_price = current_hold_stock[self.customType.PURCHASE_PRICE]
                profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
                self.logging.logger.info("REALTIME STOCK_CONCLUSION >>> [%s] current_price:[%s] buy_price:[%s] profit_rate:[%s]" % (sCode, current_price, buy_price, profit_rate))
                if current_price > buy_price:

                    self.logging.logger.info("realtime_stop_loss_sell check >>> [%s] current_price:[%s] buy_price:[%s] profit_rate:[%s]" % (sCode, current_price, buy_price, profit_rate))
                    rows = current_hold_stock["row"]
                    buy_after_rows = [x for x in rows if x[self.customType.DATE] > current_hold_stock[self.customType.DATE]]
                    if len(buy_after_rows) > 0:
                        highest_list = [item[self.customType.HIGHEST_PRICE] for item in buy_after_rows]
                        max_highest_price = max(highest_list)
                        if max_highest_price > realdata_std_higest_price:
                            highest_profit_rate = round((max_highest_price - buy_price) / buy_price * 100, 2)
                        else:
                            highest_profit_rate = round((realdata_std_higest_price - buy_price) / buy_price * 100, 2)
                    else:
                        highest_profit_rate = round((realdata_std_higest_price - buy_price) / buy_price * 100, 2)

                    if profit_rate > 15.0:
                        self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 7.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 5.55:
                        self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 5.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 3.55:
                        self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 3.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 2.55:
                        self.logging.logger.info("goni_max_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 2.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 2.05:
                        self.logging.logger.info("goni_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 2.0 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 1.55:
                        self.logging.logger.info("goni_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 1.5 <= highest_profit_rate and highest_profit_rate > profit_rate and profit_rate <= 1.05:
                        self.logging.logger.info("goni_stop_loss_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

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

    def get_conform_buy_case(self, code, rows):

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]

        first_tic = analysis_rows[0]
        second_tic = analysis_rows[1]
        ma_field_list = ["ma20", "ma5"]

        empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
        if len(empty_gap_list) > 0:
            return {}

        self.logging.logger.info("conform_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        if first_tic["ma5"] >= first_tic["ma20"]:
            pass
        else:
            self.logging.logger.info("is regular arrangement check> [%s] >> %s " % (code, first_tic["일자"]))
            return {}

        for field in ma_field_list:
            if first_tic[field] >= first_tic[self.customType.START_PRICE]:
                self.logging.logger.info("first_tic START_PRICE check > [%s] >> %s " % (code, first_tic))
                return {}

        if second_tic[self.customType.CURRENT_PRICE] > first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic))
            return {}

        if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic white candle check > [%s] >> %s " % (code, first_tic))
            return {}

        ma5_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma5"]) / first_tic["ma5"] * 100
        if ma5_percent > 0.7:
            self.logging.logger.info("ma5_percent check> [%s]" % code)
            return {}

        ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        if ma20_percent > 1.5:
            self.logging.logger.info("ma20_percent check> [%s]" % code)
            return {}

        return copy.deepcopy(first_tic)

    def get_conform_hold_stock_add_buy_case(self, code, rows):
        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]

        first_tic = analysis_rows[0]
        second_tic = analysis_rows[1]
        ma_field_list = ["ma20"]

        purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]
        if purchase_price > first_tic[self.customType.CURRENT_PRICE]:

            empty_gap_list = [x for x in analysis_rows for field in ma_field_list if x[field] == '']
            if len(empty_gap_list) > 0:
                return {}

            self.logging.logger.info("conform_hold_stock_add_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

            for field in ma_field_list:
                if first_tic[field] >= first_tic[self.customType.START_PRICE]:
                    self.logging.logger.info("first_tic START_PRICE check > [%s] >> %s " % (code, first_tic))
                    return {}

            if second_tic[self.customType.CURRENT_PRICE] > first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic))
                return {}

            if first_tic[self.customType.START_PRICE] >= first_tic[self.customType.CURRENT_PRICE]:
                self.logging.logger.info("first_tic white candle check > [%s] >> %s " % (code, first_tic))
                return {}

            return copy.deepcopy(first_tic)
        return {}

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

    def get_sell_opt10081_info(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MODIFIED_SHARE_PRICE, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_sell_opt10081", "opt10081", 0, self.screen_sell_opt10081_info)
        self.tr_sell_opt10081_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0"):
        self.logging.logger.info("not_concluded_account")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_etf_stock)

        self.not_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081":
            self.trdata_slot_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10081_all":
            self.trdata_slot_opt10081_all(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPW00018:
            self.trdata_slot_opw00018(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_sell_opt10081":
            self.trdata_slot_sell_opt10081(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "실시간미체결요청":
            self.trdata_slot_opt10075(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

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
                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    [self.customType.BUY_CANCLE, self.buy_screen_real_stock, self.account_num, 3, code, 0, 0,
                     self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], order_no]
                )

                if order_success == 0:
                    self.logging.logger.debug(self.logType.CANCLE_ORDER_BUY_SUCCESS_LOG)
                    self.current_hold_stock_count = self.current_hold_stock_count - 1
                else:
                    self.logging.logger.debug(self.logType.CANCLE_ORDER_BUY_FAIL_LOG)

        self.not_account_info_event_loop.exit()

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
            c = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.DATE)
            c = c.strip()
            d = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HIGHEST_PRICE)
            d = abs(int(d.strip()))
            e = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LOWEST_PRICE)
            e = abs(int(e.strip()))

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, self.customType.DATE: c, self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, "ma20": '', "ma5": ''}
            new_rows.append(row)

        self.current_hold_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_sell_opt10081_info)
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

            stock_quantity = int(stock_quantity.strip())
            buy_price = int(buy_price.strip())
            learn_rate = float(learn_rate.strip())
            current_price = int(current_price.strip())
            total_chegual_price = int(total_chegual_price.strip())
            possible_quantity = int(possible_quantity.strip())

            if code not in self.current_hold_etf_stock_dict.keys():
                self.current_hold_etf_stock_dict[code] = {}

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

                if code not in self.default_stock_list:
                    self.total_invest_amount = self.total_invest_amount + total_chegual_price
                else:
                    self.total_inverse_amount = self.total_inverse_amount + total_chegual_price

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, "ma20": '', "ma5": ''}
            new_rows.append(row)

        self.analysis_goal_etf_stock_dict[stock_code].update({"row": new_rows})

        self.stop_screen_cancel(self.screen_etf_stock)
        self.tr_opt10081_info_event_loop.exit()

    def trdata_slot_opt10081_all(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        stock_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        stock_code = stock_code.strip()

        new_rows = []
        cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

        if stock_code not in self.target_etf_stock_dict:
            self.target_etf_stock_dict.update({stock_code: {}})

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

            row = {self.customType.CURRENT_PRICE: a, self.customType.START_PRICE: b, "일자": c, self.customType.HIGHEST_PRICE: d, self.customType.LOWEST_PRICE: e, "ma20": '', "ma5": '', "ma3": {}}
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
                    self.target_etf_stock_dict.update({stock_code: {self.customType.STOCK_CODE: stock_code,
                                                                    self.customType.STOCK_NAME: stock_name,
                                                                    self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                    self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                    self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                    self.customType.GOAL_PRICE: '',
                                                                    "stat": '',
                                                                    "row": []}})
            f.close()

    def read_hold_etf_file(self):
        self.logging.logger.info("read_hold_etf_file")
        if os.path.exists(self.hold_etf_file_path):
            f = open(self.hold_etf_file_path, "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")

                    stock_code = ls[0]
                    purchase_date = ls[1].rstrip('\n')
                    if stock_code in self.current_hold_etf_stock_dict.keys():
                        self.current_hold_etf_stock_dict[stock_code].update({self.customType.DATE: purchase_date.strip()})
            f.close()

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

    def sell_send_order_market_off_price(self, sCode, quantity):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, self.buy_screen_real_stock, self.account_num, 2, sCode, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_OFF_TIME_LAST_PRICE], ""])
        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_SELL_SUCCESS_LOG % sCode)
        else:
            self.logging.logger.info(self.logType.ORDER_SELL_FAIL_LOG % sCode)

        return order_success

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

    def sell_send_order_favorable_limit_price(self, sCode, screen_number, quantity):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, screen_number, self.account_num, 2, sCode, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.FAVORABLE_LIMIT_PRICE],
             ""]
        )
        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_SELL_SUCCESS_LOG % sCode)
        else:
            self.logging.logger.info(self.logType.ORDER_SELL_FAIL_LOG % sCode)

        return order_success

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

            account_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.ACCOUNT_NUMBER])
            if account_number == self.account_num:

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

                if meme_gubun == self.customType.SELL and sCode in self.current_hold_etf_stock_dict.keys():
                    del self.current_hold_etf_stock_dict[sCode]
                else:
                    if sCode not in self.default_stock_list:

                        if sCode not in self.today_buy_etf_stock_dict.keys() and sCode not in self.current_hold_etf_stock_dict.keys() and sCode not in self.default_stock_list:
                            self.today_buy_etf_stock_dict.update({sCode: {self.customType.PURCHASE_PRICE: buy_price,
                                                                          self.customType.TIGHTENING_TIME: get_today_by_format('%Y%m%d%H%M%S'),
                                                                          self.customType.TOTAL_PURCHASE_PRICE: total_buy_price}})
                    if sCode in self.current_hold_etf_stock_dict.keys():
                        self.current_hold_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price,
                                                                        self.customType.HOLDING_QUANTITY: holding_quantity,
                                                                        self.customType.PURCHASE_AMOUNT: total_buy_price})

    def call_exit(self):
        sys.exit()

    def loop_system_off(self):
        self.system_off_check_timer = default_q_timer_setting(60)
        self.system_off_check_timer.timeout.connect(self.check_system_off_time)

    def check_system_off_time(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '160000') < currentDate:
            self.file_delete()
            self.create_current_hold_etf_stock_info()
            self.system_off_check_timer.stop()
            self.system_off_check_timer = default_q_timer_setting(300)
            self.logging.logger.info("시스템 종료")
            self.system_off_check_timer.timeout.connect(self.call_exit)

    def file_delete(self):
        self.logging.logger.info("file_delete")
        if os.path.isfile(self.hold_etf_file_path):
            os.remove(self.hold_etf_file_path)
            self.logging.logger.info("remove %s" % self.hold_etf_file_path)

    def create_current_hold_etf_stock_info(self):
        self.logging.logger.info("create_current_hold_etf_stock_info")

        for code in self.current_hold_etf_stock_dict.keys():
            value = self.current_hold_etf_stock_dict[code]
            if self.customType.DATE in value.keys():
                purchase_date = value[self.customType.DATE]
            else:
                purchase_date = self.today

            f = open(self.hold_etf_file_path, "a", encoding="utf8")
            f.write("%s\t%s\n" %
                    (code, purchase_date))
            f.close()

        for code in self.today_buy_etf_stock_dict.keys():
            f = open(self.hold_etf_file_path, "a", encoding="utf8")
            f.write("%s\t%s\n" %
                    (code, self.today))
            f.close()

    def get_next_search_etf_stock_code(self, max_index=4):
        if self.goal_buy_search_stock_code == '':
            item = self.analysis_goal_etf_stock_list[0]
        else:
            index = next((index for (index, d) in enumerate(self.analysis_goal_etf_stock_list) if d[self.customType.STOCK_CODE] == self.goal_buy_search_stock_code), None)
            if index < 0 or index > max_index:
                self.logging.logger.info("not found next stock code > index:[%s] " % index)

            if index == len(self.analysis_goal_etf_stock_list) - 1:
                index = -1
            self.logging.logger.info("get_next_search_etf_stock_code index >> %s" % index)
            item = self.analysis_goal_etf_stock_list[index + 1]

        self.logging.logger.info("get_next_search_etf_stock_code item >> %s" % item)
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
