import argparse

from PyQt5.QtWidgets import *

from config.lineNotify import LineNotify
from config.log_class import Logging
from kiwoom.buy_kiwoom import *
from kiwoom.day_trading_kiwoom import DayTradingKiwoom
from kiwoom.day_trading_prepare_next_day import DayTradingPrepareNextDay
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
        try:
            self.app = QApplication(sys.argv)
        except Exception as e:
            self.line.notification("ETF Error")
            self.logging.logger.exception('Exception', exc_info=e)
        # sys.exit()

        if auto_type == 'sell':
            self.sellKiwoom = SellKiwoom()
        elif auto_type == 'buy':

            # self.kiwoom = BuyKiwoom()
            # self.kiwoom = NewBuyKiwoom()
            # self.kiwoom = RenewalBuyKiwoom()
            self.kiwoom = DayTradingKiwoom()
        elif auto_type == 'prepare':
            #self.prepareNextDay = PrepareNextDay()
            self.prepareNextDay = DayTradingPrepareNextDay()
        elif auto_type == 'goal':
            try:
                self.goalKiwoom = GoalKiwoom()
            except Exception as e:
                self.logging.logger.exception('Exception', exc_info=e)

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
