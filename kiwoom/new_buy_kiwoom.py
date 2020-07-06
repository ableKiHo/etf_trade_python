import copy
import sys
from operator import itemgetter

from PyQt5.QtCore import QEventLoop
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

        self.screen_start_stop_real = "1000"  # 장 시작/종료 실시간 스크린 번호
        self.buy_screen_meme_stock = "3000"  # 종목별 할당할 주문용 스크린 번호
        self.buy_screen_real_stock = "6000"  # 종별별 할당할 스크린 번호
        self.sell_screen_meme_stock = "4000"
        self.screen_opt10079_info = "7000"
        self.screen_all_etf_stock = "8000"

        self.max_plus_sell_std_percent = 3

        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결

        self.line.notification("ETF NEW BUY TRADE START")
        self.etf_info_event_loop = QEventLoop()
        self.tr_opt10079_info_event_loop = QEventLoop()

        self.detail_account_info()
        QTest.qWait(5000)

        self.search_buy_etf()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.new_chejan_slot)

    def new_chejan_slot(self, sGubun, nItemCnt, sFidList):
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

            self.logging.logger.info(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))
            self.line.notification(self.logType.CHEJAN_STATUS_LOG % (meme_gubun, sCode, stock_name, holding_quantity, available_quantity, buy_price, total_buy_price, income_rate))

            if meme_gubun == '매도' and holding_quantity == 0:
                self.buy_point_dict = {}
                self.search_buy_etf()

    def screen_number_setting(self, code, stock_dict):
        stock_dict[code].update({self.customType.SCREEN_NUMBER: self.buy_screen_real_stock})
        stock_dict[code].update({self.customType.MEME_SCREEN_NUMBER: self.buy_screen_meme_stock})
        stock_dict[code].update({self.customType.SELL_MEME_SCREEN_NUMBER: self.sell_screen_meme_stock})

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
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

        if sPrevNext == "0":
            self.all_etc_info_event_loop.exec_()

    def get_top10_etf_stock(self):
        return sorted(self.all_etf_stock_list, key=itemgetter(self.customType.VOLUME), reverse=True)[:10]

    def detail_account_info(self, sPrevNext="0"):
        QTest.qWait(5000)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.ACCOUNT_NUMBER, self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.PASSWORD, self.account_pw)
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION_OF_PASSWORD_INPUT_MEDIA, "00")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.CLASSIFICATION, "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPW00001, "opw00001", sPrevNext, self.screen_my_info)
        self.detail_account_info_event_loop.exec_()

    def trdata_slot_opt40004(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        self.logging.logger.info("trdata_slot_opt40004 %s / %s" % (sScrNo, sPrevNext))
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
            self.all_etc_info_event_loop.exit()

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

                QTest.qWait(5000)
                self.line.notification("시스템 종료")
                sys.exit()
        elif sRealType == self.customType.STOCK_CONCLUSION:
            if self.customType.HOLDING_QUANTITY in self.buy_point_dict and self.buy_point_dict[self.customType.HOLDING_QUANTITY] > 0:
                target_etf_stock_dict = self.comm_real_data(sCode, sRealType, sRealData)
                minus_sell_std_price = get_minus_sell_std_price(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE])
                if target_etf_stock_dict[self.customType.CURRENT_PRICE] > self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE]:
                    self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], sCode)
                    self.search_buy_etf()
                if target_etf_stock_dict[self.customType.CURRENT_PRICE] < minus_sell_std_price:
                    order_success = self.sell_send_order(sCode, self.buy_point_dict[self.customType.SELL_MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
                    if order_success == 0:
                        self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], sCode)

    def comm_real_data(self, sCode, sRealType, sRealData):
        target_etf_stock_dict = {sCode: {}}
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

        target_etf_stock_dict[sCode].update({self.customType.TIGHTENING_TIME: a})
        target_etf_stock_dict[sCode].update({self.customType.CURRENT_PRICE: b})
        target_etf_stock_dict[sCode].update({self.customType.THE_DAY_BEFORE: c})
        target_etf_stock_dict[sCode].update({self.customType.SELLING_QUOTE: e})
        target_etf_stock_dict[sCode].update({self.customType.BID: f})
        target_etf_stock_dict[sCode].update({self.customType.VOLUME: g})
        target_etf_stock_dict[sCode].update({self.customType.CUMULATIVE_VOLUME: h})
        target_etf_stock_dict[sCode].update({self.customType.HIGHEST_PRICE: i})
        target_etf_stock_dict[sCode].update({self.customType.START_PRICE: j})
        target_etf_stock_dict[sCode].update({self.customType.LOWEST_PRICE: k})
        target_etf_stock_dict[sCode].update({self.customType.CURRENT_START_PRICE: target_etf_stock_dict[sCode][self.customType.START_PRICE]})

        return target_etf_stock_dict

    def get_opt10079_info(self, code):
        self.logging.logger.info('get_opt10079_info > [%s]' % code)
        QTest.qWait(5000)
        self.tr_opt10079_info(code)

    def tr_opt10079_info(self, code, sPrevNext="0"):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "120틱")
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "tr_opt10079", "opt10079", sPrevNext, self.screen_opt10079_info)

        self.tr_opt10079_info_event_loop.exec_()

    def trdata_slot_opt10079(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):

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

    def search_buy_etf(self):
        self.logging.logger.info('search_buy_etf')

        while True:
            if bool(self.buy_point_dict):
                QTest.qWait(5000)
                code = self.buy_point_dict[self.customType.STOCK_CODE]
                self.get_opt10079_info(code)
                self.create_moving_average_20_line(code)
                rows = self.analysis_etf_target_dict[code]["row"]
                result = self.get_sell_point(rows[0])
                if result is None:
                    continue
                else:
                    self.stock_real_reg(code, self.buy_point_dict)
                    if result == 'SellCase':
                        self.sell_send_order(code, self.buy_point_dict[self.customType.SELL_MEME_SCREEN_NUMBER], self.buy_point_dict[self.customType.HOLDING_QUANTITY])
                    break
            else:
                self.all_etf_stock_list = []
                self.get_all_etf_stock()
                # QTest.qWait(5000)
                top_10_etf_stock_list = self.get_top10_etf_stock()
                self.logging.logger.info("top_10_etf_stock_list > %s " % top_10_etf_stock_list)
                for item in top_10_etf_stock_list:
                    code = item[self.customType.STOCK_CODE]
                    QTest.qWait(5000)
                    self.get_opt10079_info(code)
                    self.create_moving_average_20_line(code)
                    buy_point = self.get_buy_point(code)
                    if buy_point != '':
                        buy_point.update({self.customType.STOCK_CODE: code})
                        self.logging.logger.info("buy_point > %s " % buy_point)
                        self.buy_point_dict = buy_point
                        self.screen_number_setting(code, self.buy_point_dict)
                        limit_stock_price = int(self.buy_point_dict[self.customType.CURRENT_PRICE])
                        result = self.use_money / limit_stock_price
                        quantity = int(result)
                        if quantity >= 1:
                            self.stock_real_reg(code, self.buy_point_dict)
                            order_success = self.send_order_limit_stock_price(code, quantity, limit_stock_price, self.buy_point_dict)
                            if order_success == 0:
                                self.dynamicCall("SetRealRemove(QString, QString)", self.buy_point_dict[self.customType.SCREEN_NUMBER], code)

    def stock_real_reg(self, code, stock_dict):
        screen_num = stock_dict[self.customType.SCREEN_NUMBER]
        fids = self.realType.REALTYPE[self.customType.STOCK_CONCLUSION][self.customType.TIGHTENING_TIME]
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def get_sell_point(self, last_row):
        if last_row[self.customType.CURRENT_PRICE] < self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE] and last_row[self.customType.CURRENT_PRICE] < last_row["ma20"]:
            return 'RealRegCase'
        if last_row[self.customType.CURRENT_PRICE] > self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE] and last_row[self.customType.HIGHEST_PRICE] < last_row["ma20"]:
            return 'SellCase'
        if last_row[self.customType.CURRENT_PRICE] > get_max_plus_sell_std_price_by_std_per(self.buy_point_dict[self.customType.PURCHASE_UNIT_PRICE], self.max_plus_sell_std_percent):
            return 'SellCase'

        return None

    def get_buy_point(self, code):
        rows = self.analysis_etf_target_dict[code]["row"]
        if len(rows) < 5:
            return ''
        analysis_rows = rows[:5]
        self.logging.logger.info("analysis_rows > [%s] >> %s " % (code, analysis_rows))
        today = get_today_by_format('%Y%m%d')
        first_tic = analysis_rows[0]
        other_tics = analysis_rows[1:]
        if first_tic[self.customType.TIGHTENING_TIME] < (today + '094000') or first_tic[self.customType.TIGHTENING_TIME] > (today + '151000'):
            return ''
        if first_tic["ma20"] == '':
            return ''
        if first_tic[self.customType.LOWEST_PRICE] <= first_tic["ma20"]:
            return ''
        higher_ma20_list = [x for x in other_tics if x[self.customType.LOWEST_PRICE] > x["ma20"]]
        if len(higher_ma20_list) > 0:
            return ''

        return first_tic

    def send_order_limit_stock_price(self, code, quantity, limit_stock_price, stock_dict):
        order_success = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [self.customType.NEW_PURCHASE, stock_dict[code][self.customType.MEME_SCREEN_NUMBER], self.account_num, 1, code, quantity, limit_stock_price,
             self.realType.SENDTYPE[self.customType.TRANSACTION_CLASSIFICATION][self.customType.LIMITS], ""])

        if order_success == 0:
            self.logging.logger.info(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity, limit_stock_price, self.purchased_deposit))
            self.line.notification(
                self.logType.ORDER_BUY_SUCCESS_STATUS_LOG % (code, quantity, limit_stock_price, self.purchased_deposit))
        else:
            self.logging.logger.info(self.logType.ORDER_BUY_FAIL_LOG)
        return order_success
