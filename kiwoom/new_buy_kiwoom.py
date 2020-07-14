import math
import sys

from PyQt5.QtCore import QEventLoop, QTimer

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


class NewBuyKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF New BuyKiwoom() class start.")
        self.line.notification("ETF New BuyKiwoom() class start.")

        self.analysis_etf_target_dict = {}
        self.all_etf_stock_list = []
        self.buy_point_dict = {}
        self.target_etf_stock_dict = {}
        self.top_rank_etf_stock_list = []
        self.buy_search_stock_code = ''

        self.buy_screen_meme_stock = "3000"
        self.buy_screen_real_stock = "6000"
        self.screen_opt10079_info = "7000"
        self.screen_all_etf_stock = "8000"
        self.screen_etf_stock = "5000"

        self.max_plus_sell_std_percent = 3

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF NEW BUY TRADE START")
        self.etf_info_event_loop = QEventLoop()
        self.tr_opt10079_info_event_loop = QEventLoop()
        self.all_etf_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop = QEventLoop()

        self.timer2 = QTimer()

        self.detail_account_info()
        self.detail_account_mystock()

        self.loop_all_etf_stock()

    def new_chejan_slot(self, sGubun, nItemCnt, sFidList):
        self.logging.logger.info("new_chejan_slot  %s", sGubun)
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

            self.buy_point_dict.update({self.customType.PURCHASE_UNIT_PRICE: buy_price})
            self.buy_point_dict.update({self.customType.TOTAL_PURCHASE_PRICE: total_buy_price})
            self.buy_point_dict.update({self.customType.HOLDING_QUANTITY: holding_quantity})
            self.buy_point_dict.update({self.customType.ORDER_EXECUTION: True})

            self.logging.logger.info(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))
            self.line.notification(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))

            self.logging.logger.info("new_chejan_slot meme_gubun [%s]" % meme_gubun)
            if meme_gubun == '매도':
                if holding_quantity == 0:
                    self.timer2.stop()
                    self.buy_point_dict = {}
                    self.logging.logger.info("call loop_all_etf_stock at new_chejan_slot")
                    self.loop_all_etf_stock()
            else:
                self.timer2.stop()
                self.logging.logger.info("call search_buy_etf at new_chejan_slot")
                self.loop_sell_search_etf()

    def trdata_slot_opw00018(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)  # 최대 20개 카운트
        for i in range(rows):
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_NUMBER)
            code = code.strip()[1:]

            stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.HOLDING_QUANTITY)
            buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.PURCHASE_PRICE)
            total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.PURCHASE_AMOUNT)

            stock_quantity = int(stock_quantity.strip())
            buy_price = int(buy_price.strip())
            total_chegual_price = int(total_chegual_price.strip())

            self.buy_point_dict.update({self.customType.STOCK_CODE: code})
            self.buy_point_dict.update({self.customType.HOLDING_QUANTITY: stock_quantity})
            self.buy_point_dict.update({self.customType.PURCHASE_UNIT_PRICE: buy_price})
            self.buy_point_dict.update({self.customType.TOTAL_PURCHASE_PRICE: total_chegual_price})
            self.buy_point_dict.update({self.customType.ORDER_EXECUTION: True})

        if sPrevNext == "2":
            self.detail_account_mystock(sPrevNext="2")
        else:
            self.stop_screen_cancel(self.screen_my_info)
            self.detail_account_info_event_loop.exit()

    def trdata_slot_opt40004(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        # self.logging.logger.info("trdata_slot_opt40004 %s / %s" % (sScrNo, sPrevNext))
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

    def trdata_slot_opw00001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.DEPOSIT)
        self.deposit = int(deposit)
        buy_possible_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.AVAILABLE_AMOUNT)
        self.buy_possible_deposit = int(buy_possible_deposit)

        self.logging.logger.info(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        self.line.notification(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        use_money = float(self.buy_possible_deposit) * self.use_money_percent
        self.use_money = int(use_money)
        self.purchased_deposit = int(use_money)

        self.stop_screen_cancel(self.screen_my_info)
        self.detail_account_info_event_loop.exit()
        self.logging.logger.info(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)
        self.line.notification(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)

    def get_opt10079_info(self, code):
        self.logging.logger.info('get_opt10079_info > [%s]' % code)
        self.tr_opt10079_info(code)

    def tr_opt10079_info(self, code, sPrevNext="0"):
        self.logging.logger.info('tr_opt10079_info > [%s]' % code)
        tic = "120틱"
        if code == "114800":
            tic = "60틱"
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", tic)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10079", "opt10079", sPrevNext, self.screen_opt10079_info)

        self.tr_opt10079_info_event_loop.exec_()

    def trdata_slot_opt10079(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info('trdata_slot_opt10079 > [%s][%s]' % (sScrNo, sRQName))
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
                   self.customType.LOWEST_PRICE: f, "ma20": ''}
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

        self.stop_screen_cancel(self.screen_opt10079_info)
        self.tr_opt10079_info_event_loop.exit()

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_NAME)
        last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        last_stock_price = last_stock_price.strip()
        start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.START_PRICE)
        start_price = start_price.strip()

        self.target_etf_stock_dict[code].update({self.customType.STOCK_NAME: code_nm})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LAST_PRICE: abs(int(last_stock_price))})
        self.target_etf_stock_dict[code].update({self.customType.START_PRICE: abs(int(start_price))})

        self.etf_info_event_loop.exit()

    def prepare_all_etf_stock(self):
        self.logging.logger.info('prepare_all_etf_stock')
        self.all_etf_stock_list = []
        if not bool(self.buy_point_dict):
            self.get_all_etf_stock()
            self.top_rank_etf_stock_list = get_top_rank_etf_stock(self.all_etf_stock_list, self.customType.VOLUME, 5)
            self.logging.logger.info('top_rank_etf_stock_list %s' % self.top_rank_etf_stock_list)
            self.timer2.stop()
        self.prepare_search_buy_etf()

    def loop_all_etf_stock(self):
        self.logging.logger.info('loop_all_etf_stock')
        self.timer2 = self.default_q_timer_setting()
        self.timer2.timeout.connect(self.prepare_all_etf_stock)

    def prepare_search_buy_etf(self):
        self.logging.logger.info('prepare_search_buy_etf %s' % self.buy_point_dict)

        if not bool(self.buy_point_dict):
            self.loop_buy_search_etf()
        else:
            self.screen_number_setting(self.buy_point_dict)
            self.loop_sell_search_etf()
        # self.loop_search_buy_etf()

    def default_q_timer_setting(self):
        timer2 = QTimer()
        timer2.start(1000 * 5)
        return timer2

    def loop_sell_search_etf(self):
        self.logging.logger.info('loop_sell_search_etf')
        self.timer2 = self.default_q_timer_setting()
        self.timer2.timeout.connect(self.sell_search_etf)

    def loop_buy_search_etf(self):
        self.logging.logger.info('loop_buy_search_etf')
        self.timer2 = self.default_q_timer_setting()
        self.timer2.timeout.connect(self.buy_search_etf)

    def sell_search_etf(self):
        self.logging.logger.info('sell_search_etf info %s' % self.buy_point_dict)
        if self.customType.ORDER_EXECUTION not in self.buy_point_dict.keys():
            return
        code = self.buy_point_dict[self.customType.STOCK_CODE]

        self.get_opt10079_info(code)
        create_moving_average_20_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20")
        rows = self.analysis_etf_target_dict[code]["row"]
        first_tic = rows[0]
        prepare = self.prepare_sell_send_order(code, rows[0])
        if prepare == 'SellCase':
            self.timer2.stop()
            self.logging.logger.info("SellCase prepare_sell_send_order [%s]>  %s " % (code, first_tic))
            self.sell_send_order(code, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
            return
        result = self.get_sell_point(rows[:4])
        if result == 'SellCase':
            self.timer2.stop()
            self.logging.logger.info("get_sell_point [%s]>  %s " % (code, first_tic))
            self.sell_send_order(code, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
            return
        result = self.get_loss_cut_point(rows[:5])
        if result == 'SellCase':
            self.timer2.stop()
            self.logging.logger.info("get_loss_cut_point [%s]>  %s " % (code, first_tic))
            self.sell_send_order(code, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
            return
        self.logging.logger.info('sell_search_etf end')

    def get_next_stock_code(self):
        if self.buy_search_stock_code == '':
            item = self.top_rank_etf_stock_list[0]
        else:
            index = next((index for (index, d) in enumerate(self.top_rank_etf_stock_list) if d[self.customType.STOCK_CODE] == self.buy_search_stock_code), None)
            if index < 0 or index > 4:
                self.logging.logger.info("not found next stock code > index:[%s] " % index)
                sys.exit()

            if index == len(self.top_rank_etf_stock_list) - 1:
                index = -1
            item = self.top_rank_etf_stock_list[index + 1]

        self.buy_search_stock_code = item[self.customType.STOCK_CODE]

    def buy_search_etf(self):
        self.logging.logger.info('buy_search_etf')
        today = get_today_by_format('%Y%m%d')
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (today + '153000') < currentDate:
            sys.exit()

        if (today + '150000') < currentDate:
            return

        self.get_next_stock_code()

        code = self.buy_search_stock_code
        self.logging.logger.info("top_rank_etf_stock_list loop > %s " % code)

        self.get_opt10079_info(code)
        create_moving_average_20_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20")
        buy_point = self.get_buy_point(code)
        if bool(buy_point):
            self.prepare_send_order(code, buy_point)
            self.logging.logger.info("buy_point break")
            return

        first_buy_point = self.get_conform_first_buy_case(code)
        if bool(first_buy_point):
            self.prepare_send_order(code, first_buy_point)
            self.logging.logger.info("first_buy_point break")
            return
        seconf_buy_point = self.get_conform_second_buy_case(code)
        if bool(seconf_buy_point):
            self.prepare_send_order(code, seconf_buy_point)
            self.logging.logger.info("second_buy_point break")
            return
        third_buy_point = self.get_conform_third_buy_case(code)
        if bool(third_buy_point):
            self.prepare_send_order(code, third_buy_point)
            self.logging.logger.info("third_buy_point break")
            return

        self.logging.logger.info('buy_search_etf end')

    def prepare_sell_send_order(self, code, current_dict):
        result = ''
        today = get_today_by_format('%Y%m%d')
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        self.logging.logger.info("prepare_sell_send_order [%s]>> %s" % (code, current_dict))
        if (today + '151000') < currentDate:
            self.logging.logger.info("sell_send_order by currentDate() [%s] > %s " % (code, current_dict[self.customType.CURRENT_PRICE]))
            result = "SellCase"

        minus_sell_std_price = get_minus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE])
        if current_dict[self.customType.CURRENT_PRICE] < minus_sell_std_price:
            self.logging.logger.info("sell_send_order by minus_sell_std_price() [%s] > %s / %s" % (code, current_dict[self.customType.CURRENT_PRICE], minus_sell_std_price))
            result = "SellCase"

        return result

    def init_search_info(self):
        self.timer2.stop()
        self.buy_search_stock_code = ''

    def prepare_send_order(self, code, buy_point):
        buy_point.update({self.customType.STOCK_CODE: code})
        self.logging.logger.info("buy_point > %s " % buy_point)
        self.buy_point_dict = copy.deepcopy(buy_point)
        self.screen_number_setting(self.buy_point_dict)
        limit_stock_price = int(self.buy_point_dict[self.customType.CURRENT_PRICE])
        result = self.use_money / limit_stock_price
        quantity = int(result)
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.init_search_info()
            self.send_order_limit_stock_price(code, quantity, limit_stock_price, self.buy_point_dict)

    def get_loss_cut_point(self, rows):
        self.logging.logger.info("get_loss_cut_point >  %s " % rows)
        purchase_unit_price = self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE]
        second_low = rows[1]
        third_low = rows[2]
        forth_low = rows[3]
        fifth_low = rows[4]

        if forth_low[self.customType.START_PRICE] >= forth_low[self.customType.CURRENT_PRICE]:
            if third_low[self.customType.START_PRICE] >= third_low[self.customType.CURRENT_PRICE]:
                if second_low[self.customType.START_PRICE] >= second_low[self.customType.CURRENT_PRICE]:

                    if fifth_low[self.customType.CURRENT_PRICE] >= forth_low[self.customType.CURRENT_PRICE]:
                        if forth_low[self.customType.CURRENT_PRICE] >= third_low[self.customType.CURRENT_PRICE]:
                            if third_low[self.customType.CURRENT_PRICE] >= second_low[self.customType.CURRENT_PRICE]:

                                if second_low[self.customType.CURRENT_PRICE] < second_low["ma20"]:
                                    if second_low[self.customType.CURRENT_PRICE] < (purchase_unit_price - (get_tic_price(purchase_unit_price) * 2)):
                                        return 'SellCase'

        return None




    def get_sell_point(self, rows):
        self.logging.logger.info("get_sell_point >  %s " % rows)
        purchase_unit_price = self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE]
        first_low = rows[0]
        first_current_price = first_low[self.customType.CURRENT_PRICE]
        first_lowest_price = first_low[self.customType.LOWEST_PRICE]
        first_highest_price = first_low[self.customType.HIGHEST_PRICE]
        first_start_price = first_low[self.customType.START_PRICE]
        first_ma20 = first_low["ma20"]
        second_low = rows[1]
        second_lowest_price = second_low[self.customType.LOWEST_PRICE]
        second_highest_price = second_low[self.customType.HIGHEST_PRICE]
        second_current_price = second_low[self.customType.CURRENT_PRICE]
        second_start_price = second_low[self.customType.START_PRICE]
        second_ma20 = second_low["ma20"]
        third_low = rows[2]
        third_start_price = third_low[self.customType.START_PRICE]
        third_current_price = third_low[self.customType.CURRENT_PRICE]
        forth_low = rows[3]
        forth_start_price = forth_low[self.customType.START_PRICE]
        forth_current_price = forth_low[self.customType.CURRENT_PRICE]

        if first_current_price > get_max_plus_sell_std_price_by_std_per(purchase_unit_price, self.max_plus_sell_std_percent):
            self.logging.logger.info("max_plus_sell_std_price_by_std_per")
            return 'SellCase'
        if first_current_price > (purchase_unit_price + (get_tic_price(purchase_unit_price) * 2)):
            if second_lowest_price < second_ma20 < second_highest_price:
                self.logging.logger.info("second range")
                return 'SellCase'
            if second_current_price <= second_ma20 and second_start_price > second_current_price:
                self.logging.logger.info("second price")
                return 'SellCase'
            if forth_start_price > forth_current_price and third_start_price > third_current_price and second_start_price > second_current_price:
                self.logging.logger.info("increase price")
                return 'SellCase'
            if first_lowest_price <= first_ma20 <= first_highest_price and first_start_price > first_current_price:
                self.logging.logger.info("first price")
                return 'SellCase'
        return None

    def get_buy_point(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 5:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:5]
        self.logging.logger.info("analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]
        secode_tic = analysis_rows[1]
        other_tics = analysis_rows[1:]
        some_tics = analysis_rows[2:]

        empty_ma20_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_ma20_list) > 0:
            self.logging.logger.info("empty_ma20_list > [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], empty_ma20_list))
            return {}
        if first_tic[self.customType.START_PRICE] < secode_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic START_PRICE check > [%s] >> %s / %s / %s " % (
                code, first_tic[self.customType.TIGHTENING_TIME], first_tic[self.customType.START_PRICE], secode_tic[self.customType.CURRENT_PRICE]))
            return {}
        if first_tic[self.customType.LOWEST_PRICE] <= first_tic["ma20"]:
            self.logging.logger.info("LOWEST_PRICE_check > [%s] >> %s / %s / %s " % (code, first_tic[self.customType.TIGHTENING_TIME], first_tic[self.customType.LOWEST_PRICE], first_tic["ma20"]))
            return {}
        if secode_tic[self.customType.LOWEST_PRICE] >= secode_tic["ma20"] or secode_tic["ma20"] >= secode_tic[self.customType.HIGHEST_PRICE]:
            self.logging.logger.info("secode_tic range check > [%s] >> %s / %s / %s / %s" % (
                code, first_tic[self.customType.TIGHTENING_TIME], secode_tic[self.customType.LOWEST_PRICE], secode_tic["ma20"], secode_tic[self.customType.HIGHEST_PRICE]))
            return {}
        if first_tic[self.customType.CURRENT_PRICE] < secode_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic CURRENT_PRICE_check > [%s] >> %s / %s / %s" % (
                code, first_tic[self.customType.TIGHTENING_TIME], first_tic[self.customType.CURRENT_PRICE], secode_tic[self.customType.CURRENT_PRICE]))
            return {}
        higher_ma20_list = [x for x in some_tics if x[self.customType.HIGHEST_PRICE] > x["ma20"]]
        if len(higher_ma20_list) > 0:
            self.logging.logger.info("HIGHEST_PRICE_LIST_check > [%s] >> %s / %s " % (code, first_tic[self.customType.TIGHTENING_TIME], higher_ma20_list))
            return {}
        lower_ma20_list = [x for x in other_tics if x["ma20"] > secode_tic["ma20"]]
        if len(lower_ma20_list) > 0:
            self.logging.logger.info("lower_ma20_list_check > [%s] >> %s / %s " % (code, first_tic[self.customType.TIGHTENING_TIME], lower_ma20_list))
            return {}

        return copy.deepcopy(first_tic)

    def get_conform_first_buy_case(self, code):
        self.logging.logger.info("first_buy_case analysis_rows > [%s]" % code)
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 5:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:5]

        first_tic = analysis_rows[0]
        secode_tic = analysis_rows[1]
        third_tic = analysis_rows[2]
        forth_tic = analysis_rows[3]
        fifth_tic = analysis_rows[4]

        empty_ma20_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_ma20_list) > 0:
            self.logging.logger.info("empty_ma20_list > [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], empty_ma20_list))
            return {}

        if first_tic[self.customType.LOWEST_PRICE] <= first_tic["ma20"]:
            self.logging.logger.info("first_tic lowest_price check > [%s] >> %s" % (code, first_tic[self.customType.TIGHTENING_TIME]))
            return {}
        if secode_tic["ma20"] > secode_tic[self.customType.HIGHEST_PRICE]:
            self.logging.logger.info("secode_tic highest_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
            return {}
        if third_tic["ma20"] < third_tic[self.customType.LOWEST_PRICE]:
            self.logging.logger.info("third_tic lowest_price check > [%s] >> %s" % (code, first_tic[self.customType.TIGHTENING_TIME]))
            return {}
        if forth_tic[self.customType.HIGHEST_PRICE] >= forth_tic["ma20"] or fifth_tic[self.customType.HIGHEST_PRICE] >= fifth_tic["ma20"]:
            self.logging.logger.info("forth_tic and fifth_tic highest_price check > [%s] >> %s" % (code, first_tic[self.customType.TIGHTENING_TIME]))
            return {}

        if self.is_increase_current_price(first_tic, secode_tic, third_tic, forth_tic, self.customType.CURRENT_PRICE):
            if self.is_current_start_compare(third_tic) and self.is_current_start_compare(secode_tic) and self.is_current_start_compare(first_tic):
                if first_tic["ma20"] >= secode_tic["ma20"]:
                    return copy.deepcopy(first_tic)

        self.logging.logger.info("increase check > [%s] >> %s" % (code, first_tic[self.customType.TIGHTENING_TIME]))
        return {}

    def is_increase_current_price(self, first_tic, secode_tic, third_tic, forth_tic, field):
        return forth_tic[field] <= third_tic[field] <= secode_tic[field] <= first_tic[field] and self.is_current_start_compare(first_tic)

    def is_current_start_compare(self, dict_info):
        return dict_info[self.customType.START_PRICE] < dict_info[self.customType.CURRENT_PRICE]

    def get_conform_second_buy_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 8:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:8]
        self.logging.logger.info("second_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))
        first_tic = analysis_rows[0]

        empty_ma20_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_ma20_list) > 0:
            self.logging.logger.info("empty_ma20_list > [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], empty_ma20_list))
            return {}

        compare_rows = analysis_rows[1:]
        breaker = False
        compare_tic = copy.deepcopy(first_tic)
        for x in compare_rows:
            if math.trunc(compare_tic["ma20"]) < math.trunc(x["ma20"]):
                breaker = True
                self.logging.logger.info("increase ma20 check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                break
            compare_tic = copy.deepcopy(x)

        if not breaker:
            second_tic = analysis_rows[1]
            if second_tic[self.customType.LOWEST_PRICE] < second_tic["ma20"]:
                breaker = True
                self.logging.logger.info("second_tic lowest_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))

        if not breaker:
            compare_rows = analysis_rows[2:]
            for x in compare_rows:
                if x[self.customType.LOWEST_PRICE] >= x["ma20"]:
                    breaker = True
                    self.logging.logger.info("from third tic lowest_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                    break

        if not breaker:
            first_tic = analysis_rows[0]
            second_tic = analysis_rows[1]
            if first_tic[self.customType.START_PRICE] < second_tic[self.customType.CURRENT_PRICE]:
                breaker = True
                self.logging.logger.info("first tic start_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
            elif first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
                self.logging.logger.info("first tic current_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                breaker = True

        if not breaker:
            return first_tic
        return {}

    def get_conform_third_buy_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 6:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:6]
        self.logging.logger.info("third_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))
        first_tic = analysis_rows[0]

        empty_ma20_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_ma20_list) > 0:
            self.logging.logger.info("empty_ma20_list > [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], empty_ma20_list))
            return {}

        compare_tic = copy.deepcopy(first_tic)
        breaker = False
        compare_rows = analysis_rows[1:]

        for x in compare_rows:
            if math.trunc(compare_tic["ma20"]) < math.trunc(x["ma20"]):
                breaker = True
                self.logging.logger.info("increase ma20 check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                break
            compare_tic = copy.deepcopy(x)

        if not breaker:
            first_tic = analysis_rows[0]
            second_tic = analysis_rows[1]
            if first_tic[self.customType.START_PRICE] < second_tic[self.customType.CURRENT_PRICE]:
                breaker = True
                self.logging.logger.info("first tic start_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
            elif first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
                self.logging.logger.info("first tic current_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                breaker = True

        if not breaker:
            for x in compare_rows:
                if x[self.customType.START_PRICE] >= x[self.customType.CURRENT_PRICE]:
                    breaker = True
                    self.logging.logger.info("white candle check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                    break

        if not breaker:
            compare_rows = analysis_rows[2:]
            compare_tic1 = copy.deepcopy(analysis_rows[1])
            for x in compare_rows:
                if math.trunc(compare_tic1[self.customType.CURRENT_PRICE]) <= math.trunc(x[self.customType.CURRENT_PRICE]):
                    self.logging.logger.info("increase current_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                    breaker = True
                    break
                compare_tic1 = copy.deepcopy(x)

        if not breaker:
            sixth_tic = analysis_rows[5]
            fifth_tic = analysis_rows[4]
            if sixth_tic[self.customType.LOWEST_PRICE] >= sixth_tic["ma20"] and fifth_tic[self.customType.LOWEST_PRICE] >= fifth_tic["ma20"]:
                self.logging.logger.info("last tic range check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                breaker = True

        if not breaker:
            return first_tic
        return {}

    def send_order_limit_stock_price(self, code, quantity, limit_stock_price, stock_dict):
        self.logging.logger.info("send_order_limit_stock_price > %s / %s" % (code, stock_dict))
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, stock_dict[self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, code, quantity, limit_stock_price,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

        if order_success == 0:
            self.logging.logger.info(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity, limit_stock_price, self.purchased_deposit))
            self.line.notification(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity, limit_stock_price, self.purchased_deposit))
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)

    def get_etf_stock_info(self, code):
        self.logging.logger.info("get_etf_stock_info")
        if code not in self.target_etf_stock_dict.keys():
            self.target_etf_stock_dict.update({code: {}})
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
        self.etf_info_event_loop.exec_()

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

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        # self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.new_chejan_slot)

    def detail_account_mystock(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_mystock")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00018, "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def screen_number_setting(self, stock_dict):
        stock_dict.update({self.customType.SCREEN_NUMBER: self.buy_screen_real_stock})
        stock_dict.update({self.customType.MEME_SCREEN_NUMBER: self.buy_screen_meme_stock})

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info('trdata_slot %s / %s' % (sRQName, sPrevNext))
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10079":
            self.trdata_slot_opt10079(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT40004:
            self.trdata_slot_opt40004(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPW00018:
            self.trdata_slot_opw00018(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def get_all_etf_stock(self, sPrevNext="0"):
        self.logging.logger.info("get_all_etf_stock_1 %s " % sPrevNext)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TAXATION_TYPE, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.COMPARED_TO_NAV, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MANAGER, "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40004, "opt40004", sPrevNext, self.screen_all_etf_stock)
        self.logging.logger.info("get_all_etf_stock_2 %s %s" % (sPrevNext, self.customType.OPT40004))
        self.all_etf_info_event_loop.exec_()


    def detail_account_info(self, sPrevNext="0"):
        #QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)
        self.detail_account_info_event_loop.exec_()
