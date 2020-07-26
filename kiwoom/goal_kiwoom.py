import os
import sys

from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom
from kiwoom.util_kiwoom import cal_goal_stock_price


class GoalKiwoom(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF GoalKiwoom() class start.")



        self.tr_opt10079_info_event_loop = QEventLoop()
        self.etf_info_event_loop = QEventLoop()

        self.cal_target_etf_stock_dict = {}
        a = self.cal_target_etf_stock_dict["test"]

        self.event_slots()  # 키움과 연결하기 위한 시그널 / 슬롯 모음

        self.screen_etf_stock = "5000"

        self.read_target_etf_file()  # 대상 ETF(파일) 읽기
        self.get_etf_stock_info()
        self.get_goal_price_etf()
        self.logging_reach_goal_price_etf()
        self.logging.logger.info("ETF GoalKiwoom() class end.")
        sys.exit()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.START_PRICE)
        current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        highest_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.HIGHEST_PRICE)

        self.cal_target_etf_stock_dict[code].update({self.customType.START_PRICE: abs(int(start_price.strip()))})
        self.cal_target_etf_stock_dict[code].update({self.customType.LAST_PRICE: abs(int(current_price.strip()))})
        self.cal_target_etf_stock_dict[code].update({self.customType.HIGHEST_PRICE: abs(int(highest_price.strip()))})

        self.etf_info_event_loop.exit()

    def get_goal_price_etf(self):
        self.logging.logger.info("get_goal_price_etf")
        for code in self.cal_target_etf_stock_dict.keys():
            value = self.cal_target_etf_stock_dict[code]
            goal_stock_price = cal_goal_stock_price(value[self.customType.START_PRICE], value[self.customType.LAST_DAY_LAST_PRICE], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                                                    value[self.customType.LAST_DAY_LOWEST_PRICE])
            if goal_stock_price > 0:
                self.logging.logger.info("get_goal_price_etf [%s] > %s" % (code, goal_stock_price))
            self.cal_target_etf_stock_dict[code].update({self.customType.GOAL_PRICE: goal_stock_price})

    def logging_reach_goal_price_etf(self):
        self.logging.logger.info("logging_reach_goal_price_etf")
        for code in self.cal_target_etf_stock_dict.keys():
            value = self.cal_target_etf_stock_dict[code]
            if 0 < value[self.customType.GOAL_PRICE] <= value[self.customType.LAST_PRICE] and value[self.customType.GOAL_PRICE] <= value[self.customType.HIGHEST_PRICE]:
                self.logging.logger.info("reach_goal_price_etf [%s] > GOAL_PRICE : %s / LAST_PRICE: %s / HIGHEST_PRICE: %s" % (code, value[self.customType.GOAL_PRICE], value[self.customType.LAST_PRICE], value[self.customType.HIGHEST_PRICE]))

    def get_etf_stock_info(self):
        self.logging.logger.info("get_etf_stock_info")

        for sCode in self.cal_target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

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

                    self.cal_target_etf_stock_dict.update({stock_code: {self.customType.STOCK_NAME: stock_name,
                                                                        self.customType.LAST_DAY_HIGHEST_PRICE: highest_stock_price,
                                                                        self.customType.LAST_DAY_LOWEST_PRICE: lowest_stock_price,
                                                                        self.customType.LAST_DAY_LAST_PRICE: last_stock_price,
                                                                        self.customType.THE_DAY_BEFORE_AVG: avg_the_day_before_price,
                                                                        self.customType.THE_DAY_BEFORE_MAX: max_the_day_before_price,
                                                                        self.customType.THE_DAY_BEFORE_MIN: min_the_day_before_price,
                                                                        self.customType.GOAL_PRICE: ''}})

            f.close()
            self.logging.logger.info("전일자 대상건 파일 처리 완료 > %s" % self.cal_target_etf_stock_dict)
