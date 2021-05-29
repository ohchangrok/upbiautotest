from numpy.core.numeric import isclose
from pandas.core.frame import DataFrame
import pyupbit
import time
import datetime
import pandas as pd
import os.path  
from numpy import fabs

#   define
#업비트 최소금액
upbit_minprice = 5000
#타겟금액을 구할시에 계산할 이전날짜의 갯수

access = ""          # 본인 값으로 변경
secret = ""          # 본인 값으로 변경

# Class
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
            s.init(key, int(value['buy_price']), int(value['sell_percent']), int(value['value_k']), int(value['target_day']),value['ma_Type'], value['bench_Mark'])
            stocklist.insert(0, s)

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
        print("update Update_DayTime")
        h = 9
        m = 0
        if _now.hour < h: # and _now.minute < m:
            self.start_time = _now - datetime.timedelta(days= 1, hours = _now.hour, minutes=_now.minute, seconds=_now.second, microseconds=_now.microsecond)
        else: 
            self.start_time = _now - datetime.timedelta(hours = _now.hour, minutes=_now.minute, seconds=_now.second, microseconds=_now.microsecond)
        self.start_time = self.start_time + datetime.timedelta(hours=h, minutes = m)
        self.end_time = self.start_time + datetime.timedelta(days=1)
        self.end_time = self.end_time - datetime.timedelta(seconds=10)
        
    def Update_Hourstime(self, _now):
        print("update Update_Hourstime")
        if _now > self.one_hours_max:
            self.one_hours_min = _now - datetime.timedelta(minutes=_now.minute, seconds=_now.second, microseconds=_now.microsecond) # 01:00
            self.one_hours_max = self.one_hours_min + datetime.timedelta(hours=1) #02:00
        else :
            return None
    

class Stock:
    ticker = "" #KRW-ETC
    ticker_tag = "" #ETC
    value_k = 0 #구입시 가중치
    buyprice = 0 #해당 구입리미트 0이면 다사진다 만약 다른코인이 0이라면은 그코인만 다사짐 자신의 잔고를 가지고 판단하자
    sellpercent = 0 #구입가에서 몇퍼떨어졌을시에 팔것인지
    target_day = 0  #구입시 계산에 몇일을 포함할것인지
    matype = ""
    refDF = DataFrame()

    #초기화
    def init(self, _ticker, _buyprice, _sellpercent, _value_k, _targetday, _matype, _benchtype ):
        self.ticker = "KRW-" + _ticker
        self.ticker_tag = _ticker
        self.buyprice = _buyprice
        self.sellpercent = _sellpercent
        self.value_k = (_value_k * 0.01)
        self.target_day = _targetday
        self.matype = _matype
        self.benchtype = _benchtype
        targetprice = self.Get_target_price()
        sellprice = self.Get_sellpercent()
        print(self.ticker)
        if self.benchtype == "None":
            print("기준타입: 기본설정")
            print(targetprice)
            print("판매가격:")
            print(sellprice)
            print("========================")
            return
        elif self.benchtype == "SS":
            print("기준타입: 스토케스틱슬로우")
            print(targetprice)
            print("판매가격:")
            print(sellprice)
            print("========================")
            return
        elif self.benchtype == "EMA":
            print("기준타입: 이동평균선")
            print(targetprice)
            print("판매가격:")
            print(sellprice)
            print("========================")
            return
        else :
            print("Error:타입을 설정")
            print("========================")
    # 캔들 업데이트
    def Update_Candle(self): 
        self.refDF = pyupbit.get_ohlcv(self.ticker, interval=self.matype, count=21)
        # 캔들 갯수가 있으니 한번씩만 받아서 저장해서 사용하자

    # 업데이트
    def Update(self):
        self.Update_Candle()
        nowprice = self.Get_Nowprice()        # 현제금
        targetprice = self.Get_target_price() # 목표가
        avagprice = self.Get_sellpercent() # 현제 채결되어있는 금액의 평균매수금액 -갭
        ma = self.Is_onlcy_EMA() # ema
        v = self.Is_StochasticSlow() #ss

        try:
            if avagprice > 0: #판매
                if nowprice < avagprice :
                    if self.benchtype == "SS":    
                        if v < 0:
                            self.Sell()
                    elif self.benchtype == "EMA":
                        if ma < 0:
                           self.Sell()
                    elif self.benchtype == "None":
                        self.Sell()

            if self.benchtype == "None": #구입
                if targetprice < nowprice: #value_k
                    self.Buy()
            elif self.benchtype == "EMA": #ema
                if ma > 2:
                    self.Buy()
            elif self.benchtype == "SS": 
                if v > 2:
                    self.Buy()

        except Exception as e:
            print(e)

    # 판매ticker_tag
    def Sell(self):
        bit_count = self.get_balance(self.ticker_tag)#비트의 갯수
        if bit_count > 0:
            upbit.sell_market_order(self.ticker, bit_count)
            print("sell")

    # 구입
    def Buy(self):
        amount =  self.Get_Amount(self.ticker) # 현재 매수한 금액
        krw = self.get_balance("KRW") - upbit_minprice# 현제 잔고 - 업비트 최소잔고
        buycount = self.buyprice
        if krw <= 0:
            return
        if amount > 0: 
            if buycount <= amount: 
                return
            elif (buycount - amount) < upbit_minprice:
                return
            v = buycount - amount
            if (krw - v) > 0:
                upbit.buy_market_order(self.ticker, v)
                print("buy")
        elif buycount > 0:
            if (krw - buycount) > 0:
                upbit.buy_market_order(self.ticker, buycount)
                print("buy")
        elif krw > 0:           
            upbit.buy_market_order(self.ticker, krw)
            print("buy")
        else :
            print("Buy error")

    def IsCross(self,v0, v1, v2, d0, d1, d2):
        isCross = False
        m2 = False
        m1 = False
        m0 = False
        if v2 > d2:
            m2 = True
        if v1 > d1:
            m1 = True
        if v0 > d0:
            m0 = True
        
        if m0 == False:
            if m1 == False:
                if m2 == True:
                    isCross = True
            else :
                isCross = True
        #매수
        if m0:
            if m1:
                if m2 == False:
                    isCross = True
            else :
                isCross = True

        return isCross
        
    def Is_StochasticSlow(self):

        if self.benchtype == "None":
            return 0
        if self.benchtype =="EMA":
            return 0

        max = 65
        min = 35
        k    = self.CalculateStochasticSlow(10, 3, 3, self.refDF, 'slowK', -1) *100
        k_m1 = self.CalculateStochasticSlow(10, 3, 3, self.refDF, 'slowK', -2) *100
        k_m2 = self.CalculateStochasticSlow(10, 3, 3, self.refDF, 'slowK', -3) *100
        d    = self.CalculateStochasticSlow(10, 3, 3, self.refDF, 'slowD', -1) *100
        d_m1 = self.CalculateStochasticSlow(10, 3, 3, self.refDF, 'slowD', -1) *100
        d_m2 = self.CalculateStochasticSlow(10, 3, 3, self.refDF, 'slowD', -2) *100

        #매도
        results = 0
        iscross = self.IsCross(k, k_m1, k_m2, d, d_m1, d_m2)
        if k > max:
            if k > d:
                if iscross:
                    results = 2
                else: 
                    results = 2
            else: 
                results = -1
        #매수
        elif k < min:
            if k > d:
                if iscross:
                    results = 2
                else:
                    results = 1
            else: 
                results = -1

        return results

    def CalculateStochasticSlow(self, nF, nM1, nM2, data, index, counts):
        lastindex = len(data)
        dfdata = data.iloc[:lastindex-counts]
        maxV = dfdata.high.rolling(nF).max()        
        minV = dfdata.low.rolling(nF).min()
        maxV.fillna(0)
        minV.fillna(0)
        reDf = pd.DataFrame()
        reDf['fastK'] = (dfdata.close - minV) / (maxV - minV)
        reDf['slowK'] = reDf['fastK'].rolling(nM1).mean()
        reDf['slowD'] = reDf['slowK'].rolling(nM2).mean()
        return reDf[index].iloc[-1]


    # def get_avg_buy_price(self, ticker='KRW', contain_req=False):
    #     avg = self.get_amount(ticker)
    #     if avg is None:
    #         return 0
    #     else:
    #         min = avg * (self.sellpercent * 0.01)
    #         return avg - min

    # 얼마이하로 떨어졌을시에 팔것인지
    def Get_sellpercent(self):
        amount = upbit.get_avg_buy_price(self.ticker)
        if amount is None:
            return 0
        if self.sellpercent <= 0:
            return 0

        per = (self.sellpercent * 0.01)
        return amount - (amount * per)
    
    def Get_MaBuyPerCent(self):
        targetprice = self.Get_target_price()
        per = (self.sellpercent * 0.01)
        return targetprice - (targetprice * per)
    

    # 티커
    def Get_ticker(self):
        return self.ticker

    # 잔고조회
    def get_balance(self, ticker):
        balances = upbit.get_balances()
        for b in balances:
            if b['currency'] == ticker:
                if b['balance'] is not None:
                    return float(b['balance'])
                else:
                    return 0
        return 0

    
    #현제가격 ex :10,000
    def Nowprice(self):
        if self.ticker == "":
            return 0
        nowprice = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return nowprice

    # 가중치 구분
    def Get_target_price(self):
        df = pyupbit.get_ohlcv(self.ticker , interval="day", count=self.target_day)
        h = df.iloc[0]['high']
        l = df.iloc[0]['low']
        c = df.iloc[0]['close']
        v = (h - l) * self.value_k
        target_price = df.iloc[0]['close'] + v
        return target_price

     # 현제가격
    def Get_Nowprice(self):
        current_price = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return current_price

    # ema가 현제 크로스인지 체크
    def Is_onlcy_EMA(self):

        if self.benchtype == "SS":
            return 0
        elif self.benchtype == "None":
            return 0
        else:
            df20 = self.refDF
            lastindex = len(df20)
            ema7_2minus = df20.iloc[lastindex-9:lastindex-2]['close'].ewm(7).mean().iloc[-1]
            ema7_1minus = df20.iloc[lastindex-8:lastindex-1]['close'].ewm(7).mean().iloc[-1]
            ema7 = df20.iloc[lastindex-7:lastindex]['close'].ewm(7).mean().iloc[-1]
            ema15_2minus = df20.iloc[lastindex-17:lastindex-2]['close'].ewm(15).mean().iloc[-1]
            ema15_1minus = df20.iloc[lastindex-16:lastindex-1]['close'].ewm(15).mean().iloc[-1]
            ema15 = df20.iloc[lastindex-15:lastindex]['close'].ewm(15).mean().iloc[-1]    

            iscross = self.IsCross(ema7, ema7_1minus,ema7_2minus, ema15, ema15_1minus,ema15_2minus)

            if ema7 > ema15:
                if iscross:
                   return 2
                else:
                    return 1

            elif ema7 < ema15:
                return -1

            return 0

    # ema 7수치
    def Get_onlcy_EMA(self):
        df20 = self.refDF
        lastindex = len(df20)
        ema7 = df20.iloc[lastindex-7:lastindex]['close'].ewm(7).mean().iloc[-1]
        return ema7
    
    # 매수평균가
    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = self.get_balances(contain_req=True)

            avg_buy_price = 0
            for x in balances:
                if x['currency'] == ticker:
                    avg_buy_price = float(x['avg_buy_price'])
                    break
            if contain_req:
                return avg_buy_price, req
            else:
                return avg_buy_price

        except Exception as x:
            
            return None
    # 특정 코인/원화의 매수금액 조회
    def Get_Amount(self, ticker, contain_req=False):
        try:
            # KRW-BTC
            if '-' in ticker:
                ticker = ticker.split('-')[1]

            balances, req = upbit.get_balances(contain_req=True)

            amount = 0
            for x in balances:
                if x['currency'] == 'KRW':
                    continue

                avg_buy_price = float(x['avg_buy_price'])
                balance = float(x['balance'])
                locked = float(x['locked'])

                if ticker == 'ALL':
                    amount += avg_buy_price * (balance + locked)
                elif x['currency'] == ticker:
                    amount = avg_buy_price * (balance + locked)
                    break
            if contain_req:
                return amount, req
            else:
                return amount
        except Exception as x:
            return 0


        
# Start
upbit = pyupbit.Upbit(access, secret)

stocklist = list()
tablemanager = TableManager()
tablemanager.Init()
timemanager = TimeMananger()
timemanager.Init()

print("autotrade start")

while True:
    try:
        nowtime = datetime.datetime.now()
        # 전일 09:00 < 현제 < 다음날 08:59:50
        if timemanager.start_time < nowtime < timemanager.end_time:
            if nowtime > timemanager.one_hours_max:   # 매시간 체크사항
                timemanager.Update_Hourstime(nowtime) # 시간체크
                tablemanager.LoadTable()              # 테이블로드
            for index, value in enumerate(stocklist): # 매인로직 업데이트
                value.Update()
        else:
            if timemanager.end_time < nowtime :
                timemanager.Update_DayTime(nowtime) #날짜 초기화
            for index, value in enumerate(stocklist):
                value.Sell() #날짜가 바뀌면은 판매
        time.sleep(1)

    except Exception as e:
        print(e)
        time.sleep(1)  
    