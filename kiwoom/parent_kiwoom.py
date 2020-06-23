import sys

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from config.customType import CustomType
from config.errorCode import errors
from config.kiwoomType import RealType
from config.lineNotify import LineNotify
from config.logType import LogType
from config.log_class import Logging
from config.property import Property
from kiwoom.weekend import Weekend


class ParentKiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        self.property = Property()
        self.realType = RealType()
        self.logging = Logging()
        self.line = LineNotify()
        self.customType = CustomType()
        self.logType = LogType()

        self.weekend = Weekend()

        if self.weekend.isWeekend:
            self.line.notification("ETF AUTO TRADE WEEKEND")
            QTest.qWait(5000)
            sys.exit()

        self.screen_my_info = "2000"  # 계좌 관련한 스크린 번호
        self.login_event_loop = QEventLoop()
        self.detail_account_info_event_loop = QEventLoop()  # 예수금 요청용 이벤트 루프

        self.target_etf_file_path = self.property.targetEtfFilePath
        self.account_num = self.property.account  # 계좌번호
        self.account_pw = self.property.accountPw

        self.get_ocx_instance()
        self.login_event_slots()
        self.signal_login_commconnect()

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenApiCtrl.1")

    def login_event_slots(self):
        self.OnEventConnect.connect(self.login_slot)

    def signal_login_commconnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def login_slot(self, err_code):
        login_status = errors(err_code)[1]
        self.logging.logger.info(login_status)
        self.line.notification("login > %s" % login_status)
        self.login_event_loop.exit()

    def stop_screen_cancel(self, sScrNo=None):
        self.logging.logger.info("stop_screen_cancel")
        self.dynamicCall("DisconnectRealData(QString)", sScrNo)

    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        self.logging.logger.info("스크린: %s, 요청이름: %s, tr코드: %s --- %s" % (sScrNo, sRQName, sTrCode, msg))

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
            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.HOLDING_QUANTITY])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.AVAILABLE_QUANTITY])
            like_quan = int(like_quan)
            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.PURCHASE_PRICE])
            buy_price = abs(int(buy_price))
            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.TOTAL_PURCHASE_PRICE])
            total_buy_price = int(total_buy_price)
            income_rate = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE[self.customType.BALANCE][self.customType.PROFIT_AND_LOSS])

            self.logging.logger.info(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, stock_quan, like_quan, buy_price, total_buy_price, income_rate))
            self.line.notification(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, stock_quan, like_quan, buy_price, total_buy_price, income_rate))
