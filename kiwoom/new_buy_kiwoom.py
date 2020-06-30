import copy
import os
import sys

from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom


class NewBuyKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF New BuyKiwoom() class start.")
        self.line.notification("ETF New BuyKiwoom() class start.")

        self.analysis_etf_file_path = self.property.analysisEtfFilePath
        self.sell_analysis_etf_file_path = self.property.sellAnalysisEtfFIlePath

        self.priority_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(레버리지, 인버스용)
        self.priority_portfolio_stock_dict = {}  # 실시간 조회 등록용
        self.second_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(일반)
        self.second_portfolio_stock_dict = {}  # 실시간 조회 등록용

        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린 번호
        self.buy_screen_meme_stock = "3000"  # 종목별 할당할 주문용 스크린 번호
        self.buy_screen_real_stock = "6000"  # 종별별 할당할 스크린 번호
        self.sell_screen_meme_stock = "4000"
        self.screen_etf_stock = "5000"

        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결

        self.line.notification("ETF BUY TRADE START")
        self.etf_info_event_loop = QEventLoop()

        self.detail_account_info()
        QTest.qWait(5000)
        self.read_target_etf_file()
        QTest.qWait(5000)
        self.get_etf_stock_info()
        QTest.qWait(5000)
        self.screen_number_setting(self.priority_portfolio_stock_dict)
        QTest.qWait(5000)
        self.screen_number_setting(self.second_portfolio_stock_dict)
        QTest.qWait(5000)

        # self.get_moving_average_line()

        #QTest.qWait(30000)

        # 실시간 수신 관련 함수
        self.logging.logger.info("priority_portfolio_stock_dict > %s" % self.priority_portfolio_stock_dict)
        self.logging.logger.info("second_portfolio_stock_dict > %s" % self.second_portfolio_stock_dict)
        """
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

        for code in self.priority_portfolio_stock_dict.keys():
            screen_num = self.priority_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

        for code in self.second_portfolio_stock_dict.keys():
            screen_num = self.second_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")
        """

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def screen_number_setting(self, stock_dict):
        self.logging.logger.info("screen_number_setting")
        screen_overwrite = []

        for code in stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린 번호 할당
        cnt = 0
        temp_screen = int(self.buy_screen_real_stock)
        meme_screen = int(self.buy_screen_meme_stock)
        sell_meme_screen = int(self.sell_screen_meme_stock)

        for code in screen_overwrite:

            if (cnt % 20) == 0:
                temp_screen = int(temp_screen) + 1
                temp_screen = str(temp_screen)

            if (cnt % 20) == 0:
                meme_screen = int(meme_screen) + 1
                meme_screen = str(meme_screen)

            if (cnt % 20) == 0:
                sell_meme_screen = int(sell_meme_screen) + 1
                sell_meme_screen = str(sell_meme_screen)

            if code in stock_dict.keys():
                stock_dict[code].update({self.customType.SCREEN_NUMBER: str(temp_screen)})
                stock_dict[code].update({self.customType.MEME_SCREEN_NUMBER: str(meme_screen)})
                stock_dict[code].update({self.customType.SELL_MEME_SCREEN_NUMBER: str(sell_meme_screen)})

            cnt += 1

        self.logging.logger.info(self.logType.PORTFOLIO_STOCK_DICT_LOG % stock_dict)

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def detail_account_info(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_info1 %s / %s" % (self.account_num, self.account_pw))
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)
        self.logging.logger.info("detail_account_info2")
        self.detail_account_info_event_loop.exec_()

    def trdata_slot_opw00001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info("trdata_slot_opw00001")
        deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.DEPOSIT)
        self.deposit = int(deposit)
        buy_possible_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.AVAILABLE_AMOUNT)
        self.buy_possible_deposit = int(buy_possible_deposit)

        self.logging.logger.info(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        self.line.notification(self.logType.BUY_POSSIBLE_DEPOSIT_LOG % self.buy_possible_deposit)
        #  모든 예수금을 하나의 종목을 매수하는데 사용하지 않아야 하므로 사용할 비율 지정
        use_money = float(self.buy_possible_deposit) * self.use_money_percent
        self.use_money = int(use_money)
        self.purchased_deposit = int(use_money)
        #  한 종목을 매수할 떄 모든 돈을 다 쓰면 안되므로 3종목 매수할 수 있게 나눔
        self.use_money = self.use_money / self.max_sell_stock_count

        self.stop_screen_cancel(self.screen_my_info)
        self.detail_account_info_event_loop.exit()
        self.logging.logger.info(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)
        self.line.notification(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)

    def read_target_etf_file(self):
        self.logging.logger.info("전일자 대상건 파일 처리 시작")
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
                    last_stock_price = ls[4]
                    avg_the_day_before_price = ls[5]
                    max_the_day_before_price = ls[6]
                    min_the_day_before_price = ls[7].rstrip('\n')

                    if stock_name.find("레버리지") >= 0 or stock_name.find("인버스") >= 0:
                        self.priority_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                     self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                     self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                     self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                     self.customType.THE_DAY_BEFORE_AVG: avg_the_day_before_price,
                                                                                     self.customType.THE_DAY_BEFORE_MAX: max_the_day_before_price,
                                                                                     self.customType.THE_DAY_BEFORE_MIN: min_the_day_before_price,
                                                                                     self.customType.START_PRICE: '',
                                                                                     self.customType.GOAL_PRICE: ''}})
                    else:
                        self.second_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                   self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                   self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                   self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                   self.customType.THE_DAY_BEFORE_AVG: avg_the_day_before_price,
                                                                                   self.customType.THE_DAY_BEFORE_MAX: max_the_day_before_price,
                                                                                   self.customType.THE_DAY_BEFORE_MIN: min_the_day_before_price,
                                                                                   self.customType.START_PRICE: '',
                                                                                   self.customType.GOAL_PRICE: ''}})
            f.close()
            self.logging.logger.info("전일자 대상건 파일 처리 완료")
            self.logging.logger.info("레버리지, 인버스 %s" % self.priority_cal_target_etf_stock_dict)
            self.logging.logger.info("일반 %s" % self.second_cal_target_etf_stock_dict)

    def get_etf_stock_info(self):
        self.logging.logger.info("get_etf_stock_info")

        for sCode in self.priority_cal_target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

        for sCode in self.second_cal_target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.START_PRICE)
        start_price = abs(int(start_price.strip()))

        if code in self.priority_cal_target_etf_stock_dict.keys():
            self.priority_cal_target_etf_stock_dict[code].update({self.customType.CURRENT_START_PRICE: start_price})
            value = self.priority_cal_target_etf_stock_dict[code]
            goal_stock_price = self.cal_goal_stock_price(code=code, value=value)

            if goal_stock_price > 0:
                self.priority_cal_target_etf_stock_dict[code].update({self.customType.GOAL_PRICE: goal_stock_price})
                if code not in self.priority_portfolio_stock_dict.keys():
                    self.priority_portfolio_stock_dict.update({code: {}})
                self.priority_portfolio_stock_dict[code] = copy.deepcopy(self.priority_cal_target_etf_stock_dict[code])

        if code in self.second_cal_target_etf_stock_dict.keys():
            self.second_cal_target_etf_stock_dict[code].update({self.customType.CURRENT_START_PRICE: start_price})
            value = self.second_cal_target_etf_stock_dict[code]
            goal_stock_price = self.cal_goal_stock_price(code=code, value=value)

            if goal_stock_price > 0:
                self.second_cal_target_etf_stock_dict[code].update({self.customType.GOAL_PRICE: goal_stock_price})
                if code not in self.second_portfolio_stock_dict.keys():
                    self.second_portfolio_stock_dict.update({code: {}})
                self.second_portfolio_stock_dict[code] = copy.deepcopy(self.second_cal_target_etf_stock_dict[code])

        self.etf_info_event_loop.exit()

    def cal_goal_stock_price(self, code, value):
        start_stock_price = value[self.customType.CURRENT_START_PRICE]
        start_stock_price = int(start_stock_price)
        last_stock_price = value[self.customType.LAST_DAY_LAST_PRICE]
        last_stock_price = int(last_stock_price)
        highest_stock_price = value[self.customType.LAST_DAY_HIGHEST_PRICE]
        highest_stock_price = int(highest_stock_price)
        lowest_stock_price = value[self.customType.LAST_DAY_LOWEST_PRICE]
        lowest_stock_price = int(lowest_stock_price)

        if start_stock_price > last_stock_price:
            if (start_stock_price - last_stock_price) <= (highest_stock_price - lowest_stock_price):
                goal_stock_price = last_stock_price + (0.35 * (highest_stock_price - lowest_stock_price))
                goal_stock_price = round(goal_stock_price, 0)
            else:
                goal_stock_price = 0
        else:
            goal_stock_price = 0

        if goal_stock_price > 0:
            return goal_stock_price
        else:
            return 0

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)

                QTest.qWait(5000)
                self.line.notification("시스템 종료")
                sys.exit()