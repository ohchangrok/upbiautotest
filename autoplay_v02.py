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

access = "GKzRKyi1gfcC2mtXyHxY345JxgHHQR27yZ5xBMq3"          # 본인 값으로 변경
secret = "GuRqKjGBshZObqPvrX0G27hG9pXUV2vh3UBgNztk"          # 본인 값으로 변경

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
            s.init(key, int(value['buy_price']), int(value['sell_percent']), int(value['value_k']), int(value['target_day']),value['ma_Type'])
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
        print("update Update_DayTime")
        h = 9
        m = 0
        if _now.hour <= h: # and _now.minute < m:
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
    

    #초기화
    def init(self, _ticker, _buyprice, _sellpercent, _value_k, _targetday, _matype ):
        self.ticker = "KRW-" + _ticker
        self.ticker_tag = _ticker
        self.buyprice = _buyprice
        self.sellpercent = _sellpercent
        self.value_k = _value_k * 0.01 
        self.target_day = _targetday
        self.matype = _matype

    # 업데이트
    def Update(self):
        nowprice = self.Get_Nowprice()        # 현제금
        targetprice = self.Get_target_price() # 목표가
        ma_va = self.Is_onlcy_EMA() 
        avagprice = self.Get_sellpercent(self.ticker) # 현제 채결되어있는 금액의 평균매수금액
        try:
            #구입
            if self.matype == "None":
                if targetprice < nowprice: #일반적인 k
                    self.Buy()
            elif self.matype == "EMA_K": #k값 + ema 7수치
                ema_val = self.Get_onlcy_EMA()
                if ema_val < nowprice and targetprice < nowprice:
                    self.Buy()
            else: #생 EMA 7 > 15일시에
                if ma_va > 0:
                    self.Buy()

            #판매
            if avagprice > 0: #일반적인ㅏ or k값 + ema 7수치
                if ma_va < 0:
                    self.Sell()
                elif nowprice < avagprice:
                    self.Sell()

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

    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        avg = self.get_amount(ticker)
        if avg is None:
            return 0
        else:
            min = avg * (self.sellpercent * 0.01)
            return avg - min

    # 얼마이하로 떨어졌을시에 팔것인지
    def Get_sellpercent(self, ticker):
        amount = upbit.get_avg_buy_price(ticker)
        if amount is None:
            return 0
        if self.sellpercent <= 0:
            return 0

        per = (self.sellpercent * 0.01)
        return amount - (amount * per)
        

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
        target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * self.value_k
        return target_price

     # 현제가격
    def Get_Nowprice(self):
        current_price = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return current_price

    # ema가 현제 크로스인지 체크
    def Is_onlcy_EMA(self):

        if self.matype == "EMA_K":
            return 0
        if self.matype == "None":
            return 0

        df20 = pyupbit.get_ohlcv(self.ticker, interval=self.matype, count= 20)
        lastindex = len(df20)
        ema7_1minus = df20.iloc[lastindex-8:lastindex-1]['close'].mean()
        ema7 = df20.iloc[lastindex-7:lastindex]['close'].mean()
        ema15_1minus = df20.iloc[lastindex-15:lastindex]['close'].mean()
        ema15 = df20.iloc[lastindex-15:lastindex]['close'].mean()       

        if ema7 > ema15 and ema7_1minus > ema15_1minus: #2틱상승
            return 2
        elif ema7 > ema15 and ema7_1minus < ema15_1minus: #1틱상승
            return 1
        elif ema7 < ema15 and ema7_1minus > ema15_1minus: #1틱하락
            return -1
        else: #2틱하락
            return -2

    # ema 7수치
    def Get_onlcy_EMA(self):
        #ema = df['close'].ewm(self.ma_day).mean().iloc[-1] #ema
        #ma15 = df['close'].rolling(self.ma_day).mean().iloc[-1] #ma
        df20 = pyupbit.get_ohlcv(self.ticker, interval=self.matype, count= 20)
        lastindex = len(df20)
        ema7 = df20.iloc[lastindex-7:lastindex]['close'].ewm(7).mean().iloc[-1]
        return ema7
    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        """
        특정 코인/원화의 매수평균가 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드
        :param contain_req: Remaining-Req 포함여부
        :return: 매수평균가
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
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

    def Get_Amount(self, ticker, contain_req=False):
        """
        특정 코인/원화의 매수금액 조회
        :param ticker: 화폐를 의미하는 영문 대문자 코드 (ALL 입력시 총 매수금액 조회)
        :param contain_req: Remaining-Req 포함여부
        :return: 매수금액
        [contain_req == True 일 경우 Remaining-Req가 포함]
        """
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
            #print(x.__class__.__name__)
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
    