import os
import sys
import datetime

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtTest import QTest

from config.errorCode import *
from config.kiwoomType import *
from config.lineNotify import LineNotify
from config.log_class import *
from config.property import Property


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        self.property = Property()
        self.realType = RealType()
        self.logging = Logging()
        self.line = LineNotify()

        self.logging.logger.info("ETF Kiwoom() class start.")
        self.line.notification("ETF Kiwoom() class start.")

        # event loop를 실행하기 위한 변수 모음
        self.login_event_loop = QEventLoop()  # 로그인 요청용 이벤트 루프
        self.all_etc_info_event_loop = QEventLoop()  # 전체 ETF 정보 조회 이벤트 루프
        self.etf_info_event_loop = QEventLoop()  # 특정 ETF 정보 조회 이벤트 루프
        self.calculator_event_loop = QEventLoop()  # 대상 ETF 목표가 설정 이벤트 루프
        self.detail_account_info_event_loop = QEventLoop()  # 예수금 요청용 이벤트 루프
        ##########################################

        # 계좌 관련 변수
        self.account_num = self.property.account  # 계좌번호
        self.account_pw = self.property.accountPw
        self.use_money = 0  # 실제 투자에 사용할 금액
        self.use_money_percent = 0.5  # 예수금에서 실제 사용할 비율
        self.deposit = 0  # 예수금
        self.buy_possible_deposit = 0  # 주문가능 금액
        self.purchased_deposit = 0  # 구매한 금액
        self.target_etf_file_path = self.property.targetEtfFilePath
        ##########################################

        #  종목정보 가져오기
        self.target_etf_stock_dict = {}  # 장 마감 후 저가, 고가, 종가 저장용
        self.cal_target_etf_stock_dict = {}  # 장 시작 후 시가 저장 후 목표가 설정용
        self.account_stock_dict = {}  # 보유주식 정보 저장용
        self.sell_portfolio_stock_dict = {}  # 매도용 실시간 조회 주식 정보 저장용
        self.not_order_sell_stock_dict = {}  # 매도용 주문 완료 저장용
        self.portfolio_stock_dict = {}  # 실시간 조회 주식 정보 저장용
        self.order_stock_dict = {}  # 매수 주문 완료 저장용
        self.not_order_stock_dict = {}  # 매수 주문 불가 저장용

        #  요청 스크린 번호
        self.screen_my_info = "2000"  # 계좌 관련한 스크린 번호
        self.screen_all_etf_stock = "4000"  # 전체 etf 정보 조회 스크린 번호
        self.screen_etf_stock = "5000"  # etf 개별 조회 스크린 번호
        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린 번호
        self.sell_screen_meme_stock = "7000"  # 종목별 할당할 주문용 스크린 번호
        self.sell_screen_real_stock = "8000"  # 종별별 할당할 스크린 번호
        self.buy_screen_meme_stock = "3000"  # 종목별 할당할 주문용 스크린 번호
        self.buy_screen_real_stock = "6000"  # 종별별 할당할 스크린 번호

        now = datetime.datetime.now()
        t = ['월', '화', '수', '목', '금', '토', '일']
        weekDay = datetime.datetime.today().weekday()
        if t[weekDay] == '토' or t[weekDay] == '일':
            sys.exit()

        # 초기 셋팅 함수들 바로 실행
        self.get_ocx_instance()  # OCX 방식을 파이썬에 사용할 수 있게 변환해 주는 함수
        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결
        self.signal_login_commconnect()  # 로그인 요청 함수 포함
        # self.get_account_info()  # 계좌번호 가져오기

        hour = int(now.hour)

        if 8 <= hour <= 10:
            self.line.notification("ETF AUTO SELL TRADE START")
            self.detail_account_mystock()  # 계좌평가잔고내역 가져오기(보유 ETF 조회)
            QTest.qWait(10000)
            self.sell_screen_number_setting()
            QTest.qWait(5000)

            for sCode in self.sell_portfolio_stock_dict.keys():
                asd = self.account_stock_dict[sCode]
                QTest.qWait(1000)
                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["신규매도", self.sell_portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 2, sCode, asd['보유수량'],
                     0, self.realType.SENDTYPE['거래구분']['시장가'], ""]
                )

                if order_success == 0:
                    self.logging.logger.info("매도주문 전달 성공 [%s]" % sCode)
                    self.not_order_sell_stock_dict.update({sCode: {"사유": "매도주문 전달 성공"}})
                else:
                    self.logging.logger.info("매도주문 전달 실패 [%s]" % sCode)

            QTest.qWait(10000)
            self.line.notification("ETF AUTO SELL TRADE END")
            QTest.qWait(5000)
            sys.exit()
        elif 11 <= hour <= 17:
            self.line.notification("ETF BUY TRADE START")
            self.detail_account_info()
            QTest.qWait(5000)
            self.read_target_etf_file()  # 대상 ETF(파일) 읽기
            QTest.qWait(10000)
            self.screen_number_setting()

            QTest.qWait(5000)
            # 실시간 수신 관련 함수
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '',
                             self.realType.REALTYPE['장시작시간']['장운영구분'], "0")

            for code in self.portfolio_stock_dict.keys():
                screen_num = self.portfolio_stock_dict[code]['스크린번호']
                fids = self.realType.REALTYPE['주식체결']['체결시간']
                self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

        else:
            self.line.notification("ETF PREPARE AUTO TRADE START")
            # TODO 일일 수익률 확인 필요
            self.end_detail_account_info()
            self.detail_account_mystock()  # 계좌평가잔고내역 가져오기(보유 ETF 조회)
            self.prepare_next_day()
            self.line.notification("ETF PREPARE AUTO TRADE END")

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenApiCtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)  # 로그인 관련 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot)  # 트랜잭션 요청 관련 이벤트
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)  # 실시간 이벤트 연결
        self.OnReceiveChejanData.connect(self.chejan_slot)  # 종목 주문체결 관련한 이벤트

    def signal_login_commconnect(self):
        self.dynamicCall("CommConnect()")  # 로그인 요청 시그널
        self.login_event_loop.exec_()  # 이벤트 루프 실행

    def login_slot(self, err_code):
        login_status = errors(err_code)[1]
        self.logging.logger.info(login_status)
        self.line.notification("login > %s" % login_status)
        # 로그인 처리가 완료댔으면 이벤트 루프를 종료한다.
        self.login_event_loop.exit()

    def detail_account_info(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_info")
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "opw00001", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def get_all_etf_stock(self, sPrevNext="0"):
        self.logging.logger.info("get_all_etf_stock")
        self.dynamicCall("SetInputValue(QString, QString)", "과세유형", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "NAV대비", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "운용사", "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "ETF전체시세요청", "opt40004", sPrevNext, self.screen_all_etf_stock)

        self.all_etc_info_event_loop.exec_()

    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        self.logging.logger.info("스크린: %s, 요청이름: %s, tr코드: %s --- %s" % (sScrNo, sRQName, sTrCode, msg))

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")
            self.deposit = int(deposit)
            buy_possible_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "주문가능금액")
            self.buy_possible_deposit = int(buy_possible_deposit)

            self.logging.logger.info("주문가능금액 : %s" % self.buy_possible_deposit)
            self.line.notification("당일 주문가능금액 : %s" % self.buy_possible_deposit)
            #  모든 예수금을 하나의 종목을 매수하는데 사용하지 않아야 하므로 사용할 비율 지정
            use_money = float(self.buy_possible_deposit) * self.use_money_percent
            self.use_money = int(use_money)
            self.purchased_deposit = int(use_money)
            #  한 종목을 매수할 떄 모든 돈을 다 쓰면 안되므로 3종목 매수할 수 있게 나눔
            self.use_money = self.use_money / 3

            self.stop_screen_cancel(self.screen_my_info)
            self.detail_account_info_event_loop.exit()
            self.logging.logger.info("당일 예산 [%s]" % self.purchased_deposit)
            self.line.notification("당일 예산 [%s]" % self.purchased_deposit)
        elif sRQName == "예수금상세현황요청_마감":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")
            self.deposit = int(deposit)
            self.logging.logger.info("마감 예수금 : %s" % self.deposit)
            self.line.notification("마감 예수금 : %s" % self.deposit)
            self.stop_screen_cancel(self.screen_my_info)
            self.detail_account_info_event_loop.exit()

        elif sRQName == "ETF전체시세요청":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")
                volume = volume.strip()
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
                code = code.strip()
                if int(volume) >= 100000 and code not in self.account_stock_dict.keys():
                    code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                    code_nm = code_nm.strip()

                    if code in self.target_etf_stock_dict:
                        pass
                    else:
                        self.target_etf_stock_dict[code] = {}

            if sPrevNext == "2":  # 다음페이지 존재
                self.get_all_etf_stock(sPrevNext="2")
            else:
                self.stop_screen_cancel(self.screen_all_etf_stock)
                self.all_etc_info_event_loop.exit()

        elif sRQName == "주식기본정보요청":
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()
            code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목명")
            highest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "고가")
            lowest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "저가")
            last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "현재가")
            change_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "전일대비")

            market_cap = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "시가총액") # 단위 억
            market_cap = market_cap.strip()

            self.logging.logger.info("종목번호: %s / 고가: %s / 저가: %s / 종가: %s / 전일대비: %s / 시가총액: %s" % (
                code, highest_stock_price.strip(), lowest_stock_price.strip(), last_stock_price.strip(), change_price.strip(), market_cap)
            )

            if int(market_cap) >= 130:
                self.target_etf_stock_dict[code].update({"종목명": code_nm})
                self.target_etf_stock_dict[code].update({"전일고가": abs(int(highest_stock_price.strip()))})
                self.target_etf_stock_dict[code].update({"전일저가": abs(int(lowest_stock_price.strip()))})
                self.target_etf_stock_dict[code].update({"전일종가": abs(int(last_stock_price.strip()))})

                f = open(self.target_etf_file_path, "a", encoding="utf8")
                f.write("%s\t%s\t%s\t%s\t%s\n" %
                        (code, self.target_etf_stock_dict[code]["종목명"], self.target_etf_stock_dict[code]["전일고가"],
                         self.target_etf_stock_dict[code]["전일저가"], self.target_etf_stock_dict[code]["전일종가"]))
                f.close()

            # self.stop_screen_cancel(self.screen_etf_stock)
            self.etf_info_event_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money = int(total_buy_money)
            total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액")
            total_profit_loss_money = int(total_profit_loss_money)
            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate = float(total_profit_loss_rate)

            self.logging.logger.info("계좌평가잔고내역요청 싱글데이터 : 총매입금액: %s / 총평가손익금액: %s / 총수익률: %s" % (
                total_buy_money, total_profit_loss_money, total_profit_loss_rate))

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)  # 최대 20개 카운트
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                code_nm = code_nm.strip()
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                self.logging.logger.info("종목번호: %s / 종목명: %s / 보유수량: %s / 매입가: %s / 수익률: %s / 현재가: %s" % (
                    code, code_nm, stock_quantity, buy_price, learn_rate, current_price))

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

                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

                self.line.notification("보유 종목 > %s" % self.account_stock_dict[code])

            self.logging.logger.info("계좌에 가지고 있는 종목은 %s" % rows)

            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.stop_screen_cancel(self.screen_my_info)
                self.detail_account_info_event_loop.exit()

    def chejan_slot(self, sGubun, nItemCnt, sFidList):
        if int(sGubun) == 0:  # 주문체결
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])  # 출력 : 접수, 확인, 체결
            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])  # 출력 : -매도, +매수
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
            chegual_price = self.dynamicCall("GetChejanData(int)",
                                             self.realType.REALTYPE['주문체결']['체결가'])  # 출력 : 2110, defalt : ''
            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)
            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량'])  # 출력 : 5, defalt : ''
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)
            if order_status == "체결":
                self.logging.logger.info("%s_주문체결 %s[%s] / 주문상태 : %s / 체결가 : %s / 체결량 : %s" % (
                    order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))
                self.line.notification("%s_주문체결 %s[%s] / 주문상태 : %s / 체결가 : %s / 체결량 : %s" % (
                    order_gubun, sCode, stock_name, order_status, chegual_price, chegual_quantity))

        elif int(sGubun) == 1:  # 잔고
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]
            # 주문이 처리되고 보유한 수량
            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            # 주문을 넣고 남은 나머지 수량
            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)
            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))
            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가'])
            total_buy_price = int(total_buy_price)
            income_rate = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['손익율'])

            self.logging.logger.info(
                "%s_잔고 %s[%s] / 보유수량 : %s / 주문가능수량 : %s / 매입단가 : %s / 총매입가 : %s / 손익율 : %s" % (
                    meme_gubun, sCode, stock_name, stock_quan, like_quan, buy_price, total_buy_price, income_rate
                )
            )
            self.line.notification("%s_잔고 %s[%s] / 보유수량 : %s / 주문가능수량 : %s / 매입단가 : %s / 총매입가 : %s / 손익율 : %s" % (
                    meme_gubun, sCode, stock_name, stock_quan, like_quan, buy_price, total_buy_price, income_rate
                ))

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]['장운영구분']  # (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '0':
                self.logging.logger.info("장 시작 전")
            elif value == '3':
                self.logging.logger.info("장 시작")
                self.line.notification("장 시작")
            elif value == '2':
                self.logging.logger.info("장 종료, 동시호가로 넘어감")
            elif value == '4':
                self.logging.logger.info("3시30분 장 종료")
                self.line.notification("3시 30분 장 종료")

                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[code]['스크린번호'], code)

                for code in self.sell_portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.sell_portfolio_stock_dict[code]['스크린번호'], code)

                self.line.notification("시스템 종료")
                sys.exit()

        elif sRealType == "주식체결":
            b = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['현재가'])  # 출력 : +(-)2520
            b = abs(int(b.strip()))
            e = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                 self.realType.REALTYPE[sRealType]['(최우선)매도호가'])  # 출력 : +(-)2520
            e = abs(int(e.strip()))

            if self.purchased_deposit > 0 and sCode in self.not_order_stock_dict.keys():
                if len(self.portfolio_stock_dict.keys()) == len(self.order_stock_dict.keys()) + len(self.not_order_stock_dict.keys()):

                    value = self.cal_target_etf_stock_dict[sCode]
                    reason = value['사유']
                    if reason == '매수주문 불가 [주문가능 수량 부족]':
                        goal_stock_price = value['목표가']
                        if b > goal_stock_price:
                            result = self.purchased_deposit / e
                            quantity = int(result)
                            total_buy_price = e * quantity
                            if quantity > 1 and self.purchased_deposit > total_buy_price:
                                # 사용자 구분명, 화면번호, 계좌번호 10자리, 주문유형, 종목코드, 주문수량, 주문가격, 거래구분, 원주문번호
                                # 주문유형 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                                order_success = self.dynamicCall(
                                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                    ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1, sCode,
                                     quantity, e, self.realType.SENDTYPE['거래구분']['지정가'], ""])

                                if order_success == 0:
                                    self.purchased_deposit -= total_buy_price
                                    self.order_stock_dict.update({sCode: {"사유": "매수주문 전달 성공"}})
                                    self.logging.logger.info("[%s] > 매수주문 전달 성공   [ 수량: %s / 매입단가 %s / 보유잔액: %s ]" % (
                                    sCode, quantity, e, self.purchased_deposit))
                                    self.line.notification("[%s] > 매수주문 전달 성공   [ 수량: %s / 매입단가 %s / 보유잔액: %s ]" % (
                                    sCode, quantity, e, self.purchased_deposit))
                                else:
                                    self.logging.logger.info("매수주문 전달 실패")
                            else:
                                self.logging.logger.info(
                                    "[%s] > 매수주문 불가2 [주문가능 수량 부족] [ 보유잔액: %s / 주문수량: %s / 총주문가: %s ]" % (
                                    sCode, self.purchased_deposit, quantity, total_buy_price))
                                self.not_order_stock_dict.update({sCode: {"사유": "매수주문 불가2 [주문가능 수량 부족]"}})

            if self.purchased_deposit > 0 and sCode in self.cal_target_etf_stock_dict.keys() and sCode in self.portfolio_stock_dict.keys() and sCode not in self.order_stock_dict.keys() and sCode not in self.not_order_stock_dict.keys():
                a = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['체결시간'])  # 출력 HHMMSS

                c = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['전일대비'])  # 출력 : +(-)2520
                c = abs(int(c.strip()))

                d = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['등락율'])  # 출력 : +(-)12.98
                d = float(d.strip())

                f = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['(최우선)매수호가'])  # 출력 : +(-)2515
                f = abs(int(f.strip()))

                g = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['거래량'])  # 출력 : +240124  매수일때, -2034 매도일 때
                g = abs(int(g.strip()))

                h = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['누적거래량'])  # 출력 : 240124
                h = abs(int(h.strip()))

                i = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['고가'])  # 출력 : +(-)2530
                i = abs(int(i.strip()))

                j = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['시가'])  # 출력 : +(-)2530
                j = abs(int(j.strip()))

                k = self.dynamicCall("GetCommRealData(QString, int)", sCode,
                                     self.realType.REALTYPE[sRealType]['저가'])  # 출력 : +(-)2530
                k = abs(int(k.strip()))

                self.portfolio_stock_dict[sCode].update({"체결시간": a})
                self.portfolio_stock_dict[sCode].update({"현재가": b})
                self.portfolio_stock_dict[sCode].update({"전일대비": c})
                self.portfolio_stock_dict[sCode].update({"등락율": d})
                self.portfolio_stock_dict[sCode].update({"(최우선)매도호가": e})
                self.portfolio_stock_dict[sCode].update({"(최우선)매수호가": f})
                self.portfolio_stock_dict[sCode].update({"거래량": g})
                self.portfolio_stock_dict[sCode].update({"누적거래량": h})
                self.portfolio_stock_dict[sCode].update({"고가": i})
                self.portfolio_stock_dict[sCode].update({"시가": j})
                self.portfolio_stock_dict[sCode].update({"저가": k})

                self.cal_target_etf_stock_dict[sCode].update({"당일시가": self.portfolio_stock_dict[sCode]['시가']})

                value = self.cal_target_etf_stock_dict[sCode]
                goal_stock_price = value['목표가']
                if goal_stock_price == '':
                    goal_stock_price = self.cal_goal_stock_price(code=sCode, value=value)
                    self.cal_target_etf_stock_dict[sCode].update({"목표가": goal_stock_price})
                if goal_stock_price == 0:
                    self.logging.logger.info("%s > 매수 미대상 [목표가 0원]" % sCode)
                    self.not_order_stock_dict.update({sCode: {"사유": "매수 미대상 [목표가 0원]"}})
                elif b > goal_stock_price:

                    self.logging.logger.info("%s > 매수조건 통과  목표가 : %s" % (sCode, goal_stock_price))

                    result = self.use_money / e
                    quantity = int(result)
                    total_buy_price = e * quantity
                    if quantity >= 1 and self.purchased_deposit > total_buy_price:
                        # 사용자 구분명, 화면번호, 계좌번호 10자리, 주문유형, 종목코드, 주문수량, 주문가격, 거래구분, 원주문번호
                        # 주문유형 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
                        order_success = self.dynamicCall(
                            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                            ["신규매수", self.portfolio_stock_dict[sCode]["주문용스크린번호"], self.account_num, 1, sCode, quantity, e, self.realType.SENDTYPE['거래구분']['지정가'], ""])

                        if order_success == 0:
                            self.purchased_deposit -= total_buy_price
                            self.order_stock_dict.update({sCode: {"사유": "매수주문 전달 성공"}})
                            self.logging.logger.info("[%s] > 매수주문 전달 성공   [ 수량: %s / 매입단가 %s / 보유잔액: %s ]" % (sCode, quantity, e, self.purchased_deposit))
                            self.line.notification("[%s] > 매수주문 전달 성공   [ 수량: %s / 매입단가 %s / 보유잔액: %s ]" % (sCode, quantity, e, self.purchased_deposit))
                        else:
                            self.logging.logger.info("매수주문 전달 실패")
                    else:
                        self.logging.logger.info("[%s] > 매수주문 불가 [주문가능 수량 부족] [ 보유잔액: %s / 주문수량: %s / 총주문가: %s ]" % (sCode, self.purchased_deposit, quantity, total_buy_price))
                        self.not_order_stock_dict.update({sCode: {"사유": "매수주문 불가 [주문가능 수량 부족]"}})

    def prepare_next_day(self):
        self.logging.logger.info("다음날 위한 준비 시작")
        self.line.notification("다음날 위한 준비 시작")
        self.file_delete()  # 기존 파일 삭제
        self.get_all_etf_stock()  # 장 마감 후 전체 etf 정보 가져오기 -> 거래량 충족 데이터 고가, 저가, 종가 조회
        self.get_etf_stock_info()  # 주식기본정보요청(opt10001) => 고가, 저가, 종가 -> 파일 생성

        self.line.notification("시스템 종료")
        QTest.qWait(5000)
        sys.exit()

    def cal_goal_stock_price(self, code, value):
        start_stock_price = value['당일시가']
        start_stock_price = int(start_stock_price)
        last_stock_price = value['전일종가']
        last_stock_price = int(last_stock_price)
        highest_stock_price = value['전일고가']
        highest_stock_price = int(highest_stock_price)
        lowest_stock_price = value['전일저가']
        lowest_stock_price = int(lowest_stock_price)

        if start_stock_price > last_stock_price:
            if (start_stock_price - last_stock_price) <= (highest_stock_price - lowest_stock_price):
                goal_stock_price = start_stock_price + (0.4 * (highest_stock_price - lowest_stock_price))
                goal_stock_price = round(goal_stock_price, 0)
            else:
                goal_stock_price = 0
        else:
            goal_stock_price = 0

        if goal_stock_price > 0:
            return goal_stock_price
        else:
            return 0

    def read_target_etf_file(self):
        self.logging.logger.info("전일자 대상건 파일 처리 시작")
        if os.path.exists(self.target_etf_file_path):
            f = open(self.target_etf_file_path, "r", encoding="utf8")

            lines = f.readlines()
            for line in lines:
                if line != "":
                    ls = line.split("\t")

                    stock_code = ls[0]
                    highest_stock_price = ls[2]
                    lowest_stock_price = ls[3]
                    last_stock_price = ls[4].rstrip('\n')

                    self.cal_target_etf_stock_dict.update({stock_code: {"전일고가": highest_stock_price,
                                                                        "전일저가": lowest_stock_price,
                                                                        "전일종가": last_stock_price,
                                                                        "목표가": ''}})
            f.close()
            self.logging.logger.info("전일자 대상건 파일 처리 완료")
            self.logging.logger.info(self.cal_target_etf_stock_dict)

    def stop_screen_cancel(self, sScrNo=None):
        self.logging.logger.info("stop_screen_cancel")
        self.dynamicCall("DisconnectRealData(QString)", sScrNo)

    def get_etf_stock_info(self):
        self.logging.logger.info("get_etf_stock_info")

        for sCode in self.target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def file_delete(self):
        self.logging.logger.info("file_delete")
        if os.path.isfile(self.target_etf_file_path):
            os.remove(self.target_etf_file_path)
            self.logging.logger.info("remove %s" % self.target_etf_file_path)

    def detail_account_mystock(self, sPrevNext="0"):
        self.logging.logger.info("detail_account_mystock")
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def sell_screen_number_setting(self):
        self.logging.logger.info("sell_screen_number_setting")
        screen_overwrite = []

        # 계좌평가잔고내역에 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        # 스크린 번호 할당
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
                self.sell_portfolio_stock_dict[code].update({"스크린번호": str(temp_screen)})
                self.sell_portfolio_stock_dict[code].update({"주문용스크린번호": str(meme_screen)})
            elif code not in self.sell_portfolio_stock_dict.keys():
                self.sell_portfolio_stock_dict.update({code: {"스크린번호": str(temp_screen), "주문용스크린번호": str(meme_screen)}})

            cnt += 1

        self.logging.logger.info("매도용 > %s" % self.sell_portfolio_stock_dict)

    def screen_number_setting(self):
        self.logging.logger.info("screen_number_setting")
        screen_overwrite = []

        for code in self.cal_target_etf_stock_dict.keys():
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

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(temp_screen)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(meme_screen)})
            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호": str(temp_screen), "주문용스크린번호": str(meme_screen)}})

            cnt += 1

        self.logging.logger.info("매수용 > %s" % self.portfolio_stock_dict)
