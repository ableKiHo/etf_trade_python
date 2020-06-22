import os
import sys
import numpy as np

from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest

from kiwoom.parent_kiwoom import ParentKiwoom


class PrepareNextDay(ParentKiwoom):
    def __init__(self):
        super().__init__()

        self.logging.logger.info("ETF PrepareNextDay() class start.")
        self.line.notification("ETF PrepareNextDay() class start.")

        self.all_etc_info_event_loop = QEventLoop()
        self.etf_info_event_loop = QEventLoop()
        self.etf_day_info_event_loop = QEventLoop()

        self.screen_all_etf_stock = "4000"
        self.screen_etf_stock = "5000"
        self.screen_etf_day_stock = "4050"

        self.target_etf_stock_dict = {}
        self.target_etf_day_info_dict = []
        self.event_slots()

        self.line.notification("ETF PREPARE AUTO TRADE START")
        self.prepare_next_day()

    def event_slots(self):
        self.OnReceiveTrData.connect(self.trdata_slot)
        self.OnReceiveMsg.connect(self.msg_slot)

    def prepare_next_day(self):
        self.logging.logger.info("다음날 위한 준비 시작")
        self.file_delete()
        self.get_all_etf_stock()
        self.get_etf_stock_info()
        self.get_etf_day_stock_info()

        QTest.qWait(5000)
        self.createTargetEtfStockFile()

        self.line.notification("시스템 종료")
        QTest.qWait(5000)
        sys.exit()

    def file_delete(self):
        self.logging.logger.info("file_delete")
        if os.path.isfile(self.target_etf_file_path):
            os.remove(self.target_etf_file_path)
            self.logging.logger.info("remove %s" % self.target_etf_file_path)

    def get_all_etf_stock(self, sPrevNext="0"):
        self.logging.logger.info("get_all_etf_stock")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.TAXATION_TYPE, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.COMPARED_TO_NAV, "0")
        self.dynamicCall("SetInputValue(QString, QString)", self.customType.MANAGER, "0000")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40004, "opt40004", sPrevNext, self.screen_all_etf_stock)

        self.all_etc_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        if sRQName == self.customType.OPT40004:
            self.trdata_slot_opt40004(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT10001:
            self.trdata_slot_opt10001(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)
        elif sRQName == self.customType.OPT40003:
            self.trdata_slot_opt40003(sScrNo, sRQName, sTrCode, sRecordName, sPrevNext)

    def trdata_slot_opt40003(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        compareLastDayList = []
        for i in range(rows):
            compareLastDay = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.THE_DAY_BEFORE)
            compareLastDay = compareLastDay.strip()
            if int(compareLastDay) > 0:
                compareLastDayList.append(int(compareLastDay))
        avgValue = round(int(np.mean(compareLastDayList)))
        maxValue = np.max(compareLastDayList)
        minValue = np.min(compareLastDayList)
        for code in self.target_etf_day_info_dict:
            self.target_etf_stock_dict[code].update({self.customType.THE_DAY_BEFORE_AVG: avgValue})
            self.target_etf_stock_dict[code].update({self.customType.THE_DAY_BEFORE_MAX: maxValue})
            self.target_etf_stock_dict[code].update({self.customType.THE_DAY_BEFORE_MIN: minValue})
            self.logging.logger.info(self.logType.OPT40003_STATUS_LOG % (code, avgValue, maxValue, minValue))
        del self.target_etf_day_info_dict[:]

        self.stop_screen_cancel(self.screen_etf_day_stock)
        self.etf_day_info_event_loop.exit()

    def trdata_slot_opt40004(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
        for i in range(rows):
            volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.VOLUME)
            volume = volume.strip()
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_CODE)
            code = code.strip()
            if int(volume) >= 100000:
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, self.customType.STOCK_NAME)
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

    def trdata_slot_opt10001(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_CODE)
        code = code.strip()
        code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.STOCK_NAME)
        highest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.HIGHEST_PRICE)
        lowest_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.LOWEST_PRICE)
        last_stock_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.CURRENT_PRICE)
        change_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.THE_DAY_BEFORE)

        market_cap = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, self.customType.MARTKET_CAP)
        market_cap = market_cap.strip()

        self.logging.logger.info(self.logType.OPT10001_STATUS_LOG % (
            code, highest_stock_price.strip(), lowest_stock_price.strip(), last_stock_price.strip(), change_price.strip(), market_cap)
        )

        self.target_etf_stock_dict[code].update({self.customType.STOCK_NAME: code_nm})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_HIGHEST_PRICE: abs(int(highest_stock_price.strip()))})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LOWEST_PRICE: abs(int(lowest_stock_price.strip()))})
        self.target_etf_stock_dict[code].update({self.customType.LAST_DAY_LAST_PRICE: abs(int(last_stock_price.strip()))})
        self.target_etf_stock_dict[code].update({self.customType.MARTKET_CAP: int(market_cap)})

        self.etf_info_event_loop.exit()

    def isTragetEtfStock(self, value):
        return int(value[self.customType.MARTKET_CAP]) >= 130

    def createTargetEtfStockFile(self):
        self.logging.logger.info("createTargetEtfStockFile")
        for sCode in self.target_etf_stock_dict.keys():
            value = self.target_etf_stock_dict[sCode]
            if self.isTragetEtfStock(value):
                f = open(self.target_etf_file_path, "a", encoding="utf8")
                f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %
                        (sCode, value[self.customType.STOCK_NAME], value[self.customType.LAST_DAY_HIGHEST_PRICE],
                         value[self.customType.LAST_DAY_LOWEST_PRICE], value[self.customType.LAST_DAY_LAST_PRICE],
                         value[self.customType.THE_DAY_BEFORE_AVG], value[self.customType.THE_DAY_BEFORE_MAX],
                         value[self.customType.THE_DAY_BEFORE_MIN]))
                f.close()

    def get_etf_stock_info(self):
        self.logging.logger.info("get_etf_stock_info")

        for sCode in self.target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT10001, "opt10001", 0, self.screen_etf_stock)
            self.etf_info_event_loop.exec_()

    def get_etf_day_stock_info(self):
        self.logging.logger.info("get_etf_day_stock_info")

        for sCode in self.target_etf_stock_dict.keys():
            QTest.qWait(4000)
            self.target_etf_day_info_dict.append(sCode)
            self.dynamicCall("SetInputValue(QString, QString)", self.customType.STOCK_CODE, sCode)
            self.dynamicCall("CommRqData(QString, QString, int, QString)", self.customType.OPT40003, "OPT40003", 0, self.screen_etf_day_stock)
            self.etf_day_info_event_loop.exec_()
