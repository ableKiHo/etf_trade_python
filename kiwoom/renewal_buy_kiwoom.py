import sys

from PyQt5.QtCore import *
from pandas import np

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
        self.buy_search_stock_name = ''
        self.total_cal_target_etf_stock_dict = {}
        # self.nav_buy_point_dict = {}
        # self.nav_buy_dict = {}
        # self.search_end = False
        self.add_buy_etf_flag = False

        self.buy_screen_meme_stock = "3000"
        self.buy_screen_real_stock = "6000"
        self.screen_opt10079_info = "7000"
        self.screen_opt10080_info = "7010"
        self.screen_all_etf_stock = "8000"
        self.screen_etf_stock = "5000"

        self.today = get_today_by_format('%Y%m%d')

        self.event_slots()
        self.real_event_slot()

        self.line.notification("ETF RENEWAL BUY TRADE START")
        self.tr_opt10079_info_event_loop = QEventLoop()
        self.tr_opt10080_info_event_loop = QEventLoop()
        self.all_etf_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop = QEventLoop()
        self.not_account_info_event_loop = QEventLoop()

        self.timer2 = QTimer()

        self.detail_account_info()
        self.detail_account_mystock()

        if not bool(self.buy_point_dict):
            self.loop_not_concluded_account()

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

            if order_status == self.customType.CONCLUSION:
                self.logging.logger.info(self.logType.CONCLUSION_ORDER_STATUS_LOG % (order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))
                self.line.notification(self.logType.CONCLUSION_ORDER_STATUS_LOG % (order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))
            else:
                if bool(self.buy_point_dict) and self.add_buy_etf_flag is True and order_gubun == "매수":
                    self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.BALANCE})

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
            if meme_gubun == self.customType.SELL:
                if holding_quantity == 0:
                    self.logging.logger.info("call loop_all_etf_stock at new_chejan_slot")
                    self.prepare_loop_all_etf_stock(sCode)
            else:
                self.total_cal_target_etf_stock_dict = {}
                self.buy_point_dict.update({self.customType.TOTAL_PURCHASE_PRICE: total_buy_price})
                self.buy_point_dict.update({self.customType.HOLDING_QUANTITY: holding_quantity})
                self.buy_point_dict.update({self.customType.PURCHASE_UNIT_PRICE: buy_price})
                self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.BALANCE})
                if self.add_buy_etf_flag is not True:
                    self.buy_point_dict.update({"max_minus_std_price": get_minus_sell_std_price(buy_price)})
                    self.buy_point_dict.update({"add_sell_std_price": get_minus_sell_std_price(buy_price, 0.2)})
                    self.buy_point_dict.update({"max_plus_std_price": get_max_plus_sell_std_price(buy_price)})

    def prepare_loop_all_etf_stock(self, code):
        self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], code)
        self.buy_point_dict = {}
        self.total_cal_target_etf_stock_dict = {}
        self.add_buy_etf_flag = False
        self.logging.logger.info("call loop_all_etf_stock at prepare_loop_all_etf_stock")
        self.loop_not_concluded_account()

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

                # if bool(self.buy_point_dict):
                #     self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], self.buy_point_dict[self.customType.STOCK_CODE])
                #     self.sell_send_order_market_off_time(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
                # elif bool(self.nav_buy_dict): self.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL") quantity = self.use_money / self.nav_buy_dict[self.customType.CURRENT_PRICE] if
                # quantity > 1: self.logging.logger.info("nav gap buy info > [%s] / current:%s / nav:%s" % (self.nav_buy_dict[self.customType.STOCK_CODE], self.nav_buy_dict[
                # self.customType.CURRENT_PRICE], self.nav_buy_dict["NAV"])) self.buy_send_order_market_off_time(sCode, self.nav_buy_dict[self.customType.MEME_SCREEN_NUMBER], quantity)

                self.loop_call_exit()

        elif sRealType == self.customType.STOCK_CONCLUSION:
            if bool(self.buy_point_dict) and self.customType.ORDER_STATUS in self.buy_point_dict.keys() and self.buy_point_dict[self.customType.ORDER_STATUS] == self.customType.BALANCE:

                self.comm_real_data(sCode, sRealType, sRealData)
                # createAnalysisEtfFile(sCode, self.total_cal_target_etf_stock_dict[sCode], self.analysis_etf_file_path)
                code = self.buy_point_dict[self.customType.STOCK_CODE]

                if sCode == code and sCode in self.total_cal_target_etf_stock_dict.keys():
                    current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
                    currentDate = get_today_by_format('%Y%m%d%H%M%S')
                    if (self.today + '160000') < currentDate:
                        self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.SELL_RECEPIT})
                        self.logging.logger.info("sell_send_order market off time >> %s / %s" % (current_stock_price, currentDate))
                        self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

                    if current_stock_price <= self.buy_point_dict["max_minus_std_price"]:
                        self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.SELL_RECEPIT})
                        self.logging.logger.info("sell_send_order max_minus_std_price >> %s / %s" % (current_stock_price, self.buy_point_dict["max_minus_std_price"]))
                        self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

                    if current_stock_price <= self.buy_point_dict["add_sell_std_price"] and self.add_buy_etf_flag is not True:
                        if self.buy_point_dict[self.customType.TOTAL_PURCHASE_PRICE] <= self.use_money:
                            self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.BALANCE})
                            self.logging.logger.info("add_sell_std_price >> %s / %s" % (current_stock_price, self.buy_point_dict["add_sell_std_price"]))
                            self.buy_point_dict.update({"add_sell_std_price": 0})
                            self.add_buy_etf_flag = True
                            self.add_send_order(sCode, current_stock_price)

                    if current_stock_price >= self.buy_point_dict["max_plus_std_price"]:
                        self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.SELL_RECEPIT})
                        self.logging.logger.info("sell_send_order max_plus_std_price >> %s / %s" % (current_stock_price, self.buy_point_dict["max_plus_std_price"]))
                        self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

                    if get_max_plus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], 0.25) < self.buy_point_dict[self.customType.SELL_STD_HIGHEST_PRICE]:
                        half_plus_price = get_plus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], self.buy_point_dict[self.customType.SELL_STD_HIGHEST_PRICE])
                        if current_stock_price <= half_plus_price:
                            if get_max_plus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], 0.15) < current_stock_price:
                                self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.SELL_RECEPIT})
                                self.logging.logger.info("sell_send_order second best case >> %s / %s" % (current_stock_price, half_plus_price))
                                self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
                        elif len(self.buy_point_dict[self.customType.TIC_120_PRICE]) >= 18:
                            self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.SELL_RECEPIT})
                            self.logging.logger.info("sell_send_order not change highest price until 120 * 18 >> %s" % current_stock_price)
                            self.sell_send_order(sCode, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

            elif bool(self.buy_point_dict) and self.customType.ORDER_STATUS in self.buy_point_dict.keys() and self.buy_point_dict[self.customType.ORDER_STATUS] == self.customType.NEW_PURCHASE:
                self.buy_point_dict.update({self.customType.ORDER_STATUS: self.customType.BUY_RECEIPT})
                self.comm_real_data(sCode, sRealType, sRealData)
                code = self.buy_point_dict[self.customType.STOCK_CODE]

                if sCode == code and sCode in self.total_cal_target_etf_stock_dict.keys():
                    limit_stock_price = int(self.buy_point_dict[self.customType.CURRENT_PRICE])
                    current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
                    start_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.START_PRICE]
                    max_start_stock_price = get_max_plus_sell_std_price(start_stock_price, 1)
                    if current_stock_price <= max_start_stock_price:
                        if limit_stock_price > current_stock_price:
                            limit_stock_price = current_stock_price
                        self.add_send_order(self.buy_point_dict[self.customType.STOCK_CODE], limit_stock_price)
                    else:
                        self.logging.logger.info("call loop_all_etf_stock at max current price(1 per over) %s / %s" % (current_stock_price, max_start_stock_price))
                        if limit_stock_price > current_stock_price:
                            limit_stock_price = current_stock_price
                        self.add_send_order(self.buy_point_dict[self.customType.STOCK_CODE], limit_stock_price, half_flag=True)

        # elif sRealType == "ETF NAV" and self.search_end:
        #     current_price = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
        #     current_price = abs(int(current_price.strip()))
        #
        #     nav = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]["NAV"])
        #     nav = abs(float(nav.strip()))
        #     nav_gap = nav - current_price
        #     if nav_gap > 100:
        #
        #         if "nav_gap" not in self.nav_buy_dict.keys() or ("nav_gap" in self.nav_buy_dict.keys() and self.nav_buy_dict["nav_gap"] < nav_gap):
        #             self.nav_buy_dict.update({"nav_gap": nav_gap})
        #             self.nav_buy_dict.update({self.customType.STOCK_CODE: sCode})
        #             self.nav_buy_dict.update({self.customType.CURRENT_PRICE: current_price})
        #             self.nav_buy_dict.update({"NAV": nav})

    def comm_real_data(self, sCode, sRealType, sRealData):
        b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])
        b = abs(int(b.strip()))
        a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.TIGHTENING_TIME])

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

        current_price_list = []
        tic_price_list = []

        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.TIGHTENING_TIME: a})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE: b})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.VOLUME: g})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.HIGHEST_PRICE: i})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.START_PRICE: j})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.LOWEST_PRICE: k})

        if self.customType.TIC_120_PRICE in self.total_cal_target_etf_stock_dict[sCode]:
            tic_price_list = self.total_cal_target_etf_stock_dict[sCode][self.customType.TIC_120_PRICE]
        else:
            self.total_cal_target_etf_stock_dict[sCode].update({self.customType.TIC_120_PRICE: tic_price_list})

        if self.customType.CURRENT_PRICE_LIST in self.total_cal_target_etf_stock_dict[sCode]:
            current_price_list = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE_LIST]
            current_price_list.insert(0, b)
            if len(current_price_list) >= 120:
                if len(tic_price_list) > 0:
                    tic_price_list.insert(0, np.mean(current_price_list))
                else:
                    tic_price_list.append(np.mean(current_price_list))
                current_price_list.clear()
        else:
            current_price_list.append(b)
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE_LIST: current_price_list})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.TIC_120_PRICE: tic_price_list})

        current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        if self.customType.SELL_STD_HIGHEST_PRICE in self.total_cal_target_etf_stock_dict[sCode]:
            if current_stock_price > self.total_cal_target_etf_stock_dict[sCode][self.customType.SELL_STD_HIGHEST_PRICE]:
                self.logging.logger.info("changed sell std highest price >> %s" % current_stock_price)
                self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
                self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE_LIST: []})
                self.total_cal_target_etf_stock_dict[sCode].update({self.customType.TIC_120_PRICE: []})
        else:
            self.total_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
        self.buy_point_dict.update({self.customType.SELL_STD_HIGHEST_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.SELL_STD_HIGHEST_PRICE]})
        self.buy_point_dict.update({self.customType.TIC_120_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.TIC_120_PRICE]})

    def trdata_slot_opw00018(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
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
                self.add_buy_etf_flag = True
                self.buy_point_dict.update({"add_sell_std_price": 0})
            else:
                self.add_buy_etf_flag = False
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
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", tic)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10079", "opt10079", sPrevNext, self.screen_opt10079_info)

        self.tr_opt10079_info_event_loop.exec_()

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

        self.stop_screen_cancel(self.screen_opt10079_info)
        self.tr_opt10079_info_event_loop.exit()

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

    def trdata_slot_opt10075(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(rows):
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_CODE)
            order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.ORDER_NO)
            order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.ORDER_CLASSIFICATION)

            code = code.strip()
            order_no = int(order_no.strip())
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            if order_gubun == "매수":
                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    [self.customType.BUY_CANCLE, self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.account_num, 3, code, 0, 0,
                     self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], order_no]
                )

                if order_success == 0:
                    self.logging.logger.debug(self.logType.CANCLE_ORDER_BUY_SUCCESS_LOG)
                else:
                    self.logging.logger.debug(self.logType.CANCLE_ORDER_BUY_FAIL_LOG)

        self.not_account_info_event_loop.exit()

    def loop_call_exit(self):
        self.timer2 = default_q_timer_setting()
        self.timer2.timeout.connect(self.call_exit)

    def call_exit(self):
        currentDate = get_today_by_format('%Y%m%d%H%M%S')
        if (self.today + '153400') > currentDate:
            if bool(self.buy_point_dict):
                self.sell_send_order_market_off_time(self.buy_point_dict[self.customType.STOCK_CODE], self.buy_point_dict[self.customType.MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])

        if (self.today + '160000') < currentDate:
            self.logging.logger.info("시스템 종료")
            self.timer2.stop()
            sys.exit()

    def loop_not_concluded_account(self):
        self.logging.logger.info('loop_not_concluded_account')
        self.timer2 = default_q_timer_setting()
        self.timer2.timeout.connect(self.prepare_not_concluded_account)

    def prepare_not_concluded_account(self):
        self.not_concluded_account()
        self.timer2.stop()

        self.loop_all_etf_stock()

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

        currentDate = get_today_by_format('%Y%m%d%H%M%S')

        if (self.today + '150500') < currentDate:
            self.timer2.stop()
            self.buy_search_stock_code = ''
            self.analysis_etf_target_dict = {}
            self.total_cal_target_etf_stock_dict = {}
            self.buy_point_dict = {}
            if not self.weekend.isFriday:
                self.loop_last_price_buy_all_etf_stock()
            # self.get_max_nav_stock_code()
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
            return

        if not bool(first_buy_point):
            seconf_buy_point = self.get_conform_second_buy_case(code)
            if bool(seconf_buy_point):
                self.logging.logger.info("second_buy_point break")
                self.prepare_send_order(code, seconf_buy_point)
                return

        self.logging.logger.info('buy_search_etf end')

    def loop_last_price_buy_all_etf_stock(self):
        self.logging.logger.info('loop_last_price_buy_all_etf_stock')
        self.timer2 = default_q_timer_setting()
        self.timer2.timeout.connect(self.prepare_last_price_buy_all_etf_stock)

    def prepare_last_price_buy_all_etf_stock(self):
        self.logging.logger.info('prepare_last_price_buy_all_etf_stock')
        self.all_etf_stock_list = []
        self.total_cal_target_etf_stock_dict = {}
        self.get_all_etf_stock()
        self.top_rank_etf_stock_list = get_top_rank_etf_stock(self.all_etf_stock_list, self.customType.VOLUME, 20)
        self.top_rank_etf_stock_list = [x for x in self.top_rank_etf_stock_list if x.find(self.customType.LEVERAGE) < 0 and x.find(self.customType.INVERSE) < 0]
        self.logging.logger.info('top_rank_etf_stock_list %s' % self.top_rank_etf_stock_list)
        self.timer2.stop()

        self.loop_last_price_buy_search_etf()

    def loop_last_price_buy_search_etf(self):
        self.logging.logger.info('loop_last_price_buy_search_etf')
        self.timer2 = default_q_timer_setting()
        self.timer2.timeout.connect(self.buy_search_last_price_etf)

    def buy_search_last_price_etf(self):
        self.get_next_stock_code()

        code = self.buy_search_stock_code
        self.logging.logger.info("top_rank_etf_stock_list loop > %s " % code)

        self.get_opt10080_info(code)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma20", 20)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma5", 5)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma10", 10)
        create_moving_average_gap_line(code, self.analysis_etf_target_dict, "row", self.customType.CURRENT_PRICE, "ma60", 60)

        last_price_buy_point = self.get_conform_last_price_buy_case(code)
        if bool(last_price_buy_point):
            self.timer2.stop()
            self.logging.logger.info("last_price_buy_point break")
            self.market_price_send_order(self.code, last_price_buy_point[self.customType.CURRENT_PRICE])
            return
        self.logging.logger.info('last_price_buy_search_etf end')

    def get_next_stock_code(self, max_index=4):
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
        self.buy_search_stock_name = item[self.customType.STOCK_NAME]

    def init_search_info(self):
        self.timer2.stop()
        self.buy_search_stock_code = ''
        self.buy_search_stock_name = ''

    def prepare_send_order(self, code, buy_point):
        buy_point.update({self.customType.STOCK_CODE: code})
        buy_point.update({self.customType.ORDER_STATUS: self.customType.NEW_PURCHASE})
        self.logging.logger.info("buy_point > %s " % buy_point)
        self.buy_point_dict = copy.deepcopy(buy_point)
        self.screen_number_setting(self.buy_point_dict)
        self.init_search_info()
        self.buy_stock_real_reg(self.buy_point_dict)

    def add_send_order(self, code, limit_stock_price, half_flag=False):
        self.logging.logger.info("[%s]add_send_order > %s " % (code, limit_stock_price))
        result = self.use_money / limit_stock_price
        quantity = int(result)
        if half_flag is True:
            quantity = math.trunc(quantity / 2)
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.send_order_limit_stock_price(code, quantity, limit_stock_price, self.buy_point_dict)

    def market_price_send_order(self, code, limit_stock_price):
        self.logging.logger.info("[%s]add_send_order > %s " % (code, limit_stock_price))
        result = self.use_money / limit_stock_price
        quantity = int(result)
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.send_order_market_price_stock_price(code, quantity, self.buy_point_dict)

    def get_conform_last_price_buy_case(self, code):
        self.logging.logger.info("get_conform_last_price_buy_case analysis_rows > [%s]" % code)
        rows = self.analysis_etf_target_dict[code]["row"]

        if len(rows) < 7:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:7]
        self.logging.logger.info("analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]
        if first_tic[self.customType.TIGHTENING_TIME] != '151800':
            self.logging.logger.info("time check > [%s] >> %s " % (code, first_tic[self.customType.TIGHTENING_TIME]))
            return {}

        if first_tic["ma20"] > first_tic[self.customType.CURRENT_PRICE] or first_tic["ma5"] > first_tic[self.customType.CURRENT_PRICE] or first_tic["ma10"] > first_tic[
            self.customType.CURRENT_PRICE] or first_tic["ma60"] > first_tic[self.customType.CURRENT_PRICE]:
            self.logging.logger.info("first_tic current_price check > [%s] >> %s " % (code, first_tic))
            return {}

        empty_gap_list = [x for x in analysis_rows if x["ma20"] == '' or x["ma5"] == '' or x["ma10"] == '' or x["ma60"] == '']
        if len(empty_gap_list) > 0:
            self.logging.logger.info("empty_ma20_list > [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], empty_gap_list))
            return {}

        compare_rows = analysis_rows[1:]
        lower_gap_list = [x for x in compare_rows if
                          x["ma20"] > x[self.customType.CURRENT_PRICE] or x["ma5"] > x[self.customType.CURRENT_PRICE] or x["ma10"] > x[self.customType.CURRENT_PRICE] or x["ma60"] > x[
                              self.customType.CURRENT_PRICE]]
        if len(empty_gap_list) > 0:
            self.logging.logger.info("lower_gap_list check> [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], lower_gap_list))
            return {}

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
            max_change_limit = 15
            if self.buy_search_stock_name.find("인버스2X") >= 0:
                max_change_limit = 5
            big_change_tic_list = [x for x in compare_rows if x[self.customType.CURRENT_PRICE] - x[self.customType.START_PRICE] > max_change_limit]
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

    def send_order_market_price_stock_price(self, code, quantity, stock_dict):
        self.logging.logger.info("send_order_market_price_stock_price > %s / %s" % (code, stock_dict))
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, stock_dict[self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, code, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_PRICE], ""])

        if order_success == 0:
            self.logging.logger.info(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity))
            self.line.notification(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity))
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

    def buy_send_order_market_off_time(self, sCode, screen_number, quantity):
        self.logging.logger.info("buy_send_order_market_off_time > %s " % sCode)
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, screen_number, self.account_num, 2, sCode, quantity, 0,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_OFF_TIME_LAST_PRICE],
             ""]
        )
        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_BUY_SUCCESS_LOG % sCode)
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG % sCode)

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

    def not_concluded_account(self, sPrevNext="0"):
        self.logging.logger.info("not_concluded_account")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_etf_stock)

        self.not_account_info_event_loop.exec_()

    def screen_number_setting(self, stock_dict):
        stock_dict.update({self.customType.SCREEN_NUMBER: self.buy_screen_real_stock})
        stock_dict.update({self.customType.MEME_SCREEN_NUMBER: self.buy_screen_meme_stock})

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info('trdata_slot %s / %s' % (sRQName, sPrevNext))
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10079":
            self.trdata_slot_opt10079(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10080":
            self.trdata_slot_opt10080(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT40004:
            self.trdata_slot_opt40004(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPW00018:
            self.trdata_slot_opw00018(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "실시간미체결요청":
            self.trdata_slot_opt10075(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

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
