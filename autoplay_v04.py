import talib.abstract as ta
from numpy.core.numeric import isclose
from pandas.core.frame import DataFrame
import pyupbit
import time
import datetime
import pandas as pd
import os.path  
import numpy
from numpy import fabs

#   define
#업비트 최소금액
upbit_minprice = 5000
#타겟금액을 구할시에 계산할 이전날짜의 갯수
class Stock:
    ticker = "" #KRW-ETC
    ticker_tag = "" #ETC
    value_k = 0 #구입시 가중치
    buyprice = 0 #해당 구입리미트 0이면 다사진다 만약 다른코인이 0이라면은 그코인만 다사짐 자신의 잔고를 가지고 판단하자
    sellpercent = 0 #구입가에서 몇퍼떨어졌을시에 팔것인지
    target_day = 0  #구입시 계산에 몇일을 포함할것인지
    matype = ""
    refDF = DataFrame()
    nowTick = 0
    checktick = 0

    
    # 캔들 업데이트 
    def Update_Data(self): 
        self.refDF = pyupbit.get_ohlcv(self.ticker, interval=self.matype, count=21)
        # 캔들 갯수가 있으니 한번씩만 받아서 저장해서 사용하자
        self.nowTick += 1

    # 업데이트
    def Update(self):
        self.Update_Data() #캔들 업데이트
        nowprice = self.Get_Nowprice()     # 현제금
        avagprice = self.Get_sellpercent() # 현제 채결되어있는 금액의 평균매수금액 -갭
        if avagprice > 0: 
            if nowprice < avagprice: 
                self.Sell()
                return

        if self.checktick > self.nowTick:
            return

        targetprice = self.Get_target_price() # 목표가
        ma = self.Get_EMAorMA() # ema or ma
        ss = self.Is_StochasticSlow() #ss
        ha = self.Is_Heiken_Ashi(self.refDF)#하이캔아시
        try:
            if avagprice > 0: #판매
                if self.benchtype == "SS":    
                    if ss < 0:
                        self.Sell()
                elif self.benchtype == "EMA":
                    if ma < 0:
                        self.Sell()
                elif self.benchtype == "None":
                    if nowprice < avagprice :
                        self.Sell()

            if self.benchtype == "None": #구입
                if targetprice < nowprice: #value_k
                    self.Buy()
            elif self.benchtype == "EMA": #ema
                if ma > 0:
                    self.Buy()
            elif self.benchtype == "SS": 
                if ss > 0:
                    self.Buy()

        except Exception as e:
            print(e)
        
        self.nowTick = 0

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
        buy = buycount - amount
        if krw <= 0:
            return
        if buy < 2:
            return
            
        if buy > 0:
            if buy > krw:
                upbit.buy_market_order(self.ticker, krw)
                print("buy")
            else:
                upbit.buy_market_order(self.ticker, buy)
                print("buy")
        else :
            print("Buy error")
    #Heiken_Ashi
    #평균을 내어서 언제 매도를 할것인지 매수를 할것인지를 체크하는 공식
    #단점은 급하락 / 급반등에 대처는 쉽지 않으나 작게 먹을때는 유용하다
    def Is_Heiken_Ashi(self, df):
        #사전작업
        #하이켄-아시는 이전봉의 오픈과 클로즈를 사용하기 때문에 사전작업이 필요하다
        df['he_PrevOpen'] = (df['open'] + df['close']) / 2
        df['he_PrevClose'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        df['he_prevlow'] = df['low']
        df['he_prevhigh'] = df['high']
        
        #Data Operation
        data  = []
        for i in range(len(df)):
            nowdf = df.iloc[i] #현제캔들
            if i == 0:
                #0은 이전것을 넣어올수 없기에 현제것으로 대처
                heclose = nowdf['he_PrevClose']
                heopen = nowdf['he_PrevOpen']
                hehigh = nowdf['he_prevhigh']
                helow=  nowdf['he_prevlow']
                data.append([heclose, heopen, hehigh, helow])
            else:
                prevDf =  df.iloc[i-1] #이전캔들
                heclose = (nowdf['open'] + nowdf['high'] + nowdf['low'] + nowdf['close']) / 4
                heopen = (prevDf['he_PrevOpen'] + prevDf['close'])/2# (이전캔들 시작가 + 이전캔들종가)/2
                hehigh = max(heopen, heclose, nowdf['high']) # 최고가
                helow=  min(heopen, heclose, nowdf['low']) # 최저가
                data.append([heclose, heopen, hehigh, helow])
                
        haDf = pd.DataFrame(data, columns = ['close' , 'open', 'high', 'low'])

        #Check Rogic
        #끝에서부터 갯수로 읽어가면서 이전장을 판단한다
        count = len(haDf)-1
        checkcount = 0
        upcount = 3 #이전겟수중에 업인지 다운인지 체크
        for i in range(len(haDf)):
            if checkcount < 0:
                break
            isup = self.Is_MinusCandle(haDf.iloc[count-i])
            if isup:
                upcount += 1
            checkcount -= 1

        results = 0
        isUpNow = self.Is_MinusCandle(haDf.iloc[count-i])
        if isUpNow:
            if upcount > 1:
                results = 2 #이전에도 상향이 존재함
            else:
                results = 1 #현제만 상향
        elif isUpNow == False: 
            if upcount > 1: 
                results = -2 #이전에도 하향이 존재
            else: 
                results = -1 #현제만 하향
        return results

    #캔들이 상향인지 하향인지 체크
    def Is_MinusCandle(self, _df):
        open = _df['open']
        close = _df['close']
        
        if close > open:
            return True
        else:
            return False
    

    # ema가 현제 크로스인지 체크
    def Get_EMAorMA(self, _isEMA = False):
        
        if self.benchtype == "None":
            return 0
        else:
            
            #ema or ma구하는코드 업비트기준으로 하려면 ma
            #데이터구하는 메인코드
            df_close = self.refDF['close']
            self.refDF['7ma'] = ta.MA(df_close, 7)
            self.refDF['15ma'] = ta.MA(df_close, 15)
            self.refDF['7ema'] = ta.EMA(df_close, 7)
            self.refDF['15ema'] = ta.EMA(df_close, 15)
            #여기까지

            #NaN삭제(Nan은 null)
            stocklist = list()
            for i in range(len(self.refDF)):
                if self.refDF.iloc[i].isnull().any():
                    continue
                else:
                    stocklist.append(self.refDF.iloc[i])
            dfs = pd.DataFrame(stocklist) #list->dataframe
            results = 0
            count = len(dfs)
            prev_7 = 0
            prev_15 = 0
            now_7 = 0
            now_15 = 0
            if _isEMA == True:
                prev_7 = dfs['7ema'].iloc[count-2]
                prev_15 = dfs['15ema'].iloc[count-2]
                now_7 = dfs['7ema'].iloc[-1]
                now_15 = dfs['15ema'].iloc[-1]
            else:
                prev_7 = dfs['7ma'].iloc[count-2]
                prev_15 = dfs['15ma'].iloc[count-2]
                now_7 = dfs['7ma'].iloc[-1]
                now_15 = dfs['15ma'].iloc[-1]

            #교체했는지 체크하는코드
            is_prev_cross = False
            is_now_cross = False
            if prev_7 > prev_15:
                is_prev_cross = True
            if now_7 > now_15:
                is_now_cross = True

            isCross = False
            if is_prev_cross != is_now_cross:
                isCross = True
            if isCross == True:
                if now_7 > now_15:
                    return 1
                elif now_7 < now_15:
                    return -1

            return 0
    
    #StochasticSlow
    #현제의 강도를 채크하는 공식
    #25퍼에서 크로스되어 올라오면은 구입하고 75퍼 이상에서 크로스되어 내려가면은 판매
    def Is_StochasticSlow(self):
        #data Operation
        self.refDF['k'], self.refDF['d'] = ta.STOCH(self.refDF['high'], self.refDF['low'],self.refDF['close'],10 ,3 ,0 ,3 ,0)
        stocklist = list()
        for i in range(len(self.refDF)): #널값은 삭제
            if self.refDF.iloc[i].isnull().any():
                continue
            else:
                stocklist.append(self.refDF.iloc[i])
        ssDf = pd.DataFrame(stocklist)
        
        #Ckeck logic
        ssDfcount = len(ssDf) -1
        ssCrossCount = 0
        min = 25
        max = 75
        ssCheckCount = 3
        isCheckMax = False #75퍼이상인가체크
        for i in range(len(ssDf)):
            k = ssDf['k'].iloc[ssDfcount - i]
            d = ssDf['d'].iloc[ssDfcount - i]
            if k > max and d > max: #75퍼상향일때의 크로스갯수
                if k < d:
                   ssCrossCount += 1
                isCheckMax = True 
            elif k < min and d < min: #25퍼하향일때의 크로스갯수
                if k > d:
                    ssCrossCount += 1

        k = ssDf['k'].iloc[ssDfcount]
        d = ssDf['d'].iloc[ssDfcount]
        results = 0
        if ssCrossCount > 1: #1회라도 크로스된적이 있는가
            if isCheckMax: #75%위
                if k < d: #떨어지기 대기중
                    results = -1
            else:
                if k > d:
                    results = 1
        return results
    
    #초기화
    def init(self, _ticker, _buyprice, _sellpercent, _value_k, _targetday, _matype, _benchtype, _checkTick ):
        self.ticker = "KRW-" + _ticker
        self.ticker_tag = _ticker
        self.buyprice = _buyprice
        self.sellpercent = _sellpercent
        self.value_k = (_value_k * 0.01)
        self.target_day = _targetday
        self.matype = _matype
        self.benchtype = _benchtype
        self.checktick = _checkTick
        
        sellprice = self.Get_sellpercent()
        nowprice = self.Get_Nowprice()
        print(self.ticker)
        if self.benchtype == "None":
            print("기준타입: 기본설정")
            targetprice = self.Get_target_price()
            print(targetprice)
            print("판매가격:")
            print(sellprice)
            print("현제가격:")
            print(nowprice)
            print("========================")
            return
        elif self.benchtype == "SS":
            print("기준타입: 스토케스틱슬로우")
            print("판매가격:")
            print(sellprice)
            print("현제가격:")
            print(nowprice)
            print("========================")
            return
        elif self.benchtype == "EMA":
            print("기준타입: 이동평균선")
            print("판매가격:")
            print(sellprice)
            print("현제가격:")
            print(nowprice)
            print("========================")
            return
        else :
            print("Error:타입을 설정")
            print("========================")

    # 얼마이하로 떨어졌을시에 팔것인지
    def Get_sellpercent(self):
        amount = upbit.get_avg_buy_price(self.ticker) 
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

class Key:
    access = ""
    secret = ""
    def LoadKeyData(self):
        path = "./key.csv"
        if os.path.exists(path):
            data = pd.read_csv(r"key.csv",index_col='access')
            selectdata = data.to_dict()
            for key, value in selectdata.items():
                self.access = key
                self.secret = value['secret']
        else:
            print("Not keyfile")
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
            s.init(key, int(value['buy_price']), float(value['sell_percent']), int(value['value_k']), 
                        int(value['target_day']),value['ma_Type'], value['bench_Mark'],int(value['check_delay']))
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
    

k = Key()
k.LoadKeyData()
print(k.access)
print(k.secret)
upbit = pyupbit.Upbit(k.access , k.secret)

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
    