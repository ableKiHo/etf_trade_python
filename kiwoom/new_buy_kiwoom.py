import copy
import math
import sys
from operator import itemgetter

from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import *


class NewBuyKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF New BuyKiwoom() class start.")
        self.line.notification("ETF New BuyKiwoom() class start.")

        self.analysis_etf_file_path = self.property.analysisEtfFilePath
        self.sell_analysis_etf_file_path = self.property.sellAnalysisEtfFIlePath

        self.analysis_etf_target_dict = {}  # 120틱 과 20선 구할 대상용
        self.all_etf_stock_list = []
        self.buy_point_dict = {}
        self.target_etf_stock_dict = {}
        self.top_rank_etf_stock_list = []

        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린 번호
        self.buy_screen_meme_stock = "3000"  # 종목별 할당할 주문용 스크린 번호
        self.buy_screen_real_stock = "6000"  # 종별별 할당할 스크린 번호
        self.sell_screen_meme_stock = "4000"
        self.screen_opt10079_info = "7000"
        self.screen_all_etf_stock = "8000"
        self.screen_etf_stock = "5000"

        self.max_plus_sell_std_percent = 3

        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결

        self.line.notification("ETF NEW BUY TRADE START")
        self.etf_info_event_loop = QEventLoop()
        self.tr_opt10079_info_event_loop = QEventLoop()
        self.all_etf_info_event_loop = QEventLoop()

        self.detail_account_info()
        QTest.qWait(5000)
        self.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL")

        self.prepare_search_buy_etf()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.new_chejan_slot)

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


            if meme_gubun == '매도' and holding_quantity == 0:
                self.buy_point_dict = {}
                self.logging.logger.info("call prepare_search_buy_etf at new_chejan_slot")
                self.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL")
                self.prepare_search_buy_etf()
            else:
                self.logging.logger.info("call search_buy_etf at new_chejan_slot")
                self.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL")
                self.search_buy_etf()

    def screen_number_setting(self, code, stock_dict):
        stock_dict.update({self.customType.SCREEN_NUMBER: self.buy_screen_real_stock})
        stock_dict.update({self.customType.MEME_SCREEN_NUMBER: self.buy_screen_meme_stock})
        stock_dict.update({self.customType.SELL_MEME_SCREEN_NUMBER: self.sell_screen_meme_stock})

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info('trdata_slot %s / %s' % (sRQName, sPrevNext))
        if sRQName == self.customType.OPW00001:
            self.trdata_slot_opw00001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == "tr_opt10079":
            self.trdata_slot_opt10079(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT40004:
            self.trdata_slot_opt40004(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def get_all_etf_stock(self, sPrevNext="0"):
        self.logging.logger.info("get_all_etf_stock %s " % sPrevNext)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TAXATION_TYPE, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.COMPARED_TO_NAV, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MANAGER, "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40004, "opt40004", sPrevNext, self.screen_all_etf_stock)

        self.all_etf_info_event_loop.exec_()

    def get_top_rank_etf_stock(self):
        return sorted(self.all_etf_stock_list, key=itemgetter(self.customType.VOLUME), reverse=True)[:5]

    def detail_account_info(self, sPrevNext="0"):
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)
        self.detail_account_info_event_loop.exec_()

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

    def realdata_slot(self, sCode, sRealType, sRealData):
        if sRealType == self.customType.MARKET_START_TIME:
            fid = self.realType.REALTYPE[sRealType][self.customType.MARKET_OPERATION]
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)
            if value == '4':
                self.logging.logger.info(self.logType.MARKET_END_LOG)
                self.line.notification(self.logType.MARKET_END_LOG)

                for code in self.analysis_etf_target_dict.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.buy_screen_real_stock, code)

                self.line.notification("시스템 종료")
                sys.exit()

    """def comm_real_data(self, sCode, sRealType, sRealData):
        target_etf_stock_dict = {}
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

        target_etf_stock_dict.update({self.customType.TIGHTENING_TIME: a})
        target_etf_stock_dict.update({self.customType.CURRENT_PRICE: b})
        target_etf_stock_dict.update({self.customType.THE_DAY_BEFORE: c})
        target_etf_stock_dict.update({self.customType.SELLING_QUOTE: e})
        target_etf_stock_dict.update({self.customType.BID: f})
        target_etf_stock_dict.update({self.customType.VOLUME: g})
        target_etf_stock_dict.update({self.customType.CUMULATIVE_VOLUME: h})
        target_etf_stock_dict.update({self.customType.HIGHEST_PRICE: i})
        target_etf_stock_dict.update({self.customType.START_PRICE: j})
        target_etf_stock_dict.update({self.customType.LOWEST_PRICE: k})
        target_etf_stock_dict.update({self.customType.CURRENT_START_PRICE: target_etf_stock_dict[self.customType.START_PRICE]})

        return target_etf_stock_dict """

    def get_opt10079_info(self, code):
        self.logging.logger.info('get_opt10079_info > [%s]' % code)
        self.tr_opt10079_info(code)

    def tr_opt10079_info(self, code, sPrevNext="0"):
        self.logging.logger.info('tr_opt10079_info > [%s]' % code)
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "120틱")
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
        # self.logging.logger.info("analysis_etf_target_dict > [%s] > %s" % (stock_code, self.analysis_etf_target_dict[stock_code]))

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

    def create_moving_average_20_line(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        gap = 20
        max_decimal_point = 3
        for i in range(len(rows)):
            max_ma_20_len = i + gap
            if len(rows) < max_ma_20_len:
                max_ma_20_len = len(rows)
            ma_20_list = copy.deepcopy(rows[i: max_ma_20_len])
            if len(ma_20_list) < gap:
                break
            ma_20_value = 0
            for sub_i in range(len(ma_20_list)):
                sub_row = ma_20_list[sub_i]
                ma_20_value = ma_20_value + sub_row[self.customType.CURRENT_PRICE]

            row = rows[i]
            row["ma20"] = round(ma_20_value / gap, max_decimal_point)

    def prepare_search_buy_etf(self):
        self.logging.logger.info('prepare_search_buy_etf')
        self.all_etf_stock_list = []
        QTimer.singleShot(5000, self.get_all_etf_stock())
        self.top_rank_etf_stock_list = self.get_top_rank_etf_stock()
        self.search_buy_etf()

    def search_buy_etf(self):
        self.logging.logger.info('search_buy_etf')
        today = get_today_by_format('%Y%m%d')
        breaker = False
        while True:
            self.logging.logger.info('search_buy_etf while start %s' % self.buy_point_dict)
            if bool(self.buy_point_dict):
                self.logging.logger.info('search_buy_etf buy info %s' % self.buy_point_dict)
                if self.customType.ORDER_EXECUTION not in self.buy_point_dict.keys():
                    continue

                code = self.buy_point_dict[self.customType.STOCK_CODE]
                QTimer.singleShot(5000, self.get_opt10079_info(code))
                self.create_moving_average_20_line(code)
                rows = self.analysis_etf_target_dict[code]["row"]
                prepare = self.prepare_sell_send_order(code, rows[0])
                if prepare == 'SellCase':
                    self.logging.logger.info("SellCase prepare_sell_send_order [%s]>  %s " % (code, prepare))
                    self.sell_send_order(code, self.buy_point_dict[self.customType.SELL_MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
                    break
                result = self.get_sell_point(rows[:4])
                self.logging.logger.info('sell point info >> %s / %s' % (rows, result))
                if result == 'SellCase':
                    self.logging.logger.info("get_sell_point call stock_real_reg [%s]>  %s " % (code, result))
                    self.sell_send_order(code, self.buy_point_dict[self.customType.SELL_MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
                    break
            else:
                currentDate = get_today_by_format('%Y%m%d%H%M%S')
                if (today + '143000') <= currentDate and not bool(self.buy_point_dict):
                    break

                self.logging.logger.info("top_rank_etf_stock_list > %s " % self.top_rank_etf_stock_list)
                for item in self.top_rank_etf_stock_list:
                    code = item[self.customType.STOCK_CODE]
                    self.logging.logger.info("top_rank_etf_stock_list loop > %s " % code)

                    QTimer.singleShot(5000, self.get_opt10079_info(code))
                    self.create_moving_average_20_line(code)
                    buy_point = self.get_buy_point(code)
                    if bool(buy_point):
                        self.prepare_send_order(code, buy_point)
                        breaker = True
                        self.logging.logger.info("buy_point break")
                        break

                    first_buy_point = self.get_conform_first_buy_case(code)
                    if bool(first_buy_point):
                        self.prepare_send_order(code, first_buy_point)
                        breaker = True
                        self.logging.logger.info("first_buy_point break")
                        break
                    seconf_buy_point = self.get_conform_second_buy_case(code)
                    if bool(seconf_buy_point):
                        self.prepare_send_order(code, seconf_buy_point)
                        breaker = True
                        self.logging.logger.info("second_buy_point break")
                        break
                    third_buy_point = self.get_conform_third_buy_case(code)
                    if bool(third_buy_point):
                        self.prepare_send_order(code, third_buy_point)
                        breaker = True
                        self.logging.logger.info("third_buy_point break")
                        break

                if breaker:
                    self.logging.logger.info("break search_buy_etf()")
                    break
            self.logging.logger.info('search_buy_etf while end %s' % self.buy_point_dict)

    def prepare_sell_send_order(self, code, current_dict):
        result = ''
        self.logging.logger.info("prepare_sell_send_order [%s]>> %s" % (code, current_dict))
        minus_sell_std_price = get_minus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE])
        if current_dict[self.customType.CURRENT_PRICE] < minus_sell_std_price:
            self.logging.logger.info("sell_send_order at realdata_slot() [%s] > %s / %s" % (code, current_dict[self.customType.CURRENT_PRICE], minus_sell_std_price))
            result = "SellCase"

        return result

    def prepare_send_order(self, code, buy_point):
        buy_point.update({self.customType.STOCK_CODE: code})
        self.logging.logger.info("buy_point > %s " % buy_point)
        self.buy_point_dict = copy.deepcopy(buy_point)
        self.screen_number_setting(code, self.buy_point_dict)
        limit_stock_price = int(self.buy_point_dict[self.customType.CURRENT_PRICE])
        result = self.use_money / limit_stock_price
        quantity = int(result)
        if quantity >= 1:
            self.logging.logger.info("quantity > %s " % quantity)
            self.send_order_limit_stock_price(code, quantity, limit_stock_price, self.buy_point_dict)

    """def stock_real_reg(self, code, stock_dict):
        self.logging.logger.info("stock_real_reg > %s " % code)
        screen_num = stock_dict[self.customType.SCREEN_NUMBER]
        fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "0")"""

    def get_sell_point(self, rows):
        first_low = rows[0]
        second_low = rows[1]
        third_low = rows[2]
        forth_low = rows[3]
        if first_low[self.customType.CURRENT_PRICE] > get_max_plus_sell_std_price_by_std_per(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], self.max_plus_sell_std_percent):
            return 'SellCase'
        if first_low[self.customType.CURRENT_PRICE] > self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE]:
            if second_low[self.customType.LOWEST_PRICE] < second_low["ma20"] < second_low[self.customType.HIGHEST_PRICE]:
                return 'SellCase'
            if second_low[self.customType.CURRENT_PRICE] <= second_low["ma20"] and second_low[self.customType.START_PRICE] > second_low[self.customType.CURRENT_PRICE]:
                return 'SellCase'
            if forth_low[self.customType.START_PRICE] > forth_low[self.customType.CURRENT_PRICE] and third_low[self.customType.START_PRICE] > third_low[self.customType.CURRENT_PRICE] and second_low[
                self.customType.START_PRICE] > second_low[self.customType.CURRENT_PRICE]:
                return 'SellCase'
            if first_low[self.customType.LOWEST_PRICE] <= first_low["ma20"] <= first_low[self.customType.HIGHEST_PRICE] and first_low[self.customType.START_PRICE] > first_low[
                self.customType.CURRENT_PRICE]:
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
        lower_ma20_list = [x for x in other_tics if x["ma20"] > first_tic["ma20"]]
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
        #self.logging.logger.info("first_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))

        first_tic = analysis_rows[0]
        secode_tic = analysis_rows[1]
        third_tic = analysis_rows[2]
        forth_tic = analysis_rows[3]
        fifth_tic = analysis_rows[4]
        other_tics = analysis_rows[1:2]

        empty_ma20_list = [x for x in analysis_rows if x["ma20"] == '']
        if len(empty_ma20_list) > 0:
            self.logging.logger.info("empty_ma20_list > [%s] >> %s / %s  " % (code, first_tic[self.customType.TIGHTENING_TIME], empty_ma20_list))
            return {}

        if first_tic[self.customType.LOWEST_PRICE] > first_tic["ma20"]:
            if secode_tic[self.customType.LOWEST_PRICE] < secode_tic["ma20"] < secode_tic[self.customType.HIGHEST_PRICE] or secode_tic[self.customType.LOWEST_PRICE] >= secode_tic["ma20"]:
                if third_tic[self.customType.LOWEST_PRICE] < third_tic["ma20"] < third_tic[self.customType.HIGHEST_PRICE] or third_tic[self.customType.HIGHEST_PRICE] <= third_tic["ma20"]:
                    if forth_tic[self.customType.HIGHEST_PRICE] < forth_tic["ma20"] and fifth_tic[self.customType.HIGHEST_PRICE] < fifth_tic["ma20"]:
                        if forth_tic[self.customType.CURRENT_PRICE] <= third_tic[self.customType.CURRENT_PRICE] <= secode_tic[self.customType.CURRENT_PRICE] <= first_tic[self.customType.START_PRICE]:
                            if third_tic[self.customType.START_PRICE] < third_tic[self.customType.CURRENT_PRICE] and secode_tic[self.customType.START_PRICE] < secode_tic[self.customType.CURRENT_PRICE] and first_tic[self.customType.START_PRICE] < first_tic[self.customType.CURRENT_PRICE]:
                                if first_tic["ma20"] >= secode_tic["ma20"]:
                                    return copy.deepcopy(first_tic)

        return {}

    def get_conform_second_buy_case(self, code):
        # self.logging.logger.info("get_conform_second_buy_case analysis_rows > [%s] " % code)
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 8:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:8]
        self.logging.logger.info("second_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))
        compare_rows = analysis_rows[1:]
        first_tic = analysis_rows[0]
        compare_tic = copy.deepcopy(first_tic)
        breaker = False
        for x in compare_rows:
            if math.trunc(compare_tic["ma20"]) < math.trunc(x["ma20"]):
                breaker = True
                break
            compare_tic = copy.deepcopy(x)
        if not breaker:
            second_tic = analysis_rows[1]
            if second_tic[self.customType.LOWEST_PRICE] < second_tic["ma20"]:
                breaker = True
        if not breaker:
            compare_rows = analysis_rows[2:]
            for x in compare_rows:
                if x[self.customType.LOWEST_PRICE] > x["ma20"]:
                    breaker = True
                    break
        if not breaker:
            first_tic = analysis_rows[0]
            second_tic = analysis_rows[1]
            if first_tic[self.customType.START_PRICE] < second_tic[self.customType.CURRENT_PRICE]:
                breaker = True
            elif first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
                breaker = True

        if not breaker:
            return first_tic
        return {}

    def get_conform_third_buy_case(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 8:
            self.logging.logger.info("analysis count > [%s] >> %s  " % (code, rows))
            return {}

        analysis_rows = rows[:6]
        self.logging.logger.info("third_buy_case analysis_rows > [%s] >> %s " % (code, analysis_rows))
        compare_rows = analysis_rows[1:]
        first_tic = analysis_rows[0]
        compare_tic = copy.deepcopy(first_tic)
        breaker = False
        for x in compare_rows:
            if math.trunc(compare_tic["ma20"]) < math.trunc(x["ma20"]):
                breaker = True
                break
            compare_tic = copy.deepcopy(x)

        if not breaker:
            first_tic = analysis_rows[0]
            second_tic = analysis_rows[1]
            if first_tic[self.customType.START_PRICE] < second_tic[self.customType.CURRENT_PRICE]:
                breaker = True
            elif first_tic[self.customType.CURRENT_PRICE] < first_tic["ma20"]:
                breaker = True
        if not breaker:
            for x in compare_rows:
                if x[self.customType.START_PRICE] > x[self.customType.CURRENT_PRICE]:
                    breaker = True
                    break
        if not breaker:
            compare_rows = analysis_rows[2:]
            compare_tic1 = copy.deepcopy(copy.deepcopy(analysis_rows[1]))
            for x in compare_rows:
                if math.trunc(compare_tic1[self.customType.CURRENT_PRICE]) < math.trunc(x[self.customType.CURRENT_PRICE]):
                    breaker = True
                    break
                compare_tic1 = copy.deepcopy(x)

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
