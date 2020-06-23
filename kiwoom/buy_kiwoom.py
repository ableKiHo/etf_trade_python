import datetime
import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom


class BuyKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF BuyKiwoom() class start.")
        self.line.notification("ETF BuyKiwoom() class start.")

        self.analysis_etf_file_path = self.property.analysisEtfFilePath

        self.use_money = 0  # 실제 투자에 사용할 금액
        self.use_money_percent = 0.5  # 예수금에서 실제 사용할 비율
        self.deposit = 0  # 예수금
        self.buy_possible_deposit = 0  # 주문가능 금액
        self.purchased_deposit = 0  # 구매한 금액
        self.max_sell_stock_count = 3  # 일일 최대 구매 가능 종목 수

        self.priority_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(레버리지, 인버스용)
        self.second_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(일반)
        self.total_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(일반)
        self.total_portfolio_stock_dict = {}  # 실시간 조회 주식 정보 저장용(전체)
        self.priority_portfolio_stock_dict = {}  # 실시간 조회 주식 정보 저장용(레버리지, 인버스용)
        self.second_portfolio_stock_dict = {}  # 실시간 조회 주식 정보 저장용(일반)
        self.priority_order_stock_dict = {}  # 매수 주문 완료 저장용
        self.priority_not_order_stock_dict = {}  # 매수 주문 불가 저장용
        self.second_order_stock_dict = {}  # 매수 주문 완료 저장용
        self.second_not_order_stock_dict = {}  # 매수 주문 불가 저장용

        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린 번호
        self.buy_screen_meme_stock = "3000"  # 종목별 할당할 주문용 스크린 번호
        self.buy_screen_real_stock = "6000"  # 종별별 할당할 스크린 번호

        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결

        self.line.notification("ETF BUY TRADE START")
        self.detail_account_info()
        QTest.qWait(5000)
        self.read_target_etf_file()  # 대상 ETF(파일) 읽기
        QTest.qWait(10000)
        self.priority_screen_number_setting()
        self.second_screen_number_setting()

        QTest.qWait(5000)
        # 실시간 수신 관련 함수
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

        for code in self.priority_portfolio_stock_dict.keys():
            screen_num = self.priority_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)

    def detail_account_info(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_info")
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opw00001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
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
                    last_stock_price = ls[4].rstrip('\n')

                    if stock_name.find("레버리지") or stock_name.find("인버스"):
                        self.priority_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                     self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                     self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                     self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                     self.customType.GOAL_PRICE: ''}})
                    else:
                        self.second_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                   self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                   self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                   self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                   self.customType.GOAL_PRICE: ''}})

                    self.total_portfolio_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                   self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                   self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                   self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                   self.customType.GOAL_PRICE: ''}})
            f.close()
            self.logging.logger.info("전일자 대상건 파일 처리 완료")
            self.logging.logger.info("레버리지, 인버스 %s" % self.priority_cal_target_etf_stock_dict)
            self.logging.logger.info("일반 %s" % self.second_cal_target_etf_stock_dict)

    def priority_screen_number_setting(self):
        self.logging.logger.info("priority_screen_number_setting")
        screen_overwrite = []

        for code in self.priority_cal_target_etf_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린 번호 할당
        cnt = 0
        temp_screen = int(self.buy_screen_real_stock)
        meme_screen = int(self.buy_screen_meme_stock)

        for code in screen_overwrite:

            if (cnt % 20) == 0:
                temp_screen = int(temp_screen) + 1
                temp_screen = str(temp_screen)

            if (cnt % 20) == 0:
                meme_screen = int(meme_screen) + 1
                meme_screen = str(meme_screen)

            if code in self.priority_portfolio_stock_dict.keys():
                self.priority_portfolio_stock_dict[code].update({self.customType.SCREEN_NUMBER: str(temp_screen)})
                self.priority_portfolio_stock_dict[code].update({self.customType.MEME_SCREEN_NUMBER: str(meme_screen)})
            elif code not in self.priority_portfolio_stock_dict.keys():
                self.priority_portfolio_stock_dict.update({code: {self.customType.SCREEN_NUMBER: str(temp_screen), self.customType.MEME_SCREEN_NUMBER: str(meme_screen)}})

            cnt += 1

        self.logging.logger.info(self.logType.PRIORITY_PORTFOLIO_STOCK_DICT_LOG % self.priority_portfolio_stock_dict)

    def second_screen_number_setting(self):
        self.logging.logger.info("second_screen_number_setting")
        screen_overwrite = []

        for code in self.second_cal_target_etf_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린 번호 할당
        cnt = 0
        temp_screen = int(self.buy_screen_real_stock)
        meme_screen = int(self.buy_screen_meme_stock)

        for code in screen_overwrite:

            if (cnt % 20) == 0:
                temp_screen = int(temp_screen) + 1
                temp_screen = str(temp_screen)

            if (cnt % 20) == 0:
                meme_screen = int(meme_screen) + 1
                meme_screen = str(meme_screen)

            if code in self.second_portfolio_stock_dict.keys():
                self.second_portfolio_stock_dict[code].update({self.customType.SCREEN_NUMBER: str(temp_screen)})
                self.second_portfolio_stock_dict[code].update({self.customType.MEME_SCREEN_NUMBER: str(meme_screen)})
            elif code not in self.second_portfolio_stock_dict.keys():
                self.second_portfolio_stock_dict.update({code: {self.customType.SCREEN_NUMBER: str(temp_screen), self.customType.MEME_SCREEN_NUMBER: str(meme_screen)}})

            cnt += 1

        self.logging.logger.info(self.logType.SECOND_PORTFOLIO_STOCK_DICT_LOG % self.second_portfolio_stock_dict)

    def secondPortfolioStockRealReg(self):
        for code in self.second_portfolio_stock_dict.keys():
            screen_num = self.second_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def isGoalStockPriceRange(self, goalStockPrice, currentStockPrice):
        rangePercentage = 1.5
        maxPrice = goalStockPrice + round(goalStockPrice * (rangePercentage / 100))
        return currentStockPrice <= maxPrice

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]  # (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)

                for code in self.priority_portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.priority_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER], code)

                QTest.qWait(5000)
                self.line.notification("시스템 종료")
                sys.exit()

        elif sRealType == self.customType.STOCK_CONCLUSION:
            self.createAnalysisEtfFile(sCode, sRealData)
            self.commRealData(sCode, sRealType, sRealData)

            if self.purchased_deposit > 0 and sCode in self.second_cal_target_etf_stock_dict.keys() and sCode in self.second_portfolio_stock_dict.keys() and sCode not in self.second_order_stock_dict.keys() and sCode not in self.second_not_order_stock_dict.keys():
                self.buySecondEtf(sCode, sRealType, sRealData)

            if self.purchased_deposit > 0 and sCode in self.priority_cal_target_etf_stock_dict.keys() and sCode in self.priority_portfolio_stock_dict.keys() and sCode not in self.priority_order_stock_dict.keys() and sCode not in self.priority_not_order_stock_dict.keys():
                self.buyPriorityEtf(sCode, sRealType, sRealData)

    def commRealData(self, sCode, sRealType, sRealData):
        b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CURRENT_PRICE])  # 출력 : +(-)2520
        b = abs(int(b.strip()))
        e = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.SELLING_QUOTE])  # 출력 : +(-)2520
        e = abs(int(e.strip()))
        a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.TIGHTENING_TIME])  # 출력 HHMMSS

        c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.THE_DAY_BEFORE])  # 출력 : +(-)2520
        c = abs(int(c.strip()))

        d = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.FLUCTUATION_RATE])  # 출력 : +(-)12.98
        d = float(d.strip())

        f = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.BID])  # 출력 : +(-)2515
        f = abs(int(f.strip()))

        g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.VOLUME])  # 출력 : +240124  매수일때, -2034 매도일 때
        g = abs(int(g.strip()))

        h = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.CUMULATIVE_VOLUME])  # 출력 : 240124
        h = abs(int(h.strip()))

        i = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.HIGHEST_PRICE])  # 출력 : +(-)2530
        i = abs(int(i.strip()))

        j = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.START_PRICE])  # 출력 : +(-)2530
        j = abs(int(j.strip()))

        k = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType][self.customType.LOWEST_PRICE])  # 출력 : +(-)2530
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

    def buyPriorityEtf(self, sCode, sRealType, sRealData):
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.TIGHTENING_TIME: self.total_cal_target_etf_stock_dict[sCode][self.customType.TIGHTENING_TIME]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.THE_DAY_BEFORE: self.total_cal_target_etf_stock_dict[sCode][self.customType.THE_DAY_BEFORE]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.SELLING_QUOTE: self.total_cal_target_etf_stock_dict[sCode][self.customType.SELLING_QUOTE]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.BID: self.total_cal_target_etf_stock_dict[sCode][self.customType.BID]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.VOLUME: self.total_cal_target_etf_stock_dict[sCode][self.customType.VOLUME]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.CUMULATIVE_VOLUME: self.total_cal_target_etf_stock_dict[sCode][self.customType.CUMULATIVE_VOLUME]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.HIGHEST_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.HIGHEST_PRICE]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.START_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.START_PRICE]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.LOWEST_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.LOWEST_PRICE]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_START_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_START_PRICE]})

        value = self.priority_cal_target_etf_stock_dict[sCode]
        goal_stock_price = value[self.customType.GOAL_PRICE]
        current_stock_price = self.priority_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        limit_stock_price = self.priority_cal_target_etf_stock_dict[sCode][self.customType.SELLING_QUOTE]
        if goal_stock_price == '':
            goal_stock_price = self.cal_goal_stock_price(code=sCode, value=value)
            self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.GOAL_PRICE: goal_stock_price})

        if goal_stock_price == 0:
            self.logging.logger.info("%s > %s" % (sCode, self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG))
            self.priority_not_order_stock_dict.update({sCode: {"사유": self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG}})
        elif goal_stock_price <= current_stock_price != self.priority_cal_target_etf_stock_dict[sCode][self.customType.HIGHEST_PRICE] and self.isGoalStockPriceRange(goal_stock_price, current_stock_price):

            self.logging.logger.info(self.logType.PASS_CONDITION_GOAL_PRICE_LOG % (sCode, goal_stock_price))
            result = self.use_money / limit_stock_price
            quantity = int(result)
            total_buy_price = limit_stock_price * quantity
            if quantity >= 1 and self.purchased_deposit > total_buy_price:
                # 사용자 구분명, 화면번호, 계좌번호 10자리, 주문유형, 종목코드, 주문수량, 주문가격, 거래구분, 원주문번호
                # 주문유형 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    [self.customType.NEW_PURCHASE, self.priority_portfolio_stock_dict[sCode][self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, sCode, quantity, limit_stock_price,
                     self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

                if order_success == 0:
                    self.purchased_deposit -= total_buy_price
                    self.priority_order_stock_dict.update({sCode: {"사유": self.logType.ORDER_BUY_SUCCESS_LOG}})
                    self.logging.logger.info(
                        self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
                    self.line.notification(
                        self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
                else:
                    self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)
            else:
                self.logging.logger.info(self.logType.ORDER_BUY_FAIL_STATUS_LOG % (sCode, self.purchased_deposit, quantity, total_buy_price))
                self.priority_not_order_stock_dict.update({sCode: {"사유": self.logType.ORDER_BUY_FAIL_NOT_POSSIBLE}})

        if len(self.priority_portfolio_stock_dict.keys()) == len(self.priority_order_stock_dict.keys()) + len(self.priority_not_order_stock_dict.keys()) and self.purchased_deposit > 0:
            self.secondPortfolioStockRealReg()

    def buySecondEtf(self, sCode, sRealType, sRealData):
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.TIGHTENING_TIME: self.total_cal_target_etf_stock_dict[sCode][self.customType.TIGHTENING_TIME]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.THE_DAY_BEFORE: self.total_cal_target_etf_stock_dict[sCode][self.customType.THE_DAY_BEFORE]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.SELLING_QUOTE: self.total_cal_target_etf_stock_dict[sCode][self.customType.SELLING_QUOTE]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.BID: self.total_cal_target_etf_stock_dict[sCode][self.customType.BID]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.VOLUME: self.total_cal_target_etf_stock_dict[sCode][self.customType.VOLUME]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.CUMULATIVE_VOLUME: self.total_cal_target_etf_stock_dict[sCode][self.customType.CUMULATIVE_VOLUME]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.HIGHEST_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.HIGHEST_PRICE]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.START_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.START_PRICE]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.LOWEST_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.LOWEST_PRICE]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_START_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_START_PRICE]})

        value = self.second_cal_target_etf_stock_dict[sCode]
        goal_stock_price = value[self.customType.GOAL_PRICE]
        current_stock_price = self.second_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        limit_stock_price = self.second_cal_target_etf_stock_dict[sCode][self.customType.SELLING_QUOTE]
        if goal_stock_price == '':
            goal_stock_price = self.cal_goal_stock_price(code=sCode, value=value)
            self.second_cal_target_etf_stock_dict[sCode].update({self.customType.GOAL_PRICE: goal_stock_price})

        if goal_stock_price == 0:
            self.logging.logger.info("%s > %s" % (sCode, self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG))
            self.second_not_order_stock_dict.update({sCode: {"사유": self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG}})
        elif goal_stock_price <= current_stock_price != self.second_cal_target_etf_stock_dict[sCode][self.customType.HIGHEST_PRICE] and self.isGoalStockPriceRange(goal_stock_price, current_stock_price):

            self.logging.logger.info(self.logType.PASS_CONDITION_GOAL_PRICE_LOG % (sCode, goal_stock_price))
            result = self.use_money / limit_stock_price
            quantity = int(result)
            total_buy_price = limit_stock_price * quantity
            if quantity >= 1 and self.purchased_deposit > total_buy_price:
                # 사용자 구분명, 화면번호, 계좌번호 10자리, 주문유형, 종목코드, 주문수량, 주문가격, 거래구분, 원주문번호
                # 주문유형 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    [self.customType.NEW_PURCHASE, self.second_portfolio_stock_dict[sCode][self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, sCode, quantity, limit_stock_price,
                     self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

                if order_success == 0:

                    self.purchased_deposit -= total_buy_price
                    self.second_order_stock_dict.update({sCode: {"사유": self.logType.ORDER_BUY_SUCCESS_LOG}})
                    self.logging.logger.info(
                        self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
                    self.line.notification(
                        self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
                else:
                    self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)
            else:
                self.logging.logger.info(self.logType.ORDER_BUY_FAIL_STATUS_LOG % (sCode, self.purchased_deposit, quantity, total_buy_price))
                self.priority_not_order_stock_dict.update({sCode: {"사유": self.logType.ORDER_BUY_FAIL_NOT_POSSIBLE}})

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

    def createAnalysisEtfFile(self, sCode, sRealData):
        now = datetime.datetime.now()
        nowDate = now.strftime('%Y-%m-%d')
        parent_path = self.analysis_etf_file_path + nowDate
        if not os.path.isdir(parent_path):
            os.mkdir(parent_path)
        path = parent_path + '/' + sCode + '.txt'
        f = open(path, "a", encoding="utf8")
        f.write("%s\t%s\n" %
                (sCode, sRealData))
        f.close()