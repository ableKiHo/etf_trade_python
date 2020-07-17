import argparse

from PyQt5.QtWidgets import *

from config.lineNotify import LineNotify
from config.log_class import Logging
from kiwoom.buy_kiwoom import *
from kiwoom.goal_kiwoom import GoalKiwoom
from kiwoom.prepare_next_day import PrepareNextDay
from kiwoom.renewal_buy_kiwoom import RenewalBuyKiwoom
from kiwoom.sell_kiwoom import SellKiwoom

sys.path.append("D:/PycharmProjects/etf/")

class Main():
    def __init__(self):
        print("Main() start")
        self.logging = Logging()
        self.line = LineNotify()
        parser = argparse.ArgumentParser()
        parser.add_argument('--type', required=True)
        args = parser.parse_args()
        auto_type = args.type

        print("AUTO ETF TYPE %s" % auto_type)

        self.app = QApplication(sys.argv)
        if auto_type == 'sell':
            self.sellKiwoom = SellKiwoom()
        elif auto_type == 'buy':
            try:
                # self.kiwoom = BuyKiwoom()
                # self.kiwoom = NewBuyKiwoom()
                self.kiwoom = RenewalBuyKiwoom()
            except Exception as e:
                self.logging.logger.error('Exception', exc_info=e)
                self.line.notification("ETF Error")
                sys.exit()
        elif auto_type == 'prepare':
            self.prepareNextDay = PrepareNextDay()
        elif auto_type == 'goal':
            self.goalKiwoom = GoalKiwoom()
        elif auto_type == 'error':
            try:
                raise Exception('error test')
            except Exception as e:
                self.logging.logger.error('Exception', exc_info=e)
                sys.exit()
        else:
            print("ERROR TYPE %s" % auto_type)
            sys.exit()
        self.app.exec_()

if __name__ == "__main__":
    Main()
