import sys

from PyQt5.QtCore import *

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


def default_q_timer_setting(second=5):
    timer2 = QTimer()
    timer2.start(1000 * second)
    return timer2


class RenewalBuyKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF RenewalBuyKiwoom() class start.")
        self.line.notification("ETF RenewalBuyKiwoom() class start.")

        self.analysis_etf_file_path = self.property.analysisEtfFilePath

        self.analysis_etf_target_dict = {}
        self.all_etf_stock_list = []
        self.buy_point_dict = {}
        self.top_rank_etf_stock_list = []
        self.buy_search_stock_code = ''
        self.total_cal_target_etf_stock_dict = {}

        self.buy_screen_meme_stock = "3000"
        self.buy_screen_real_stock = "6000"
        self.screen_opt10079_info = "7000"
        self.screen_all_etf_stock = "8000"
        self.screen_etf_stock = "5000"

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF RENEWAL BUY TRADE START")
        self.tr_opt10079_info_event_loop = QEventLoop()
        self.all_etf_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop = QEventLoop()

        self.timer2 = QTimer()

        self.detail_account_info()
        self.detail_account_mystock()

        if not bool(self.buy_point_dict):
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
            self.logging.logger.info("new_chejan_slot order_status > %s" % order_status)
            self.buy_point_dict.update({self.customType.ORDER_STATUS: order_status})
            if order_status == self.customType.CONCLUSION:
                self.logging.logger.info(self.logType.CONCLUSION_ORDER_STATUS_LOG % (order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))
                self.line.notification(self.logType.CONCLUSION_ORDER_STATUS_LOG % (order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))
                
            # TODO 주문 체결 실패시... 대안 필요

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

            self.logging.logger.info("new_chejan_slot meme_gubun [%s]" % meme_gubun)
            if meme_gubun == '매도':
                if holding_quantity == 0:
                    self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], sCode)
                    self.buy_point_dict = {}
                    self.logging.logger.info("call loop_all_etf_stock at new_chejan_slot")
                    self.loop_all_etf_stock()
            else:
                self.buy_point_dict.update({self.customType.TOTAL_PURCHASE_PRICE: total_buy_price})
                self.buy_point_dict.update({self.customType.HOLDING_QUANTITY: holding_quantity})
                self.buy_point_dict.update({self.customType.PURCHASE_UNIT_PRICE: buy_price})
                self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.BALANCE})
                if "add_sell_std_price" not in self.buy_point_dict.keys():
                    self.buy_point_dict.update({"max_minus_std_price": get_minus_sell_std_price(buy_price)})
                    self.buy_point_dict.update({"add_sell_std_price": get_minus_sell_std_price(buy_price, 0.2)})
                    self.buy_point_dict.update({"max_plus_std_price": get_max_plus_sell_std_price(buy_price)})

    def buy_stock_real_reg(self, stock_dict):
        self.logging.logger.info("buy_stock_real_reg")
        screen_num = stock_dict[self.customType.SCREEN_NUMBER]
        fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, stock_dict[self.customType.STOCK_CODE], fids, "0")

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)

                if bool(self.buy_point_dict):
                    self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], self.buy_point_dict[self.customType.STOCK_CODE])
                    self.sell_send_order_market_off_time(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

                self.line.notification("시스템 종료")
                sys.exit()

        elif sRealType == self.customType.STOCK_CONCLUSION:
            if bool(self.buy_point_dict) and self.customType.ORDER_STATUS in self.buy_point_dict.keys() and self.buy_point_dict[self.customType.ORDER_STATUS] == self.customType.BALANCE:
                self.comm_real_data(sCode, sRealType, sRealData)
                # createAnalysisEtfFile(sCode, self.total_cal_target_etf_stock_dict[sCode], self.analysis_etf_file_path)
                code = self.buy_point_dict[self.customType.STOCK_CODE]

                if sCode == code and sCode in self.total_cal_target_etf_stock_dict.keys():
                    current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
                    if current_stock_price <= self.buy_point_dict["max_minus_std_price"]:
                        self.logging.logger.info("sell_send_order max_minus_std_price >> %s / %s" % (current_stock_price, self.buy_point_dict["max_minus_std_price"]))
                        self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

                    if current_stock_price <= self.buy_point_dict["add_sell_std_price"]:
                        self.logging.logger.info("add_sell_std_price >> %s / %s" % (current_stock_price, self.buy_point_dict["add_sell_std_price"]))
                        self.buy_point_dict.update({"add_sell_std_price": 0})
                        self.add_send_order(sCode, current_stock_price)

                    if current_stock_price >= self.buy_point_dict["max_plus_std_price"]:
                        self.logging.logger.info("sell_send_order max_plus_std_price >> %s / %s" % (current_stock_price, self.buy_point_dict["max_plus_std_price"]))
                        self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

                    if current_stock_price < self.buy_point_dict[self.customType.SELL_STD_HIGHEST_PRICE]:
                        half_plus_price = get_plus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], self.buy_point_dict[self.customType.SELL_STD_HIGHEST_PRICE])
                        if current_stock_price <= half_plus_price:
                            if get_max_plus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], 0.25) < current_stock_price:
                                self.logging.logger.info("sell_send_order second best case >> %s / %s" % (current_stock_price, half_plus_price))
                                self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

            elif bool(self.buy_point_dict) and self.customType.ORDER_STATUS in self.buy_point_dict.keys() and self.buy_point_dict[self.customType.ORDER_STATUS] == self.customType.NEW_PURCHASE:
                self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.RECEIPT})
                self.comm_real_data(sCode, sRealType, sRealData)
                code = self.buy_point_dict[self.customType.STOCK_CODE]

                if sCode == code and sCode in self.total_cal_target_etf_stock_dict.keys():
                    limit_stock_price = int(self.buy_point_dict[self.customType.CURRENT_PRICE])
                    current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
                    if limit_stock_price > current_stock_price:
                        limit_stock_price = current_stock_price
                    self.add_send_order(self.buy_point_dict[self.customType.STOCK_CODE], limit_stock_price)

    def comm_real_data(self, sCode, sRealType, sRealData):
        b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
        b = abs(int(b.strip()))
        e = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.SELLING_QUOTE])
        e = abs(int(e.strip()))
        a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.TIGHTENING_TIME])

        c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.THE_DAY_BEFORE])
        c = abs(int(c.strip()))

        d = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.FLUCTUATION_RATE])
        d = float(d.strip())

        f = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.BID])
        f = abs(int(f.strip()))

        g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.VOLUME])
        g = abs(int(g.strip()))

        h = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CUMULATIVE_VOLUME])
        h = abs(int(h.strip()))

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
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.THE_DAY_BEFORE: c})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELLING_QUOTE: e})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.BID: f})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.VOLUME: g})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CUMULATIVE_VOLUME: h})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.HIGHEST_PRICE: i})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.START_PRICE: j})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.LOWEST_PRICE: k})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_START_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.START_PRICE]})

        current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        if self.customType.SELL_STD_HIGHEST_PRICE in self.total_cal_target_etf_stock_dict[sCode]:
            if current_stock_price > self.total_cal_target_etf_stock_dict[sCode][self.customType.SELL_STD_HIGHEST_PRICE]:
                self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
        else:
            self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
        self.buy_point_dict.update({self.customType.SELL_STD_HIGHEST_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.SELL_STD_HIGHEST_PRICE]})

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
            if total_chegual_price > self.use_money:
                self.buy_point_dict.update({"add_sell_std_price": 0})
            else:
                self.buy_point_dict.update({"add_sell_std_price": get_minus_sell_std_price(buy_price, 0.2)})
            self.buy_point_dict.update({"max_minus_std_price": get_minus_sell_std_price(buy_price)})
            self.buy_point_dict.update({"max_plus_std_price": get_max_plus_sell_std_price(buy_price)})
            self.buy_point_dict.update({self.customType.SELL_STD_HIGHEST_PRICE: buy_price})
            self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.BALANCE})
            self.screen_number_setting(self.buy_point_dict)

        self.stop_screen_cancel(self.screen_my_info)
        self.detail_account_info_event_loop.exit()
        if bool(self.buy_point_dict):
            self.buy_stock_real_reg(self.buy_point_dict)

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
        self.tr_opt10079_info(code)

    def tr_opt10079_info(self, code, sPrevNext="0"):
        self.logging.logger.info('tr_opt10079_info > [%s]' % code)
        tic = "120틱"
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

    def loop_all_etf_stock(self):
        self.logging.logger.info('loop_all_etf_stock')
        self.timer2 = default_q_timer_setting()
        self.timer2.timeout.connect(self.prepare_all_etf_stock)

    def prepare_all_etf_stock(self):
        self.logging.logger.info('prepare_all_etf_stock')
        self.all_etf_stock_list = []
        self.total_cal_target_etf_stock_dict = {}
        self.get_all_etf_stock()
        self.top_rank_etf_stock_list = get_top_rank_etf_stock(self.all_etf_stock_list, self.customType.VOLUME, 5)
        self.top_rank_etf_stock_list = [x for x in self.top_rank_etf_stock_list if x[self.customType.STOCK_CODE] != '114800']
        self.logging.logger.info('top_rank_etf_stock_list %s' % self.top_rank_etf_stock_list)
        self.timer2.stop()

        self.loop_buy_search_etf()

    def loop_buy_search_etf(self):
        self.logging.logger.info('loop_buy_search_etf')
        self.timer2 = default_q_timer_setting()
        self.timer2.timeout.connect(self.buy_search_etf)

    def buy_search_etf(self):

        today = get_today_by_format('%Y%m%d')
        currentDate = get_today_by_format('%Y%m%d%H%M%S')

        if (today + '151000') < currentDate:
            self.timer2.stop()
            return

        self.logging.logger.info('buy_search_etf')
        self.get_next_stock_code()

        code = self.buy_search_stock_code
        self.logging.logger.info("top_rank_etf_stock_list loop > %s " % code)

        self.get_opt10079_info(code)
        create_moving_average_20_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20")

        first_buy_point = self.get_conform_first_buy_case(code)
        if bool(first_buy_point):
            self.logging.logger.info("first_buy_point break")
            self.prepare_send_order(code, first_buy_point)

        if not bool(first_buy_point):
            seconf_buy_point = self.get_conform_second_buy_case(code)
            if bool(seconf_buy_point):
                self.logging.logger.info("second_buy_point break")
                self.prepare_send_order(code, seconf_buy_point)

        self.logging.logger.info('buy_search_etf end')

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

    def init_search_info(self):
        self.timer2.stop()
        self.buy_search_stock_code = ''

    def prepare_send_order(self, code, buy_point):
        buy_point.update({self.customType.STOCK_CODE: code})
        buy_point.update({self.customType.ORDER_STATUS: self.customType.NEW_PURCHASE})
        self.logging.logger.info("buy_point > %s " % buy_point)
        self.buy_point_dict = copy.deepcopy(buy_point)
        self.screen_number_setting(self.buy_point_dict)
        self.init_search_info()
        self.buy_stock_real_reg(self.buy_point_dict)

    def add_send_order(self, code, limit_stock_price):
        self.logging.logger.info("[%s]add_send_order > %s " % (code, limit_stock_price))
        result = self.use_money / limit_stock_price
        quantity = int(result)
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.send_order_limit_stock_price(code, quantity, limit_stock_price, self.buy_point_dict)

    def get_conform_first_buy_case(self, code):
        self.logging.logger.info("first_buy_case analysis_rows > [%s]" % code)
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 5:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:5]
        self.logging.logger.info("analysis_rows > [%s] >> %s " % (code, analysis_rows))

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
                if first_tic["ma20"] >= secode_tic["ma20"] and first_tic[self.customType.CURRENT_PRICE] - secode_tic[self.customType.CURRENT_PRICE] <= get_etf_tic_price():
                    result = copy.deepcopy(first_tic)
                    result.update({"second": secode_tic[self.customType.CURRENT_PRICE]})
                    return result

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

        breaker = False

        if not breaker:
            second_tic = analysis_rows[1]
            if second_tic[self.customType.HIGHEST_PRICE] - second_tic[self.customType.LOWEST_PRICE] > 5:
                if second_tic[self.customType.LOWEST_PRICE] > second_tic["ma20"] and second_tic[self.customType.LOWEST_PRICE] - second_tic["ma20"] < 5:
                    pass
                else:
                    if second_tic[self.customType.LOWEST_PRICE] > second_tic["ma20"] or second_tic[self.customType.HIGHEST_PRICE] < second_tic["ma20"]:
                        breaker = True
                        self.logging.logger.info("second_tic range check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))

                if not breaker:
                    if second_tic[self.customType.CURRENT_PRICE] - second_tic[self.customType.START_PRICE] > 20:
                        self.logging.logger.info("second_tic big change check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                        breaker = True
                if not breaker:
                    if second_tic[self.customType.START_PRICE] > second_tic[self.customType.CURRENT_PRICE]:
                        self.logging.logger.info("second_tic white candle check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                        breaker = True

            else:
                third_tic = analysis_rows[2]
                if third_tic[self.customType.LOWEST_PRICE] > third_tic["ma20"] or second_tic[self.customType.HIGHEST_PRICE] < third_tic["ma20"]:
                    breaker = True
                    self.logging.logger.info("third_tic range check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))

                if not breaker:
                    if third_tic[self.customType.CURRENT_PRICE] - third_tic[self.customType.START_PRICE] > 20:
                        self.logging.logger.info("third_tic big change check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                        breaker = True

                if not breaker:
                    if third_tic[self.customType.START_PRICE] > third_tic[self.customType.CURRENT_PRICE]:
                        self.logging.logger.info("third_tic white candle check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                        breaker = True

        if not breaker:
            compare_rows = analysis_rows[2:]
            big_change_tic_list = [x for x in compare_rows if x[self.customType.CURRENT_PRICE] - x[self.customType.START_PRICE] > 15]
            if len(big_change_tic_list) == 0:
                self.logging.logger.info("big_change_tic_list check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                breaker = True

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
            elif first_tic[self.customType.CURRENT_PRICE] - second_tic[self.customType.CURRENT_PRICE] > get_etf_tic_price():
                self.logging.logger.info("first tic current_price by second_tic_last_price check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
                breaker = True

        if not breaker:
            result = copy.deepcopy(analysis_rows[0])
            second_tic = analysis_rows[1]
            result.update({"second": second_tic[self.customType.CURRENT_PRICE]})

            return result

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

    def sell_send_order(self, sCode, screen_number, quantity):
        self.logging.logger.info("sell_send_order > %s / %s" % (sCode, quantity))
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, screen_number, self.account_num, 2, sCode, quantity, 0, self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_PRICE],
             ""]
        )
        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_SELL_SUCCESS_LOG % sCode)
        else:
            self.logging.logger.info(self.logType.ORDER_SELL_FAIL_LOG % sCode)

    def sell_send_order_market_off_time(self, sCode, screen_number, quantity):
        self.logging.logger.info("sell_send_order_market_off_time > %s / %s" % (sCode, quantity))
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, screen_number, self.account_num, 2, sCode, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_OFF_TIME_LAST_PRICE],
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
        self.OnReceiveRealData.connect(self.realdata_slot)
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
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TAXATION_TYPE, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.COMPARED_TO_NAV, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MANAGER, "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40004, "opt40004", sPrevNext, self.screen_all_etf_stock)
        self.all_etf_info_event_loop.exec_()

    def detail_account_info(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)
        self.detail_account_info_event_loop.exec_()
