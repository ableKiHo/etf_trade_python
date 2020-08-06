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

        self.priority_list = ['252670', '233740', '122630', '251340']
        self.today = get_today_by_format('%Y%m%d')

        self.etf_info_event_loop = QEventLoop()
        self.tr_opt10080_info_event_loop = QEventLoop()
        self.all_etf_info_event_loop = QEventLoop()

        self.priority_cal_target_etf_stock_dict = {}
        self.second_cal_target_etf_stock_dict = {}

        self.screen_start_stop_real = "1000"
        self.buy_screen_meme_stock = "3000"
        self.buy_screen_real_stock = "6000"
        self.screen_opt10080_info = "4010"
        self.screen_etf_stock = "4020"
        self.screen_all_etf_stock = "4030"

        self.search_timer = QTimer()
        self.sell_timer = QTimer()

        self.martket_off_buy_count = 0
        self.total_buy_amount = 0
        self.priority_buy_flag = False
        self.second_buy_flag = False
        self.buy_search_stock_code = ''
        self.analysis_etf_target_dict = {}
        self.total_cal_target_etf_stock_dict = {}
        self.order_stock_dict = {}
        self.buy_point_dict = {}
        self.all_etf_stock_list = []
        self.top_rank_etf_stock_list = []
        self.search_stock_code = []

        self.status = "WAIT"

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF DAY TRADE START")
        self.detail_account_info()
        QTest.qWait(5000)
        self.read_target_etf_file()
        QTest.qWait(10000)

        self.get_all_etf_info()
        QTest.qWait(5000)
        self.get_goal_price_etf()
        QTest.qWait(5000)
        self.screen_number_setting(self.priority_cal_target_etf_stock_dict)
        self.screen_number_setting(self.second_cal_target_etf_stock_dict)

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
                self.loop_call_exit()

        elif sRealType == self.customType.STOCK_CONCLUSION:
            if self.status == "SEARCH":
                if sCode in self.second_cal_target_etf_stock_dict.keys() or sCode in self.priority_cal_target_etf_stock_dict.keys():

                    current_stock_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
                    current_stock_price = abs(int(current_stock_price.strip()))
                    if self.total_buy_amount < self.buy_possible_deposit:
                        if sCode in self.priority_cal_target_etf_stock_dict.keys() and self.priority_buy_flag is False:
                            if sCode not in self.order_stock_dict.keys() and current_stock_price >= self.priority_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]:
                                if current_stock_price > self.priority_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE] + 10:
                                    self.priority_buy_flag = True
                                    self.dynamicCall("SetRealRemove(QString, QString)", self.priority_cal_target_etf_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
                                    self.logging.logger.info("priority_buy >> %s" % self.order_stock_dict[sCode])
                                    self.buy_order_etf(sCode, sRealType, sRealData, get_next_price(self.priority_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]), self.priority_cal_target_etf_stock_dict)
                                else:
                                    self.order_stock_dict.update({sCode: {self.customType.GOAL_PRICE: self.priority_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE],
                                                                          self.customType.CURRENT_PRICE: current_stock_price}})
                                    self.priority_buy_flag = True
                                    self.dynamicCall("SetRealRemove(QString, QString)", self.priority_cal_target_etf_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
                                    self.logging.logger.info("priority_buy >> %s" % self.order_stock_dict[sCode])
                                    self.buy_order_etf(sCode, sRealType, sRealData, current_stock_price, self.priority_cal_target_etf_stock_dict)

                        if sCode in self.second_cal_target_etf_stock_dict.keys() and self.second_buy_flag is False:
                            if sCode not in self.order_stock_dict.keys() and current_stock_price >= self.second_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]:
                                if current_stock_price > self.second_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE] + 10:
                                    self.order_stock_dict.update({sCode: {self.customType.GOAL_PRICE: self.second_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE],
                                                                          self.customType.CURRENT_PRICE: current_stock_price}})
                                    self.second_buy_flag = True
                                    self.dynamicCall("SetRealRemove(QString, QString)", self.second_cal_target_etf_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
                                    self.logging.logger.info("second_buy >> %s" % self.order_stock_dict[sCode])
                                    self.buy_order_etf(sCode, sRealType, sRealData, get_next_price(self.second_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE]), self.second_cal_target_etf_stock_dict)
                                else:
                                    self.order_stock_dict.update({sCode: {self.customType.GOAL_PRICE: self.second_cal_target_etf_stock_dict[sCode][self.customType.GOAL_PRICE], self.customType.CURRENT_PRICE: current_stock_price}})
                                    self.second_buy_flag = True
                                    self.dynamicCall("SetRealRemove(QString, QString)", self.second_cal_target_etf_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
                                    self.logging.logger.info("second_buy >> %s" % self.order_stock_dict[sCode])
                                    self.buy_order_etf(sCode, sRealType, sRealData, current_stock_price, self.second_cal_target_etf_stock_dict)

    def martket_off_trading(self):
        self.logging.logger.info("market_off_trading")
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '153000') < currentDate:
            self.search_timer.stop()
            self.buy_search_stock_code = ''
            self.analysis_etf_target_dict = {}
            self.total_cal_target_etf_stock_dict = {}
            self.buy_point_dict = {}
            self.loop_last_price_buy_all_etf_stock()

            return

    def loop_last_price_buy_all_etf_stock(self):
        self.logging.logger.info('loop_last_price_buy_all_etf_stock')
        self.search_timer = default_q_timer_setting()
        self.search_timer.timeout.connect(self.prepare_last_price_buy_all_etf_stock)

    def prepare_last_price_buy_all_etf_stock(self):
        self.logging.logger.info('prepare_last_price_buy_all_etf_stock')
        self.all_etf_stock_list = []
        self.total_cal_target_etf_stock_dict = {}
        self.get_all_etf_stock()
        self.top_rank_etf_stock_list = get_top_rank_etf_stock(self.all_etf_stock_list, self.customType.VOLUME, 20)
        self.top_rank_etf_stock_list = [x for x in self.top_rank_etf_stock_list if
                                        x[self.customType.STOCK_CODE] not in self.priority_list and x[self.customType.STOCK_CODE] not in self.order_stock_dict.keys()]
        self.logging.logger.info('top_rank_etf_stock_list %s' % self.top_rank_etf_stock_list)
        self.search_timer.stop()

        self.loop_last_price_buy_search_etf()

    def loop_last_price_buy_search_etf(self):
        self.logging.logger.info('loop_last_price_buy_search_etf')
        self.search_timer = default_q_timer_setting()
        self.search_timer.timeout.connect(self.buy_search_last_price_etf)

    def buy_search_last_price_etf(self):
        if self.total_buy_amount >= self.buy_possible_deposit:
            self.logging.logger.info("day trade possible deposit over > %s / %s " % (self.total_buy_amount, self.buy_possible_deposit))
            self.call_exit()
        if len(self.top_rank_etf_stock_list) == 0:
            self.logging.logger.info("day trade target nothing")
            self.call_exit()
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '160000') < currentDate:
            self.logging.logger.info("day trade time over")
            self.call_exit()

        self.get_next_rank_etf_stock_code(len(self.top_rank_etf_stock_list))

        code = self.buy_search_stock_code
        self.logging.logger.info("top_rank_etf_stock_list loop > %s " % code)
        self.search_stock_code.append(code)

        self.get_opt10080_info(code)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma60", 60)

        last_price_buy_point = self.get_conform_last_price_buy_case(code)

        if bool(last_price_buy_point) and code not in self.order_stock_dict.keys():
            self.logging.logger.info("last_price_buy_point >>  %s " % last_price_buy_point)
            if self.martket_off_buy_count < 2:
                result = self.use_money / last_price_buy_point[self.customType.CURRENT_PRICE]
                quantity = int(result)
                if quantity >= 1:
                    self.logging.logger.info("last_price_buy_point break >> %s" % code)
                    self.martket_off_buy_count = self.martket_off_buy_count + 1
                    self.market_price_send_order(code, quantity)
                else:
                    self.line.notification("lack quantity[%s] > %s " % (code, last_price_buy_point[self.customType.CURRENT_PRICE]))
                    self.logging.logger.info("lack quantity[%s] > %s " % (code, last_price_buy_point[self.customType.CURRENT_PRICE]))

        if len(self.search_stock_code) == len(self.top_rank_etf_stock_list):
            self.logging.logger.info("market time off trade search end")
            self.search_timer.stop()
            self.call_exit()

        self.logging.logger.info('last_price_buy_search_etf end')

    def get_next_rank_etf_stock_code(self, max_index=4):
        if self.buy_search_stock_code == '':
            item = self.top_rank_etf_stock_list[0]
        else:
            index = next((index for (index, d) in enumerate(self.top_rank_etf_stock_list) if d[self.customType.STOCK_CODE] == self.buy_search_stock_code), None)
            if index < 0 or index > max_index:
                self.logging.logger.info("not found next stock code > index:[%s] " % index)
                sys.exit()

            if index == len(self.top_rank_etf_stock_list) - 1:
                index = -1
            item = self.top_rank_etf_stock_list[index + 1]

        self.buy_search_stock_code = item[self.customType.STOCK_CODE]

    def get_conform_last_price_buy_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 7:
            return {}

        analysis_rows = rows[:7]

        first_tic = analysis_rows[0]

        ma_field_list = ["ma20", "ma5", "ma10", "ma60"]
        for field in ma_field_list:
            if first_tic[field] == '':
                return {}

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '' or x["ma5"] == '' or x["ma10"] == '' or x["ma60"] == '']
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

        return copy.deepcopy(first_tic)

    def all_real_remove(self):
        self.logging.logger.info('all_real_remove')
        for code in self.priority_cal_target_etf_stock_dict.keys():
            self.dynamicCall("SetRealRemove(QString, QString)", self.priority_cal_target_etf_stock_dict[code][self.customType.SCREEN_NUMBER], code)
        for code in self.second_cal_target_etf_stock_dict.keys():
            self.dynamicCall("SetRealRemove(QString, QString)", self.second_cal_target_etf_stock_dict[code][self.customType.SCREEN_NUMBER], code)

    def buy_order_etf(self, sCode, sRealType, sRealData, current_stock_price, target_dict):
        result = self.use_money / current_stock_price
        self.logging.logger.info(self.logType.PASS_CONDITION_GOAL_PRICE_LOG % (sCode, target_dict[sCode][self.customType.GOAL_PRICE], current_stock_price, result))
        quantity = int(result)
        if quantity >= 1:
            self.send_order_limit_stock_price(sCode, quantity, current_stock_price, target_dict)
        else:
            self.line.notification("lack quantity[%s] > %s " % (sCode, current_stock_price))
            self.logging.logger.info("lack quantity[%s] > %s " % (sCode, current_stock_price))

    def get_all_etf_info(self):
        self.logging.logger.info('get_all_etf_info_opt10001')
        code_list = list(set(list(self.priority_cal_target_etf_stock_dict.keys()) + list(self.second_cal_target_etf_stock_dict.keys())))
        for code in code_list:
            QTest.qWait(5000)
            self.logging.logger.info('call opt10001 %s' % code)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def get_all_etf_stock(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TAXATION_TYPE, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.COMPARED_TO_NAV, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MANAGER, "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40004, "opt40004", sPrevNext, self.screen_all_etf_stock)

        if sPrevNext == "0":
            self.logging.logger.info('get_all_etf_stock_opt40004')
            self.all_etf_info_event_loop.exec_()

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

    def get_opt10080_info(self, code):
        self.tr_opt10080_info(code)

    def tr_opt10080_info(self, code, sPrevNext="0"):
        self.logging.logger.info('tr_opt10080_info > [%s]' % code)
        tic = "3분"
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", tic)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10080", "opt10080", sPrevNext, self.screen_opt10080_info)

        self.tr_opt10080_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT40004:
            self.trdata_slot_opt40004(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10080":
            self.trdata_slot_opt10080(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opw00001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.DEPOSIT)
        self.deposit = int(deposit)
        buy_possible_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.AVAILABLE_AMOUNT)
        self.buy_possible_deposit = int(buy_possible_deposit)
        self.buy_possible_deposit = math.trunc(self.buy_possible_deposit / 2)
        self.logging.logger.info(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        self.line.notification(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        use_money = float(self.buy_possible_deposit) * self.use_money_percent
        self.use_money = int(use_money)
        self.purchased_deposit = int(use_money)

        self.stop_screen_cancel(self.screen_my_info)
        self.detail_account_info_event_loop.exit()
        self.logging.logger.info(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)
        self.line.notification(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.START_PRICE)
        if code in self.priority_cal_target_etf_stock_dict.keys():
            self.priority_cal_target_etf_stock_dict[code].update({self.customType.START_PRICE: abs(int(start_price.strip()))})

        if code in self.second_cal_target_etf_stock_dict.keys():
            self.second_cal_target_etf_stock_dict[code].update({self.customType.START_PRICE: abs(int(start_price.strip()))})

        self.etf_info_event_loop.exit()

    def trdata_slot_opt40004(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(rows):
            volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            volume = int(volume.strip())
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_CODE)
            code = code.strip()
            code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_NAME)
            code_nm = code_nm.strip()
            row = {self.customType.STOCK_CODE: code, self.customType.VOLUME: volume, self.customType.STOCK_NAME: code_nm}
            self.all_etf_stock_list.append(row)

        if sPrevNext == "2":
            self.get_all_etf_stock(sPrevNext="2")
        else:
            self.stop_screen_cancel(self.screen_all_etf_stock)
            self.all_etf_info_event_loop.exit()

    def trdata_slot_opt10080(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info('trdata_slot_opt10080 > [%s][%s]' % (sScrNo, sRQName))
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
            b = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            b = int(b.strip())
            c = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.TIGHTENING_TIME)
            c = c.strip()
            d = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.START_PRICE)
            d = int(d.strip())
            e = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HIGHEST_PRICE)
            e = int(e.strip())
            f = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.LOWEST_PRICE)
            f = int(f.strip())

            row = {self.customType.CURRENT_PRICE: a, self.customType.VOLUME: b, self.customType.TIGHTENING_TIME: c, self.customType.START_PRICE: d, self.customType.HIGHEST_PRICE: e,
                   self.customType.LOWEST_PRICE: f, "ma20": '', "ma5": '', "ma10": '', "ma60": ''}
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

                    if stock_code in self.priority_list:
                        self.priority_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                     self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                     self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                     self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                     self.customType.GOAL_PRICE: '',
                                                                                     "stat": ''}})
                    else:
                        self.second_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                   self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                   self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                   self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                   self.customType.GOAL_PRICE: '',
                                                                                   "stat": ''}})

            f.close()

    def get_goal_price_etf(self):
        self.logging.logger.info("get_goal_price_etf")
        for code in self.priority_cal_target_etf_stock_dict.keys():
            value = self.priority_cal_target_etf_stock_dict[code]
            goal_stock_price = cal_goal_stock_price(value[self.customType.START_PRICE], value[self.customType.LAST_DAY_LAST_PRICE], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                                                    value[self.customType.LAST_DAY_LOWEST_PRICE])
            if goal_stock_price > 0:
                self.priority_cal_target_etf_stock_dict[code].update({self.customType.GOAL_PRICE: goal_stock_price})
                self.logging.logger.info("pass goal_price_priority_etf[%s] >> %s" % (code, self.priority_cal_target_etf_stock_dict[code]))
                self.line.notification("pass goal_price_priority_etf[%s] >> %s" % (code, goal_stock_price))
            else:
                self.priority_cal_target_etf_stock_dict[code].update({"stat": "del"})

        for code in self.second_cal_target_etf_stock_dict.keys():
            value = self.second_cal_target_etf_stock_dict[code]
            goal_stock_price = cal_goal_stock_price(value[self.customType.START_PRICE], value[self.customType.LAST_DAY_LAST_PRICE], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                                                    value[self.customType.LAST_DAY_LOWEST_PRICE])
            if goal_stock_price > 0:
                self.second_cal_target_etf_stock_dict[code].update({self.customType.GOAL_PRICE: goal_stock_price})
                self.logging.logger.info("pass goal_price_second_etf[%s] >> %s" % (code, self.second_cal_target_etf_stock_dict[code]))
                self.line.notification("pass goal_price_second_etf[%s] >> %s" % (code, goal_stock_price))
            else:
                self.second_cal_target_etf_stock_dict[code].update({"stat": "del"})

        for key in [key for key in self.priority_cal_target_etf_stock_dict if self.priority_cal_target_etf_stock_dict[key]["stat"] == "del"]: del self.priority_cal_target_etf_stock_dict[key]
        for key in [key for key in self.second_cal_target_etf_stock_dict if self.second_cal_target_etf_stock_dict[key]["stat"] == "del"]: del self.second_cal_target_etf_stock_dict[key]

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
        for code in self.priority_cal_target_etf_stock_dict.keys():
            if self.priority_cal_target_etf_stock_dict[code][self.customType.GOAL_PRICE] > 0:
                screen_num = self.priority_cal_target_etf_stock_dict[code][self.customType.SCREEN_NUMBER]
                fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
                self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")
        for code in self.second_cal_target_etf_stock_dict.keys():
            if self.second_cal_target_etf_stock_dict[code][self.customType.GOAL_PRICE] > 0:
                screen_num = self.second_cal_target_etf_stock_dict[code][self.customType.SCREEN_NUMBER]
                fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
                self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

        self.status = "SEARCH"

    def send_order_limit_stock_price(self, sCode, quantity, limit_stock_price, stock_dict):
        self.logging.logger.info("send_order_limit_stock_price")
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, stock_dict[sCode][self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, sCode, quantity, limit_stock_price,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

        if order_success == 0:

            self.logging.logger.info(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
            self.line.notification(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)
        return order_success

    def market_price_send_order(self, code, quantity):
        self.logging.logger.info("[%s]add_send_order > %s " % (code, quantity))
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.send_order_market_price_stock_price(code, quantity, self.buy_point_dict)

    def send_order_market_price_stock_price(self, code, quantity, stock_dict):
        self.logging.logger.info("send_order_market_price_stock_price > %s / %s" % (code, stock_dict))
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, self.buy_screen_real_stock, self.account_num, 1, code, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_OFF_TIME_LAST_PRICE], ""])

        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_BUY_SUCCESS_LOG)
            self.line.notification(self.logType.ORDER_BUY_SUCCESS_LOG)
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)

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
            self.total_buy_amount = self.total_buy_amount + total_buy_price
            if self.priority_buy_flag is True and self.second_buy_flag is True:
                self.logging.logger.info("all_real_remove >> %s" % self.order_stock_dict)
                self.all_real_remove()
                return

    def loop_call_exit(self):
        self.logging.logger.info("loop_call_exit")
        self.search_timer = default_q_timer_setting(20)
        self.search_timer.timeout.connect(self.martket_off_trading)

    def call_exit(self):
        self.logging.logger.info("시스템 종료")
        self.search_timer.stop()
        sys.exit()
