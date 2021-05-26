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
            s.init(key, int(value['buy_percent']), int(value['sell_percent']), int(value['value_k']), value['is_ma'],int(value['target_day']),int(value['ma_day']))
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
        self.start_time = _now - datetime.timedelta(hours = _now.hour, minutes=_now.minute, seconds=_now.second, microseconds=_now.microsecond)
        self.start_time = self.start_time + datetime.timedelta(hours=9)
        self.end_time = self.start_time + datetime.timedelta(days=1)
        self.end_time = self.end_time - datetime.timedelta(seconds=10)
        
    def Update_Hourstime(self, _now):
        print("update Update_Hourstime")
        print(_now)
        if _now > self.one_hours_max:
            self.one_hours_min = _now - datetime.timedelta(minutes=_now.minute, seconds=_now.second, microseconds=_now.microsecond) # 01:00
            self.one_hours_max = self.one_hours_min + datetime.timedelta(hours=1) #02:00
        else :
            return None

class Stock:
    ticker = "" #_ticker : ETC등
    ticker_tag = "" #KRW-ETC
    value_k = 0 #구입시 가중치
    isMa = False #ma를 할것인지 여부
    buypercent = 0 #_buypercent : 100퍼센트등 다른 Stock을 합쳐서 넘지 않도록하자.
    sellpercent = 0 #구입가에서 몇퍼떨어졌을시에 팔것인지
    target_day = 0  #구입시 계산에 몇일을 포함할것인지
    ma_day = 0 #ma시에 몇일치를 통계낼것인지
    
    
    #초기화
    def init(self, _ticker, _buypercent, _sellpercent, _value_k, _isMA, _targetday,_ma_day ):
        self.ticker = "KRW-" + _ticker
        self.ticker_tag = _ticker
        self.buypercent = _buypercent
        self.sellpercent = _sellpercent
        self.value_k = _value_k * 0.01 
        self.isMa = _isMA
        self.target_day = _targetday
        self.ma_day = _ma_day

    def get_avg_buy_price(self, ticker='KRW', contain_req=False):
        avg = self.get_amount(ticker)
        if avg is None:
            return 0
        else:
            min = avg * (self.sellpercent * 0.01)
            return avg - min

    # 살경우에 내현제 잔고에서 몇퍼센트로 소모할것인지
    def Get_buypercent(self):
        if self.buypercent != 0:
            krw = self.get_balance("KRW")
            per = (self.buypercent * 0.01)
            return krw * per
        else:
            return self.get_balance("KRW")

    # 얼마이하로 떨어졌을시에 팔것인지
    def Get_sellpercent(self):
        if self.buypercent != 0:
            amount = upbit.get_amount(self.ticker)
            per = (self.buypercent * 0.01)
            return amount * per
        else:
            return 0

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

    def get_amount(self, ticker, contain_req=False):
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
            print(x.__class__.__name__)
            return None

    #현제가격 ex :10,000
    def Nowprice(self):
        if self.ticker == "":
            return 0
        nowprice = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return nowprice

    # 판매
    def Sell(self):
        bit_count = self.get_balance(self.ticker_tag)#비트의 갯수
        if bit_count > 0:
            upbit.sell_market_order(self.ticker, bit_count)

    # 구입
    def Buy(self):
        krw = self.get_balance("KRW")
        if upbit_minprice < krw:
                upbit.buy_market_order(self.ticker, self.Get_buypercent() - upbit_minprice)

    # 가중치 구분
    def Get_target_price(self):
        df = pyupbit.get_ohlcv(self.ticker , interval="day", count=self.target_day)
        target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * self.value_k
        return target_price

    # 이동평균선
    def Get_EMA(self):
        """2일 이동 평균선 조회"""
        df = pyupbit.get_ohlcv(self.ticker, interval="day", count=self.ma_day)
        ema = df['close'].ewm(self.ma_day).mean().iloc[-1] #ema
        #ma15 = df['close'].rolling(self.ma_day).mean().iloc[-1] #ma
        return ema

    # 현제가격
    def Get_Nowprice(self):
        current_price = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return current_price

    # 업데이트
    def Update(self):
        nowprice = self.Get_Nowprice()        # 현제금
        mavalue = self.Get_EMA()              # ema 수치
        targetprice = self.Get_target_price() # 목표가
        avagprice = self.get_avg_buy_price(self.ticker) # 장중에 매도할 금액
        try:
            if targetprice < nowprice:
                if self.isMa:
                    if mavalue < nowprice:
                        self.Buy()
                else:
                    self.Buy()

            elif avagprice != 0:
                if nowprice < avagprice:
                    self.Sell()
                    
        except Exception as e:
            print(e)


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
    