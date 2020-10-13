import configparser


class Property():
    def __init__(self):
        self.property = configparser.ConfigParser()
        self.property.read('properties/etf_property.ini')

        self.tokenfilePath = self.property['FILE']['TOKEN_FILE_PATH']
        self.targetEtfFilePath = self.property['FILE']['TARGET_ETF_FILE_PATH']
        self.analysisEtfFilePath = self.property['FILE']['ANALYSIS_ETF_FILE_PATH']
        self.sellAnalysisEtfFIlePath = self.property['FILE']['SELL_ANALYSIS_ETF_FILE_PATH']
        self.holdEtfFilePath = self.property['FILE']['HOLD_ETF_FILE_PATH']
        self.targetEtfFileHistoryPath = self.property['FILE']['TARGET_ETF_FILE_HISTORY_PATH']
        self.account = self.property['KIWOOM']['ACCOUNT']
        self.accountPw = self.property['KIWOOM']['PASSWORD']