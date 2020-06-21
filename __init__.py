import argparse

from PyQt5.QtWidgets import *

from kiwoom.buy_kiwoom import *
from kiwoom.prepare_next_day import PrepareNextDay
from kiwoom.sell_kiwoom import SellKiwoom

sys.path.append("D:/PycharmProjects/etf/")

class Main():
    def __init__(self):
        print("Main() start")
        parser = argparse.ArgumentParser()
        parser.add_argument('--type', required=True)
        args = parser.parse_args()
        auto_type = args.type

        print("AUTO ETF TYPE %s" % auto_type)

        self.app = QApplication(sys.argv)
        if auto_type == 'sell':
            self.sellKiwoom = SellKiwoom()
        elif auto_type == 'buy':
            self.kiwoom = BuyKiwoom()
        elif auto_type == 'prepare':
            self.prepareNextDay = PrepareNextDay()
        else:
            print("ERROR TYPE %s" % auto_type)
            sys.exit()
        self.app.exec_()

if __name__ == "__main__":
    Main()
