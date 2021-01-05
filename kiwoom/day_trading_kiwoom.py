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

        # 1차(2020-06~2020-12) : 300,000 + 150,000 = 450,000
        # 2차(2021-01~       ) : 8,000,000 + 1,000,000 = 9,000,000
        self.max_hold_stock_count = 0
        self.max_buy_amount_by_stock = 600000  # 50,000 -> 600,000
        self.max_buy_amount_by_one_point = 100000
        self.max_buy_total_amount = 1000000  # 한 종목당 최대 1,000,000원
        self.max_buy_total_amount_by_index = 1000000  # 150,000 -> 1,000,000
        self.max_buy_day_amount_by_index = 50000
        self.add_buy_max_amount_by_day = 50000
        self.default_buy_stock_count = 8
        self.max_buy_stock_count = 9  # 3 -> 9
        self.max_invest_amount = self.max_buy_total_amount * self.default_buy_stock_count
        self.total_invest_amount = 0
        self.total_inverse_amount = 0

        self.buy_inverse_flag = False

        self.analysis_search_timer1 = QTimer()
        self.analysis_search_timer2 = QTimer()
        self.system_off_check_timer = QTimer()
        self.hold_stock_check_timer = QTimer()
        self.cancle_check_timer = QTimer()

        self.analysis_goni_timer1 = QTimer()
        self.analysis_goni_timer2 = QTimer()

        self.default_analysis_search_timer1 = QTimer()
        self.default_analysis_search_timer2 = QTimer()

        self.current_hold_stock_count = 0

        self.current_hold_etf_stock_dict = {}

        self.total_cal_target_etf_stock_dict = {}
        self.today_buy_etf_stock_dict = {}
        self.today_order_etf_stock_list = []
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
        self.loop_default_analysis_buy_etf()
        self.loop_system_off()
        self.loop_add_buy_hold_etf_stock()
        self.loop_goni_hold_etf_stock()

        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

    def current_hold_stock_real_reg(self):
        for code in self.current_hold_etf_stock_dict.keys():
            screen_num = self.current_hold_etf_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.logging.logger.info("current_hold_stock_real_reg >> %s %s" % (code, screen_num))
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def today_buy_stock_real_reg(self, code):
        screen_num = int(self.buy_screen_real_stock) + 1
        fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
        self.logging.logger.info("today_buy_stock_real_reg >> %s %s" % (code, screen_num))
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def init_stock_values(self):
        # self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_AMOUNT]
        # self.current_hold_etf_stock_dict[code].update({self.customType.STOCK_CODE: code})
        if self.buy_possible_deposit < self.max_buy_total_amount and self.current_hold_stock_count >= self.default_buy_stock_count:
            self.max_hold_stock_count = self.current_hold_stock_count
            self.screen_number_setting(self.current_hold_etf_stock_dict)
            return

        if (self.max_invest_amount - self.max_buy_amount_by_stock) <= self.total_invest_amount:
            self.max_hold_stock_count = self.current_hold_stock_count
            self.screen_number_setting(self.current_hold_etf_stock_dict)
            return

        filtered_current_hold_etf_stock = [x for x in self.current_hold_etf_stock_dict.keys() if x not in self.default_stock_list]
        self.current_hold_stock_count = len(filtered_current_hold_etf_stock)
        if self.current_hold_stock_count >= self.max_buy_stock_count:
            self.max_hold_stock_count = self.current_hold_stock_count
            self.screen_number_setting(self.current_hold_etf_stock_dict)
            return

        able_addbuy_stock_count = int((self.max_invest_amount - self.total_invest_amount) / self.max_buy_total_amount)
        if able_addbuy_stock_count > 0:
            if self.max_buy_stock_count >= self.current_hold_stock_count + able_addbuy_stock_count:
                self.max_hold_stock_count = self.current_hold_stock_count + able_addbuy_stock_count
            else:
                self.max_hold_stock_count = self.max_buy_stock_count
        else:
            self.max_hold_stock_count = self.current_hold_stock_count

        self.screen_number_setting(self.current_hold_etf_stock_dict)

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

    def realtime_stop_loss_limit_price_sell(self, code, limit_price):
        quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
        self.logging.logger.info("realtime_stop_loss_sell_point break >> %s" % code)
        self.sell_send_order_limit_price(code, self.sell_screen_meme_stock, quantity, limit_price)
        self.sell_receive_stock_code.append(code)

    def realtime_stop_loss_half_sell(self, code, limit_price):
        quantity = self.current_hold_etf_stock_dict[code][self.customType.HOLDING_QUANTITY]
        sell_quantity = math.trunc(quantity / 2) if quantity >= 2 else 0
        if sell_quantity > 0:
            self.logging.logger.info("realtime_stop_loss_half_sell_point break >> %s" % code)
            self.sell_send_order_limit_price(code, self.sell_screen_meme_stock, sell_quantity, limit_price)
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

        if len(self.sell_search_stock_code_list) == len(self.analysis_sell_etf_stock_list):
            self.logging.logger.info("daily_candle_goni_point_check end")
            self.analysis_goni_timer2.stop()
            self.current_hold_stock_real_reg()

    def loop_add_buy_hold_etf_stock(self):
        self.hold_stock_check_timer = default_q_timer_setting(120)
        self.hold_stock_check_timer.timeout.connect(self.analysis_hold_etf_stock)

    def analysis_hold_etf_stock(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '143000') <= currentDate <= (self.today + '143500'):
            pass
        else:
            return
        self.hold_stock_check_timer.stop()
        self.logging.logger.info('loop_add_buy_hold_etf_stock')
        self.sell_search_stock_code_list = []
        self.sell_search_stock_code = ''
        self.analysis_sell_etf_stock_list = []
        for key in self.current_hold_etf_stock_dict.keys():
            self.analysis_sell_etf_stock_list.append(copy.deepcopy(self.current_hold_etf_stock_dict[key]))

        self.hold_stock_check_timer = default_q_timer_setting(4)
        self.hold_stock_check_timer.timeout.connect(self.daily_candle_add_buy_point_check)

    def daily_candle_add_buy_point_check(self):
        if len(self.analysis_sell_etf_stock_list) == 0:
            self.logging.logger.info("analysis_add_buy_etf_stock_list nothing")
            self.hold_stock_check_timer.stop()
            return

        if self.buy_possible_deposit < self.total_invest_amount + self.max_buy_amount_by_stock:
            self.logging.logger.info("add_buy_etf_stock surplus funds to lack")
            self.hold_stock_check_timer.stop()
            return

        self.get_sell_next_search_etf_stock_code(len(self.analysis_sell_etf_stock_list))

        code = self.sell_search_stock_code
        self.logging.logger.info("analysis_add_buy_etf_stock_list loop > %s " % code)
        self.sell_search_stock_code_list.append(code)

        self.get_sell_opt10081_info(code)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma3", 3)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        create_moving_average_gap_line(code, self.current_hold_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)

        if code not in self.default_stock_list:
            add_buy_point = self.get_conform_add_default_amount_buy_case(code, self.current_hold_etf_stock_dict)
            if bool(add_buy_point):
                max_buy_count = math.trunc(self.max_buy_amount_by_one_point / add_buy_point[self.customType.CURRENT_PRICE])
                first_limit_price = add_buy_point[self.customType.CURRENT_PRICE] - 10

                if max_buy_count >= 2:
                    self.send_order_limit_stock_price(code, max_buy_count, first_limit_price)
            else:
                add_buy_point = self.get_conform_add_stock_buy_case(code, self.current_hold_etf_stock_dict)
                if bool(add_buy_point):
                    total_chegual_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_AMOUNT]
                    self.logging.logger.info("conform_add_stock_buy_case buy_point break >> %s" % code)
                    if self.max_buy_total_amount >= total_chegual_price + self.add_buy_max_amount_by_day:
                        max_buy_count = math.trunc(self.add_buy_max_amount_by_day / add_buy_point[self.customType.CURRENT_PRICE])
                    else:
                        available_amount = self.max_buy_total_amount - total_chegual_price
                        max_buy_count = math.trunc(available_amount / add_buy_point[self.customType.CURRENT_PRICE]) if available_amount >= add_buy_point[self.customType.CURRENT_PRICE] else 0

                    first_limit_price = add_buy_point[self.customType.CURRENT_PRICE] - 10
                    second_limit_price = add_buy_point[self.customType.CURRENT_PRICE] - 15

                    if max_buy_count >= 2:
                        buy_count = math.ceil(max_buy_count / 2)
                        self.send_order_limit_stock_price(code, (max_buy_count - buy_count), second_limit_price)
                        self.send_order_limit_stock_price(code, buy_count, first_limit_price)

        if len(self.sell_search_stock_code_list) == len(self.analysis_sell_etf_stock_list):
            self.logging.logger.info("daily_candle_add_buy_point_check end")
            self.hold_stock_check_timer.stop()

    def loop_default_analysis_buy_etf(self):
        self.default_analysis_search_timer1 = default_q_timer_setting(60)
        self.default_analysis_search_timer1.timeout.connect(self.loop_default_target_buy_etf_stock)

    def loop_default_target_buy_etf_stock(self):
        self.default_analysis_search_timer1.start(1000 * 60)
        if self.buy_inverse_flag is True:
            return
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '110500') <= currentDate <= (self.today + '110900'):
            pass
        else:
            return
        self.logging.logger.info("default analysis target etf")
        self.default_analysis_search_timer1.stop()

        self.default_analysis_search_timer2 = default_q_timer_setting(5)
        self.default_analysis_search_timer2.timeout.connect(self.default_stock_candle_analysis_check)

    def loop_analysis_buy_etf(self):
        self.analysis_search_timer1 = default_q_timer_setting(60)
        self.analysis_search_timer1.timeout.connect(self.loop_other_target_buy_etf_stock)

    def loop_other_target_buy_etf_stock(self):
        self.analysis_search_timer1.start(1000 * 60)
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '100100') <= currentDate <= (self.today + '100500'):
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

        if len(self.analysis_goal_etf_stock_list) == 0:
            self.logging.logger.info("no analysis_goal_etf_stock_list")
            self.analysis_search_timer2.stop()
            return

        self.get_next_search_etf_stock_code(len(self.analysis_goal_etf_stock_list))

        code = self.goal_buy_search_stock_code
        self.logging.logger.info("other_target_candle_analysis_check loop [%s]> %s " % (code, self.target_etf_stock_dict[code]))

        if self.current_hold_stock_count == self.max_hold_stock_count:
            self.logging.logger.info("max buy stock")
            self.analysis_search_timer2.stop()
            return

        self.search_stock_code.append(code)

        self.get_opt10081_info_all(code)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        rows = self.target_etf_stock_dict[code]["row"]

        if code not in self.today_order_etf_stock_list:
            buy_point = self.get_conform_buy_case(code, rows)
            if code not in self.current_hold_etf_stock_dict.keys():
                if bool(buy_point):
                    if self.current_hold_stock_count < self.max_hold_stock_count and code not in self.today_buy_etf_stock_dict.keys():
                        std_limit_price = buy_point[self.customType.CURRENT_PRICE]
                        max_quantity = math.trunc((self.max_buy_amount_by_stock / std_limit_price))
                        min_one_quantity = math.trunc((self.max_buy_amount_by_one_point / std_limit_price))

                        if min_one_quantity >= 1:
                            self.logging.logger.info("conform_buy_case buy_point(- 25) break >> %s" % code)
                            limit_price = std_limit_price - 25
                            self.send_order_limit_stock_price(code, min_one_quantity, limit_price)
                            max_quantity = max_quantity - min_one_quantity

                            self.logging.logger.info("conform_buy_case buy_point(- 20) break >> %s" % code)
                            limit_price = std_limit_price - 20
                            self.send_order_limit_stock_price(code, min_one_quantity, limit_price)
                            max_quantity = max_quantity - min_one_quantity

                            self.logging.logger.info("conform_buy_case buy_point(- 15) break >> %s" % code)
                            limit_price = std_limit_price - 15
                            self.send_order_limit_stock_price(code, min_one_quantity, limit_price)
                            max_quantity = max_quantity - min_one_quantity

                            self.logging.logger.info("conform_buy_case buy_point(- 10) break >> %s" % code)
                            self.today_order_etf_stock_list.append(code)
                            self.current_hold_stock_count = self.current_hold_stock_count + 1
                            limit_price = std_limit_price - 10
                            self.send_order_limit_stock_price(code, max_quantity, limit_price)

                            self.logging.logger.info("conform_buy_case buy_point(- 40) break >> %s" % code)
                            limit_price = std_limit_price - 40
                            self.send_order_limit_stock_price(code, min_one_quantity, limit_price)

            else:
                if bool(buy_point):
                    stock_info = self.current_hold_etf_stock_dict[code]
                    purchase_price = stock_info[self.customType.PURCHASE_PRICE]
                    if stock_info[self.customType.PURCHASE_AMOUNT] < self.max_buy_amount_by_stock:
                        limit_purchase_amount = self.max_buy_amount_by_stock - stock_info[self.customType.PURCHASE_AMOUNT]
                    else:
                        limit_purchase_amount = self.add_buy_max_amount_by_day

                    if limit_purchase_amount > 0 and purchase_price > buy_point[self.customType.CURRENT_PRICE]:

                        limit_price = buy_point[self.customType.CURRENT_PRICE] - 10
                        max_quantity = math.trunc(limit_purchase_amount / limit_price)
                        if max_quantity >= 1:
                            quantity = math.trunc(max_quantity/2)
                            self.logging.logger.info("current_hold_etf_stock_dict conform_buy_case buy_point(- 10) break >> %s" % code)
                            self.today_order_etf_stock_list.append(code)
                            self.send_order_limit_stock_price(code, quantity, limit_price)

                            limit_price = buy_point[self.customType.CURRENT_PRICE] - 15
                            self.logging.logger.info("current_hold_etf_stock_dict conform_buy_case buy_point(- 15) break >> %s" % code)
                            self.today_order_etf_stock_list.append(code)
                            self.send_order_limit_stock_price(code, (max_quantity - quantity), limit_price)

        if len(self.search_stock_code) == len(self.analysis_goal_etf_stock_list):
            self.logging.logger.info("other_target_candle_analysis_check end")
            self.analysis_search_timer2.stop()
            self.analysis_search_timer1.start(1000 * 300)
            return

    def default_stock_candle_analysis_check(self):

        for code in self.default_stock_list:
            self.get_opt10081_info_all(code)
            create_moving_average_gap_line(code, self.target_etf_stock_dict, "row", self.customType.CURRENT_PRICE, "ma3", 3)

            rows = self.target_etf_stock_dict[code]["row"]
            buy_point = self.get_conform_default_stock_buy_case(code, rows)

            if code not in self.current_hold_etf_stock_dict.keys():
                total_chegual_price = 0
            else:
                total_chegual_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_AMOUNT]

            if bool(buy_point):

                if self.max_buy_total_amount_by_index >= total_chegual_price + self.max_buy_day_amount_by_index:
                    self.logging.logger.info("default_stock_candle_analysis buy_point break >> %s" % code)
                    max_buy_count = math.trunc(self.max_buy_day_amount_by_index / buy_point[self.customType.CURRENT_PRICE])
                    buy_count = math.ceil(max_buy_count / 2) if max_buy_count >= 2 else max_buy_count
                    min_limit_price = buy_point[self.customType.CURRENT_PRICE] - 20
                    if buy_count >= 1:
                        self.total_inverse_amount = self.total_inverse_amount + min_limit_price
                        self.send_order_limit_stock_price(code, buy_count, min_limit_price)
                        self.buy_inverse_flag = True

                    max_buy_count = max_buy_count - buy_count
                    buy_count = math.ceil(max_buy_count / 2) if max_buy_count >= 2 else max_buy_count
                    first_limit_price = buy_point[self.customType.CURRENT_PRICE] - 15
                    if buy_count >= 1:
                        self.total_inverse_amount = self.total_inverse_amount + first_limit_price
                        self.send_order_limit_stock_price(code, buy_count, first_limit_price)
                        self.buy_inverse_flag = True

                    max_buy_count = max_buy_count - buy_count
                    second_limit_price = buy_point[self.customType.CURRENT_PRICE] - 10
                    if max_buy_count >= 1:
                        self.total_inverse_amount = self.total_inverse_amount + second_limit_price
                        self.send_order_limit_stock_price(code, max_buy_count, second_limit_price)
            else:
                if self.weekend.isMonday:
                    buy_point = self.get_conform_default_stock_buy_min_case(code, rows)
                    if bool(buy_point):
                        if self.max_buy_total_amount_by_index >= total_chegual_price + math.trunc(self.max_buy_day_amount_by_index/2):
                            self.logging.logger.info("default_stock_candle_analysis buy_point break >> %s" % code)
                            max_buy_count = math.trunc(math.trunc(self.max_buy_day_amount_by_index/2) / buy_point[self.customType.CURRENT_PRICE])
                            buy_count = math.ceil(max_buy_count / 2) if max_buy_count >= 2 else max_buy_count
                            min_limit_price = buy_point[self.customType.CURRENT_PRICE] - 20
                            if buy_count >= 1:
                                self.total_inverse_amount = self.total_inverse_amount + min_limit_price
                                self.send_order_limit_stock_price(code, buy_count, min_limit_price)
                                self.buy_inverse_flag = True

                            max_buy_count = max_buy_count - buy_count
                            buy_count = math.ceil(max_buy_count / 2) if max_buy_count >= 2 else max_buy_count
                            first_limit_price = buy_point[self.customType.CURRENT_PRICE] - 15
                            if buy_count >= 1:
                                self.total_inverse_amount = self.total_inverse_amount + first_limit_price
                                self.send_order_limit_stock_price(code, buy_count, first_limit_price)
                                self.buy_inverse_flag = True

                            max_buy_count = max_buy_count - buy_count
                            second_limit_price = buy_point[self.customType.CURRENT_PRICE] - 10
                            if max_buy_count >= 1:
                                self.total_inverse_amount = self.total_inverse_amount + second_limit_price
                                self.send_order_limit_stock_price(code, max_buy_count, second_limit_price)

        self.default_analysis_search_timer2.stop()
        self.default_analysis_search_timer1.start(1000 * 300)

    def get_conform_add_default_amount_buy_case(self, code, target_dict):
        rows = target_dict[code]["row"]

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        yesterday_tic = analysis_rows[1]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]

        if purchase_price < current_price:
            self.logging.logger.info("purchase_price check> [%s] purchase_price:[%s] current_price:[%s]" % (code, purchase_price, current_price))
            return {}

        if yesterday_tic[self.customType.CURRENT_PRICE] > current_price:
            self.logging.logger.info("yesterday_tic price check> [%s] yesterday_price:[%s] current_price:[%s]" % (code, yesterday_tic[self.customType.CURRENT_PRICE], current_price))
            return {}

        total_chegual_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_AMOUNT]
        available_add_amount = self.max_buy_amount_by_stock - total_chegual_price
        if available_add_amount < self.max_buy_amount_by_one_point:
            self.logging.logger.info("available_add_amount check> [%s] total_chegual_price:[%s] available_add_amount:[%s]" % (code, total_chegual_price, available_add_amount))
            return {}

        return copy.deepcopy(today_tic)

    def get_conform_add_stock_buy_case(self, code, target_dict):
        rows = target_dict[code]["row"]

        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        yesterday_tic = analysis_rows[1]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        start_price = today_tic[self.customType.START_PRICE]
        purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]

        profit_rate = round((current_price - purchase_price) / purchase_price * 100, 2)

        if profit_rate >= 0.1:
            self.logging.logger.info("purchase_price check> [%s] purchase_price:[%s] current_price:[%s] profit_rate:[%s]" % (code, purchase_price, current_price, profit_rate))
            return {}

        if start_price > current_price and yesterday_tic[self.customType.CURRENT_PRICE] > current_price:
            self.logging.logger.info("start price check> [%s] purchase_price:[%s] current_price:[%s] profit_rate:[%s]" % (code, purchase_price, current_price, profit_rate))
            return {}

        today_ma3 = today_tic["ma3"]
        if today_ma3 > current_price:
            self.logging.logger.info("ma3_position check> [%s] today_ma3:[%s] current_price:[%s]" % (code, today_ma3, current_price))
            return {}

        return copy.deepcopy(today_tic)

    def get_conform_default_stock_buy_min_case(self, code, rows):
        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]

        profit_rate = round((current_price - purchase_price) / purchase_price * 100, 2)

        if profit_rate > -10.0:
            self.logging.logger.info("min profit_rate [%s] profit_rate[%s]" % (code, profit_rate))
            return {}

        if code not in self.current_hold_etf_stock_dict.keys():
            self.logging.logger.info("not incurrent_hold_etf_stock_dict ")
            return {}

        return copy.deepcopy(today_tic)

    def get_conform_default_stock_buy_case(self, code, rows):
        if len(rows) < 3:
            return {}

        analysis_rows = rows[:3]
        today_tic = analysis_rows[0]
        yesterday_tic = analysis_rows[1]
        current_price = today_tic[self.customType.CURRENT_PRICE]
        today_ma3 = today_tic["ma3"]
        if today_ma3 > current_price:
            self.logging.logger.info("ma3_position check> [%s] today_ma3:[%s] current_price:[%s]" % (code, today_ma3, current_price))
            return {}

        if code not in self.current_hold_etf_stock_dict.keys():
            if today_tic[self.customType.CURRENT_PRICE] > today_tic[self.customType.START_PRICE]:
                if yesterday_tic["ma3"] > yesterday_tic[self.customType.CURRENT_PRICE]:
                    return copy.deepcopy(today_tic)
        else:
            purchase_price = self.current_hold_etf_stock_dict[code][self.customType.PURCHASE_PRICE]

            if purchase_price < current_price:
                self.logging.logger.info("purchase_price check> [%s] purchase_price:[%s] current_price:[%s]" % (code, purchase_price, current_price))
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
        if self.customType.SELL_STD_HIGHEST_PRICE in self.total_cal_target_etf_stock_dict[sCode]:
            if current_stock_price > self.total_cal_target_etf_stock_dict[sCode][self.customType.SELL_STD_HIGHEST_PRICE]:
                self.logging.logger.info("changed sell std highest price >> [%s] %s" % (sCode, current_stock_price))
                self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
        else:
            self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})

        if self.customType.SELL_STD_LOWEST_PRICE in self.total_cal_target_etf_stock_dict[sCode]:
            if current_stock_price < self.total_cal_target_etf_stock_dict[sCode][self.customType.SELL_STD_LOWEST_PRICE]:
                self.logging.logger.info("changed sell std lowest price >> [%s] %s" % (sCode, current_stock_price))
                self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_LOWEST_PRICE: current_stock_price})
        else:
            self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_LOWEST_PRICE: current_stock_price})

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)
                self.analysis_search_timer1.stop()
        elif sRealType == self.customType.STOCK_CONCLUSION:
            if sCode in self.sell_receive_stock_code:
                return

            self.comm_real_data(sCode, sRealType, sRealData)

            realdata_stock = self.total_cal_target_etf_stock_dict[sCode]
            realdata_std_higest_price = realdata_stock[self.customType.SELL_STD_HIGHEST_PRICE]
            current_price = realdata_stock[self.customType.CURRENT_PRICE]
            start_price = realdata_stock[self.customType.START_PRICE]
            realdata_std_lowest_price = realdata_stock[self.customType.SELL_STD_LOWEST_PRICE]

            if sCode in self.current_hold_etf_stock_dict.keys():
                current_hold_stock = self.current_hold_etf_stock_dict[sCode]

            elif sCode in self.today_buy_etf_stock_dict.keys():
                current_hold_stock = self.today_buy_etf_stock_dict[sCode]

            else:
                return

            buy_price = current_hold_stock[self.customType.PURCHASE_PRICE]
            profit_rate = round((current_price - buy_price) / buy_price * 100, 2)
            total_chegual_price = current_hold_stock[self.customType.PURCHASE_AMOUNT]
            is_add_buy_posible = True if (total_chegual_price + self.add_buy_max_amount_by_day) < self.max_buy_total_amount else False

            if current_price > buy_price and profit_rate >= 1.0:
                highest_profit_rate = round((realdata_std_higest_price - buy_price) / buy_price * 100, 2)

                if "row" not in current_hold_stock:
                    return
                rows = current_hold_stock["row"]

                if len(rows) == 0:
                    return
                analysis_rows = rows[:2]

                today_tic = analysis_rows[0]
                if today_tic[self.customType.HIGHEST_PRICE] > realdata_std_higest_price:
                    realdata_std_higest_price = today_tic[self.customType.HIGHEST_PRICE]
                    highest_profit_rate = round((realdata_std_higest_price - buy_price) / buy_price * 100, 2)

                yesterday_tic = analysis_rows[1]

                self.logging.logger.info("realtime_info [%s] yesterday:[%s] current:[%s] profit_rate:[%s]" % (sCode, yesterday_tic[self.customType.CURRENT_PRICE], current_price, profit_rate))

                if yesterday_tic[self.customType.CURRENT_PRICE] > current_price:

                    if profit_rate >= 10.0:
                        self.logging.logger.info("highest_10_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        half_sell_limit_price = current_price - 20
                        self.realtime_stop_loss_limit_price_sell(sCode, half_sell_limit_price)

                    buy_after_rows = [x for x in rows if x[self.customType.DATE] > current_hold_stock[self.customType.DATE]]
                    if len(buy_after_rows) > 0:
                        highest_list = [item[self.customType.HIGHEST_PRICE] for item in buy_after_rows]
                        max_highest_price = max(highest_list)
                        # self.logging.logger.info("max price > [%s] >> %s / %s" % (sCode, max_highest_price, realdata_std_higest_price))
                        if max_highest_price > realdata_std_higest_price:
                            highest_profit_rate = round((max_highest_price - buy_price) / buy_price * 100, 2)
                        else:
                            highest_profit_rate = round((realdata_std_higest_price - buy_price) / buy_price * 100, 2)
                    else:
                        highest_profit_rate = round((realdata_std_higest_price - buy_price) / buy_price * 100, 2)

                    self.logging.logger.info("yesterday_std_info[%s] >> highest_profit_rate:%s / profit_rate:%s" % (sCode, highest_profit_rate, profit_rate))

                    if 7.5 <= highest_profit_rate and highest_profit_rate > profit_rate and 6.95 < profit_rate <= 7.05:
                        self.logging.logger.info("highest_7.5_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 5.5 <= highest_profit_rate and highest_profit_rate > profit_rate and 4.95 < profit_rate <= 5.15:
                        self.logging.logger.info("highest_5.5_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 5.0 <= highest_profit_rate and highest_profit_rate > profit_rate and 4.45 < profit_rate <= 4.65:
                        self.logging.logger.info("highest_5.0_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 4.5 <= highest_profit_rate and highest_profit_rate > profit_rate and 3.95 < profit_rate <= 4.15:
                        self.logging.logger.info("highest_4.5_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 4.0 <= highest_profit_rate and highest_profit_rate > profit_rate and 3.45 < profit_rate <= 3.65:
                        self.logging.logger.info("highest_4.0_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 3.5 <= highest_profit_rate and highest_profit_rate > profit_rate and 2.95 < profit_rate <= 3.15:
                        self.logging.logger.info("highest_3.5_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if 3.0 <= highest_profit_rate and highest_profit_rate > profit_rate and 2.45 < profit_rate <= 2.65:
                        self.logging.logger.info("highest_3.0_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        self.realtime_stop_loss_sell(sCode)

                    if is_add_buy_posible is False and start_price > current_price:

                        if 2.1 <= profit_rate <= 2.9 and current_hold_stock["half_sell"] is False:
                            self.logging.logger.info("not is_add_buy_posible flase half sell point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                            half_sell_limit_price = current_price - 20
                            self.realtime_stop_loss_half_sell(sCode, half_sell_limit_price)

                else:

                    self.logging.logger.info("realdata_std_info[%s] >> highest_profit_rate:%s / profit_rate:%s" % (sCode, highest_profit_rate, profit_rate))
                    if realdata_std_lowest_price == current_price:
                        return

                    if profit_rate > 20.0:
                        self.logging.logger.info("highest_15_profit_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        half_sell_limit_price = current_price - 20
                        self.realtime_stop_loss_limit_price_sell(sCode, half_sell_limit_price)

                    if 20.0 >= profit_rate > 11.0 and current_hold_stock["half_sell"] is False and (highest_profit_rate-0.5) > profit_rate:
                        self.logging.logger.info("profit_10_half_sell_point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                        half_sell_limit_price = current_price - 20
                        self.realtime_stop_loss_half_sell(sCode, half_sell_limit_price)

                    if highest_profit_rate >= 7.1 and highest_profit_rate > profit_rate:
                        if (highest_profit_rate - 3.3) <= profit_rate < (highest_profit_rate - 3.0):
                            self.logging.logger.info("highest_profit_sell_point(6.1) check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                            self.realtime_stop_loss_sell(sCode)

                    if 7.1 > highest_profit_rate >= 5.1 and highest_profit_rate > profit_rate:
                        if ((highest_profit_rate / 2) - 0.3) <= profit_rate < (highest_profit_rate / 2):
                            self.logging.logger.info("goni_profit_sell_point(5.1) check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                            self.realtime_stop_loss_sell(sCode)

                    if is_add_buy_posible is False and start_price > current_price:
                        if 2.0 <= profit_rate <= 3.1 and current_hold_stock["half_sell"] is False:
                            self.logging.logger.info("not is_add_buy_posible flase half sell point check > [%s] >> %s / %s / %s" % (sCode, current_price, profit_rate, highest_profit_rate))
                            half_sell_limit_price = current_price - 20
                            self.realtime_stop_loss_half_sell(sCode, half_sell_limit_price)

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

        # ma5_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma5"]) / first_tic["ma5"] * 100
        # if ma5_percent > 1.5:
        #     self.logging.logger.info("ma5_percent check> [%s][%s]" % (code, ma5_percent))
        #     return {}
        #
        # ma20_percent = (first_tic[self.customType.CURRENT_PRICE] - first_tic["ma20"]) / first_tic["ma20"] * 100
        # if ma20_percent > 3.0:
        #     self.logging.logger.info("ma20_percent check> [%s][%s]" % (code, ma20_percent))
        #     return {}

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
                self.current_hold_etf_stock_dict[code].update({"half_sell": False})

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
        # self.buy_possible_deposit = math.trunc(self.buy_possible_deposit / 2)

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
                    if len(ls) == 2:
                        stock_code = ls[0]
                        purchase_date = ls[1].rstrip('\n')
                        half_sell = False
                    else:
                        stock_code = ls[0]
                        purchase_date = ls[1]
                        half_sell = ls[2].rstrip('\n')
                    if stock_code in self.current_hold_etf_stock_dict.keys():
                        self.current_hold_etf_stock_dict[stock_code].update({self.customType.DATE: purchase_date.strip()})
                        self.current_hold_etf_stock_dict[stock_code].update({"half_sell": half_sell})
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

    def sell_send_order_limit_price(self, sCode, screen_number, quantity, limit_price):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, screen_number, self.account_num, 2, sCode, quantity, limit_price, self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS],
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
                    if holding_quantity == 0:
                        del self.current_hold_etf_stock_dict[sCode]
                    elif holding_quantity > 0:
                        if sCode in self.today_buy_etf_stock_dict.keys():
                            self.today_buy_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price,
                                                                         self.customType.HOLDING_QUANTITY: holding_quantity,
                                                                         self.customType.PURCHASE_AMOUNT: total_buy_price,
                                                                         "half_sell": True})
                        if sCode in self.current_hold_etf_stock_dict.keys():
                            self.current_hold_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price,
                                                                            self.customType.HOLDING_QUANTITY: holding_quantity,
                                                                            self.customType.PURCHASE_AMOUNT: total_buy_price,
                                                                            "half_sell": True})
                else:
                    if sCode in self.today_buy_etf_stock_dict.keys():
                        self.today_buy_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price,
                                                                     self.customType.HOLDING_QUANTITY: holding_quantity,
                                                                     self.customType.PURCHASE_AMOUNT: total_buy_price})
                        self.today_buy_etf_stock_dict[sCode].update({"half_sell": False})

                    if sCode in self.current_hold_etf_stock_dict.keys():
                        self.current_hold_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price,
                                                                        self.customType.HOLDING_QUANTITY: holding_quantity,
                                                                        self.customType.PURCHASE_AMOUNT: total_buy_price})

                        if self.current_hold_etf_stock_dict[sCode]["half_sell"] is True:
                            is_add_buy_posible = True if (total_buy_price + self.add_buy_max_amount_by_day) < self.max_buy_amount_by_stock else False
                            if is_add_buy_posible:
                                self.current_hold_etf_stock_dict[sCode].update({"half_sell": False})

                    if sCode not in self.today_buy_etf_stock_dict.keys() and sCode not in self.current_hold_etf_stock_dict.keys():
                        self.today_buy_etf_stock_dict.update({sCode: {self.customType.PURCHASE_PRICE: buy_price,
                                                                      self.customType.TIGHTENING_TIME: get_today_by_format('%Y%m%d%H%M%S'),
                                                                      self.customType.PURCHASE_AMOUNT: total_buy_price,
                                                                      "half_sell": False}})
                        self.today_buy_stock_real_reg(sCode)
                    if sCode not in self.default_stock_list:
                        self.total_invest_amount = self.total_invest_amount + total_buy_price

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
            if "half_sell" in value.keys():
                half_sell = value["half_sell"]
            else:
                half_sell = False

            f = open(self.hold_etf_file_path, "a", encoding="utf8")
            f.write("%s\t%s\t%s\n" %
                    (code, purchase_date, half_sell))
            f.close()

        for code in self.today_buy_etf_stock_dict.keys():
            value = self.today_buy_etf_stock_dict[code]
            if "half_sell" in value.keys():
                half_sell = value["half_sell"]
            else:
                half_sell = False

            f = open(self.hold_etf_file_path, "a", encoding="utf8")
            f.write("%s\t%s\t%s\n" %
                    (code, self.today, half_sell))
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

        self.logging.logger.info("get_next_search_etf_stock_code item >> %s" % item[self.customType.STOCK_CODE])
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
