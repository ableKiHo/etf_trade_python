import argparse

from kiwoom.kiwoom import *
import sys
from PyQt5.QtWidgets import *

sys.path.append("D:/PycharmProjects/etf/")

class Main():
    def __init__(self):
        print("Main() start")

        self.app = QApplication(sys.argv)
        self.kiwoom = Kiwoom()
        self.app.exec_()

if __name__ == "__main__":
    Main()
