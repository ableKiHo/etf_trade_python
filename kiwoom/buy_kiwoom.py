import sys

import numpy as np
from PyQt5.QtTest import *

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


class BuyKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF BuyKiwoom() class start.")
        self.line.notification("ETF BuyKiwoom() class start.")

        self.analysis_etf_file_path = self.property.analysisEtfFilePath
        self.sell_analysis_etf_file_path = self.property.sellAnalysisEtfFIlePath

        self.priority_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(레버리지, 인버스용)
        self.second_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(일반)
        self.total_cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용(일반)
        self.priority_portfolio_stock_dict = {}  # 실시간 조회 주식 정보 저장용(레버리지, 인버스용)
        self.second_portfolio_stock_dict = {}  # 실시간 조회 주식 정보 저장용(일반)
        self.priority_not_order_stock_dict = {}  # 매수 주문 불가 저장용
        self.second_not_order_stock_dict = {}  # 매수 주문 불가 저장용
        self.priority_wait_order_stock_dict = {}  # 매수 주문 대기용 저장용

        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린 번호
        self.buy_screen_meme_stock = "3000"  # 종목별 할당할 주문용 스크린 번호
        self.buy_screen_real_stock = "6000"  # 종별별 할당할 스크린 번호
        self.sell_screen_meme_stock = "4000"

        self.callable_sencod_stock = True

        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결

        self.line.notification("ETF BUY TRADE START")
        self.detail_account_info()
        QTest.qWait(5000)
        self.read_target_etf_file()  # 대상 ETF(파일) 읽기
        QTest.qWait(10000)
        self.screen_number_setting(self.priority_cal_target_etf_stock_dict, self.priority_portfolio_stock_dict)
        self.screen_number_setting(self.second_cal_target_etf_stock_dict, self.second_portfolio_stock_dict)

        QTest.qWait(5000)
        # 실시간 수신 관련 함수
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                         self.realType.REALTYPE[self.customType.MARKET_START_TIME][self.customType.MARKET_OPERATION], "0")

        self.portfolio_stock_real_reg(self.priority_portfolio_stock_dict)

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
        use_money = float(self.buy_possible_deposit) * self.use_money_percent
        self.use_money = int(use_money)
        self.purchased_deposit = int(use_money)
        self.use_money = self.use_money / self.max_sell_stock_count

        self.stop_screen_cancel(self.screen_my_info)
        self.detail_account_info_event_loop.exit()
        self.logging.logger.info(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)
        self.line.notification(self.logType.PURCHASED_DEPOSIT_LOG % self.purchased_deposit)

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
                                                                                     self.customType.GOAL_PRICE: ''}})
                    else:
                        self.second_cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                                   self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                                   self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                                   self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                                   self.customType.THE_DAY_BEFORE_AVG: avg_the_day_before_price,
                                                                                   self.customType.THE_DAY_BEFORE_MAX: max_the_day_before_price,
                                                                                   self.customType.THE_DAY_BEFORE_MIN: min_the_day_before_price,
                                                                                   self.customType.GOAL_PRICE: ''}})

            f.close()
            self.logging.logger.info("전일자 대상건 파일 처리 완료")
            self.logging.logger.info("레버리지, 인버스 %s" % self.priority_cal_target_etf_stock_dict)
            self.logging.logger.info("일반 %s" % self.second_cal_target_etf_stock_dict)

    def screen_number_setting(self, cal_dict, stock_dict):
        self.logging.logger.info("screen_number_setting")
        screen_overwrite = []

        for code in cal_dict.keys():
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
            elif code not in stock_dict.keys():
                stock_dict.update({code: {self.customType.SCREEN_NUMBER: str(temp_screen),
                                          self.customType.MEME_SCREEN_NUMBER: str(meme_screen),
                                          self.customType.SELL_MEME_SCREEN_NUMBER: str(sell_meme_screen)}})

            cnt += 1

        self.logging.logger.info(self.logType.PORTFOLIO_STOCK_DICT_LOG % stock_dict)

    def portfolio_stock_real_reg(self, portfolio_stock_dict):
        for code in portfolio_stock_dict.keys():
            screen_num = portfolio_stock_dict[code][self.customType.SCREEN_NUMBER]
            fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)

                for code in self.priority_portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.priority_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER], code)

                for code in self.second_portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.second_portfolio_stock_dict[code][self.customType.SCREEN_NUMBER], code)

                QTest.qWait(5000)
                self.line.notification("시스템 종료")
                sys.exit()

        elif sRealType == self.customType.STOCK_CONCLUSION:
            self.commRealData(sCode, sRealType, sRealData)
            createAnalysisEtfFile(sCode, self.total_cal_target_etf_stock_dict[sCode], self.analysis_etf_file_path)

            if sCode in self.second_order_stock_dict.keys() or sCode in self.priority_order_stock_dict.keys():

                current_stock_price = self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]

                if sCode in self.priority_order_stock_dict.keys():
                    order_info = self.priority_cal_target_etf_stock_dict[sCode]
                    self.plus_sell_send_order(sCode, current_stock_price, order_info, self.priority_portfolio_stock_dict)
                    createAnalysisEtfFile(sCode, order_info, self.sell_analysis_etf_file_path)

                if sCode in self.second_order_stock_dict.keys():
                    order_info = self.second_cal_target_etf_stock_dict[sCode]
                    self.plus_sell_send_order(sCode, current_stock_price, order_info, self.second_portfolio_stock_dict)
                    createAnalysisEtfFile(sCode, order_info, self.sell_analysis_etf_file_path)

            if self.purchased_deposit > 0 and sCode in self.second_cal_target_etf_stock_dict.keys() and sCode not in self.second_order_stock_dict.keys() and sCode not in self.second_not_order_stock_dict.keys():
                self.buy_second_etf(sCode, sRealType, sRealData)

            if self.purchased_deposit > 0 and sCode in self.priority_cal_target_etf_stock_dict.keys() and sCode not in self.priority_order_stock_dict.keys() and sCode not in self.priority_not_order_stock_dict.keys():
                self.buy_priority_etf(sCode, sRealType, sRealData)

    def plus_sell_send_order(self, sCode, current_stock_price, order_info, target_dict):
        if current_stock_price < order_info[self.customType.SELL_STD_PRICE]:
            self.logging.logger.info(
                self.logType.SELL_MINUS_STD_PRICE_LOG % (sCode, order_info[self.customType.PURCHASE_PRICE], order_info[self.customType.SELL_STD_PRICE], current_stock_price))

            self.sell_send_order(sCode, target_dict[sCode][self.customType.SELL_MEME_SCREEN_NUMBER], order_info[self.customType.HOLDING_QUANTITY])
        else:
            if self.customType.SELL_STD_HIGHEST_PRICE in order_info:
                if current_stock_price > order_info[self.customType.SELL_STD_HIGHEST_PRICE]:
                    order_info.update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})
            else:
                order_info.update({self.customType.SELL_STD_HIGHEST_PRICE: current_stock_price})

            if current_stock_price > order_info[self.customType.SELL_HIGHEST_PRICE]:
                self.logging.logger.info(
                    self.logType.SELL_MAX_PLUS_STD_PRICE_LOG % (
                        sCode, order_info[self.customType.PURCHASE_PRICE], current_stock_price)
                )
                self.sell_send_order(sCode, target_dict[sCode][self.customType.SELL_MEME_SCREEN_NUMBER], order_info[self.customType.HOLDING_QUANTITY])

            if is_second_rank_plus_sell_price(order_info[self.customType.PURCHASE_PRICE], order_info[self.customType.SELL_STD_HIGHEST_PRICE], current_stock_price):
                self.logging.logger.info(
                    self.logType.SELL_PLUS_STD_PRICE_LOG % (
                        sCode, order_info[self.customType.PURCHASE_PRICE], order_info[self.customType.SELL_STD_HIGHEST_PRICE], current_stock_price)
                )
                self.sell_send_order(sCode, target_dict[sCode][self.customType.SELL_MEME_SCREEN_NUMBER], order_info[self.customType.HOLDING_QUANTITY])

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

        current_price_list = []
        tic_price_list = []

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
                    if len(tic_price_list) >= 6:
                        del tic_price_list[6:]
                else:
                    tic_price_list.append(np.mean(current_price_list))
                current_price_list.clear()
        else:
            current_price_list.append(b)
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE_LIST: current_price_list})
        self.total_cal_target_etf_stock_dict[sCode].update({self.customType.TIC_120_PRICE: tic_price_list})

    def buy_priority_etf(self, sCode, sRealType, sRealData):
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
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE_LIST: self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE_LIST]})
        self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.TIC_120_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.TIC_120_PRICE]})

        value = self.priority_cal_target_etf_stock_dict[sCode]
        goal_stock_price = value[self.customType.GOAL_PRICE]
        current_stock_price = self.priority_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        limit_stock_price = self.priority_cal_target_etf_stock_dict[sCode][self.customType.SELLING_QUOTE]
        tic_120_avg_price_history = self.priority_cal_target_etf_stock_dict[sCode][self.customType.TIC_120_PRICE]
        highest_stock_price = self.priority_cal_target_etf_stock_dict[sCode][self.customType.HIGHEST_PRICE]

        if goal_stock_price == '':
            goal_stock_price = cal_goal_stock_price(value[self.customType.CURRENT_START_PRICE], value[self.customType.LAST_DAY_LAST_PRICE], value[self.customType.LAST_DAY_HIGHEST_PRICE], value[self.customType.LAST_DAY_LOWEST_PRICE])
            self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.GOAL_PRICE: goal_stock_price})

        if goal_stock_price == 0:
            self.logging.logger.info("%s > %s" % (sCode, self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG))
            self.priority_not_order_stock_dict.update({sCode: {"사유": self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG}})
            self.dynamicCall("SetRealRemove(QString, QString)", self.priority_portfolio_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
        elif goal_stock_price <= current_stock_price < highest_stock_price and is_target_stock_price_range(goal_stock_price, current_stock_price) and is_current_price_compare_history(current_stock_price, tic_120_avg_price_history):

            if sCode in self.priority_wait_order_stock_dict.keys():
                del self.priority_wait_order_stock_dict[sCode]

            self.logging.logger.info(self.logType.PASS_CONDITION_GOAL_PRICE_LOG % (sCode, goal_stock_price, current_stock_price, limit_stock_price))
            result = self.use_money / limit_stock_price

            quantity = int(result)
            total_buy_price = limit_stock_price * quantity
            if quantity >= 1 and self.purchased_deposit > total_buy_price:
                order_success = self.send_order_limit_stock_price(sCode, total_buy_price, quantity, limit_stock_price, self.priority_order_stock_dict, self.priority_portfolio_stock_dict)
                if order_success == 0:
                    self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: limit_stock_price})
                    self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.HOLDING_QUANTITY: quantity})
                    self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_PRICE: get_minus_sell_std_price(limit_stock_price)})
                    self.priority_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_HIGHEST_PRICE: get_max_plus_sell_std_price(limit_stock_price)})

            else:
                self.logging.logger.info(self.logType.ORDER_BUY_FAIL_STATUS_LOG % (sCode, self.purchased_deposit, quantity, total_buy_price))
                self.priority_not_order_stock_dict.update({sCode: {"사유": self.logType.ORDER_BUY_FAIL_NOT_POSSIBLE}})
        else:
            if sCode not in self.priority_wait_order_stock_dict.keys():
                self.priority_wait_order_stock_dict.update({sCode: {}})
            self.priority_wait_order_stock_dict[sCode].update({'goal_stock_price': goal_stock_price})
            self.priority_wait_order_stock_dict[sCode].update({'current_stock_price': current_stock_price})

        if len(self.priority_portfolio_stock_dict.keys()) == len(self.priority_order_stock_dict.keys()) + len(self.priority_not_order_stock_dict.keys()) + len(self.priority_wait_order_stock_dict.keys()) and self.purchased_deposit > 0:

            if self.callable_sencod_stock:
                self.logging.logger.info("second_portfolio_stock_start")
                self.callable_sencod_stock = False
                self.portfolio_stock_real_reg(self.second_portfolio_stock_dict)

    def buy_second_etf(self, sCode, sRealType, sRealData):
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
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE_LIST: self.total_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE_LIST]})
        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.TIC_120_PRICE: self.total_cal_target_etf_stock_dict[sCode][self.customType.TIC_120_PRICE]})

        value = self.second_cal_target_etf_stock_dict[sCode]
        goal_stock_price = value[self.customType.GOAL_PRICE]
        current_stock_price = self.second_cal_target_etf_stock_dict[sCode][self.customType.CURRENT_PRICE]
        limit_stock_price = self.second_cal_target_etf_stock_dict[sCode][self.customType.SELLING_QUOTE]
        tic_120_avg_price_history = self.second_cal_target_etf_stock_dict[sCode][self.customType.TIC_120_PRICE]
        highest_stock_price = self.second_cal_target_etf_stock_dict[sCode][self.customType.HIGHEST_PRICE]

        if goal_stock_price == '':
            goal_stock_price = cal_goal_stock_price(value[self.customType.CURRENT_START_PRICE], value[self.customType.LAST_DAY_LAST_PRICE], value[self.customType.LAST_DAY_HIGHEST_PRICE], value[self.customType.LAST_DAY_LOWEST_PRICE])
            self.second_cal_target_etf_stock_dict[sCode].update({self.customType.GOAL_PRICE: goal_stock_price})

        if goal_stock_price == 0:
            self.logging.logger.info("%s > %s" % (sCode, self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG))
            self.second_not_order_stock_dict.update({sCode: {"사유": self.logType.NOT_BUY_TARGET_GOAL_PRICE_ZERO_LOG}})
            self.dynamicCall("SetRealRemove(QString, QString)", self.second_portfolio_stock_dict[sCode][self.customType.SCREEN_NUMBER], sCode)
        elif goal_stock_price <= current_stock_price < highest_stock_price and is_target_stock_price_range(goal_stock_price, current_stock_price) and is_current_price_compare_history(current_stock_price, tic_120_avg_price_history):
            self.logging.logger.info(self.logType.PASS_CONDITION_GOAL_PRICE_LOG % (sCode, goal_stock_price, current_stock_price, limit_stock_price))
            result = self.use_money / limit_stock_price
            quantity = int(result)
            total_buy_price = limit_stock_price * quantity
            if quantity >= 1 and self.purchased_deposit > total_buy_price:
                order_success = self.send_order_limit_stock_price(sCode, total_buy_price, quantity, limit_stock_price, self.second_order_stock_dict, self.second_portfolio_stock_dict)
                if order_success == 0:
                    self.second_cal_target_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: limit_stock_price})
                    self.second_cal_target_etf_stock_dict[sCode].update({self.customType.HOLDING_QUANTITY: quantity})
                    self.second_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_PRICE: get_minus_sell_std_price(limit_stock_price)})
                    self.second_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_HIGHEST_PRICE: get_max_plus_sell_std_price(limit_stock_price)})
            elif total_buy_price >= self.purchased_deposit >= limit_stock_price:
                result = self.purchased_deposit / limit_stock_price
                quantity = int(result)
                total_buy_price = limit_stock_price * quantity
                if quantity >= 1:
                    order_success = self.send_order_limit_stock_price(sCode, total_buy_price, quantity, limit_stock_price, self.second_order_stock_dict, self.second_portfolio_stock_dict)
                    if order_success == 0:
                        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.PURCHASE_PRICE: limit_stock_price})
                        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.HOLDING_QUANTITY: quantity})
                        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_STD_PRICE: get_minus_sell_std_price(limit_stock_price)})
                        self.second_cal_target_etf_stock_dict[sCode].update({self.customType.SELL_HIGHEST_PRICE: get_max_plus_sell_std_price(limit_stock_price)})
            else:
                self.logging.logger.info(self.logType.ORDER_BUY_FAIL_STATUS_LOG % (sCode, self.purchased_deposit, quantity, total_buy_price))
                self.second_not_order_stock_dict.update({sCode: {"사유": self.logType.ORDER_BUY_FAIL_NOT_POSSIBLE}})

    def send_order_limit_stock_price(self, sCode, total_buy_price, quantity, limit_stock_price, use_dict, stock_dict):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, stock_dict[sCode][self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, sCode, quantity, limit_stock_price,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

        if order_success == 0:

            self.purchased_deposit -= total_buy_price
            use_dict.update({sCode: {"사유": self.logType.ORDER_BUY_SUCCESS_LOG}})
            self.logging.logger.info(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
            self.line.notification(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (sCode, quantity, limit_stock_price, self.purchased_deposit))
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)
        return order_success

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
