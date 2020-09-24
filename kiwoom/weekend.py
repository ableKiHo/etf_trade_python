import datetime


class Weekend():
    def __init__(self):
        self.isWeekend = False
        self.isFriday = False
        self.isMonday = False
        t = ['월', '화', '수', '목', '금', '토', '일']
        weekDay = datetime.datetime.today().weekday()
        if t[weekDay] == '토' or t[weekDay] == '일':
            self.isWeekend = True

        if t[weekDay] == '금':
            self.isFriday = True

        if t[weekDay] == '월':
            self.isMonday = True

