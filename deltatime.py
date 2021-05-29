import time
import datetime
import pandas as pd
import os.path  

class Stock:
    ticker = ""
    ticker_tag = ""
    today_maxprice = 0
    value_k = 0
    isMa = False
    buypercent = 0
    sellpercent = 0

class TableManager:
    path = "./table.csv"
    def Init(self):
        if os.path.exists(self.path):
            self.LoadTable()
        else:
            return None
    
    def LoadTable(self):
        print("LoadTable")
        data = pd.read_csv(r"table.csv",index_col='ticker')
        selectdata = data.to_dict()
        
        stocklist.clear()
        for key, value in selectdata.items():
            s = Stock()
            s.ticker = key
            s.ticker_tag = "KRW-" + s.ticker
            s.buypercent = int(value['buy_percent'])
            s.sellpercent = int(value['sell_percent'])
            s.value_k = bool(value['is_ma'])
            stocklist.insert(0, s)
        print(len(stocklist))

class TimeMananger:
    now = datetime.datetime.now()
    one_hours_min = datetime.datetime.now()
    one_hours_max = datetime.datetime.now()
    start_time = datetime.datetime.now()
    end_time = datetime.datetime.now()
    def Init(self):
        now = datetime.datetime.now()
        self.Update_DayTime(now)
        self.Update_Hourstime(now)

    def Update_DayTime(self, _now):
        self.start_time = _now - datetime.timedelta(hours = _now.hour, minutes=_now.minute, seconds=_now.second, microseconds=_now.microsecond)
        self.start_time = self.start_time + datetime.timedelta(hours=9)
        self.end_time = self.start_time + datetime.timedelta(days=1)
        self.end_time = self.end_time - datetime.timedelta(seconds=10)
        print(self.start_time)
        print(self.end_time)
        
    def Update_Hourstime(self, _now):
        print("update Update_Hourstime")
        print(_now)
        if _now > self.one_hours_max:
            self.one_hours_min = _now - datetime.timedelta(seconds=_now.second, microseconds=_now.microsecond)
            self.one_hours_max = self.one_hours_min + datetime.timedelta(minutes=1)
            print(self.one_hours_min)
            print(self.one_hours_max)
        else :
            return None

stocklist = list()
tablemanager = TableManager()
tablemanager.Init()

timemanager = TimeMananger()
timemanager.Init()

while True:
    nowtime = datetime.datetime.now()
    if timemanager.start_time < nowtime < timemanager.end_time:
        if nowtime > timemanager.one_hours_max:
            timemanager.Update_Hourstime(nowtime)
            tablemanager.LoadTable()
        
    else:
          if timemanager.end_time < nowtime :
              timemanager.Update_DayTime(nowtime)

    time.sleep(1)





 