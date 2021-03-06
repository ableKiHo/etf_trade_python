import sys

from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom


class SellKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF SellKiwoom() class start.")
        self.line.notification("ETF SellKiwoom() class start.")

        self.sell_screen_meme_stock = "7000"
        self.sell_screen_real_stock = "8000"

        self.account_stock_dict = {}
        self.sell_portfolio_stock_dict = {}

        self.event_slots()
        self.real_event_slot()

        self.sellOwnEtfStock()

    def sellOwnEtfStock(self):
        self.line.notification("ETF AUTO SELL TRADE START")
        self.detail_account_mystock()
        QTest.qWait(10000)
        self.sell_screen_number_setting()
        QTest.qWait(5000)

        for sCode in self.sell_portfolio_stock_dict.keys():
            asd = self.account_stock_dict[sCode]
            QTest.qWait(1000)
            self.sell_send_order(sCode, self.sell_portfolio_stock_dict[sCode][self.customType.MEME_SCREEN_NUMBER], asd[self.customType.HOLDING_QUANTITY])

        QTest.qWait(60000)
        self.line.notification("ETF AUTO SELL TRADE END")
        QTest.qWait(5000)
        sys.exit()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def detail_account_mystock(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_mystock")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00018, "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPW00018:
            self.trdata_slot_opw00018(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opw00018(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.TOTAL_PURCHASE_AMOUNT)
        total_buy_money = int(total_buy_money)
        total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.TOTAL_VALUATION_GAIN_LOSS)
        total_profit_loss_money = int(total_profit_loss_money)
        total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.TOTAL_RETURN)
        total_profit_loss_rate = float(total_profit_loss_rate)

        self.logging.logger.info(self.logType.OPW00018_SUMMARY_LOG % (total_buy_money, total_profit_loss_money, total_profit_loss_rate))

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

            if code in self.account_stock_dict:
                pass
            else:
                self.account_stock_dict[code] = {}

            stock_quantity = int(stock_quantity.strip())
            buy_price = int(buy_price.strip())
            learn_rate = float(learn_rate.strip())
            current_price = int(current_price.strip())
            total_chegual_price = int(total_chegual_price.strip())
            possible_quantity = int(possible_quantity.strip())

            self.account_stock_dict[code].update({self.customType.STOCK_NAME: code_nm})
            self.account_stock_dict[code].update({self.customType.HOLDING_QUANTITY: stock_quantity})
            self.account_stock_dict[code].update({self.customType.PURCHASE_PRICE: buy_price})
            self.account_stock_dict[code].update({self.customType.YIELD: learn_rate})
            self.account_stock_dict[code].update({self.customType.CURRENT_PRICE: current_price})
            self.account_stock_dict[code].update({self.customType.PURCHASE_AMOUNT: total_chegual_price})
            self.account_stock_dict[code].update({self.customType.AMOUNT_OF_TRADING_AVAILABLE: possible_quantity})

            self.line.notification(self.logType.OWN_STOCK_LOG % self.account_stock_dict[code])

        self.logging.logger.info(self.logType.OWN_TOTAL_STOCK_LOG % rows)

        if sPrevNext == "2":
            self.detail_account_mystock(sPrevNext="2")
        else:
            self.stop_screen_cancel(self.screen_my_info)
            self.detail_account_info_event_loop.exit()

    def sell_screen_number_setting(self):
        self.logging.logger.info("sell_screen_number_setting")
        screen_overwrite = []

        for code in self.account_stock_dict.keys():
            screen_overwrite.append(code)

        cnt = 0
        temp_screen = int(self.sell_screen_real_stock)
        meme_screen = int(self.sell_screen_meme_stock)

        for code in screen_overwrite:

            if (cnt % 20) == 0:
                temp_screen = int(temp_screen) + 1
                temp_screen = str(temp_screen)

            if (cnt % 20) == 0:
                meme_screen = int(meme_screen) + 1
                meme_screen = str(meme_screen)

            if code in self.sell_portfolio_stock_dict.keys():
                self.sell_portfolio_stock_dict[code].update({self.customType.SCREEN_NUMBER: str(temp_screen)})
                self.sell_portfolio_stock_dict[code].update({self.customType.MEME_SCREEN_NUMBER: str(meme_screen)})
            elif code not in self.sell_portfolio_stock_dict.keys():
                self.sell_portfolio_stock_dict.update({code: {self.customType.SCREEN_NUMBER: str(temp_screen), self.customType.MEME_SCREEN_NUMBER: str(meme_screen)}})

            cnt += 1

        self.logging.logger.info(self.logType.SELL_PORTFOLIO_STOCK_DICT_LOG % self.sell_portfolio_stock_dict)

    def chejan_slot(self, sGubun, nItemCnt, sFidList):
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

            if sCode in self.priority_order_stock_dict.keys():
                self.priority_order_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price})

            if sCode in self.second_order_stock_dict.keys():
                self.second_order_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: buy_price})

            self.logging.logger.info(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))
            self.line.notification(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))

            if meme_gubun == '매도' and holding_quantity == 0:
                self.purchased_deposit = self.purchased_deposit + total_buy_price
                if sCode in self.priority_order_stock_dict.keys():
                    del self.priority_order_stock_dict[sCode]
                if sCode in self.second_order_stock_dict.keys():
                    del self.second_order_stock_dict[sCode]

    def sell_send_order(self, sCode, screen_number, quantity):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_STOCK_SELL, screen_number, self.account_num, 2, sCode, quantity, 0, self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.MARKET_PRICE], ""]
        )
        if order_success == 0:
            self.logging.logger.info(self.logType.ORDER_SELL_SUCCESS_LOG % sCode)
        else:
            self.logging.logger.info(self.logType.ORDER_SELL_FAIL_LOG % sCode)

        return order_success
