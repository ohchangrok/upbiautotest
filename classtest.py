
from numpy import fabs
import pyupbit
import time
import datetime

#define
#업비트 최소금액
upbit_minprice = 5000
#타겟금액을 구할시에 계산할 이전날짜의 갯수
target_dayValue = 2
#Ma수치를 구할때 계산될 이전날짜의 갯수
target_MaValue = 15

tickerName = ['ETC'] #티커이름
buyper  = [100] #구입비중 안에 있는것을 다 합쳐서 100이다
sellper = [4] #판매비중 삿을떄 비중에해서 해당퍼센트 이하로 떨어지면은 파는 드 만약 저번처럼 훅떨어지는것을 계산해서 들어가는 수치를 잡음(%)
value_k = [10] #가중치(%)
Ma      = [True] #ma

access = ""          # 본인 값으로 변경
secret = ""          # 본인 값으로 변경

class Stock:
    ticker = ""
    ticker_tag = ""
    today_maxprice = 0
    value_k = 0
    isMa = False
    sellpercent = 0
    isInit = False
    buypercent = 0
    sellpercent = 0
    lastprice = 0
    #_ticker : ETC등
    #_buypercent : 100퍼센트등 다른 Stock을 합쳐서 넘지 않도록하자.
    #_value_k 구입시 고려할 배중치
    #MA수치를 적용할지 유무
    def init(self, _ticker, _buypercent, _sellpercent, _value_k, _isMA):
        self.result = 0
        self.ticker = "KRW-" + _ticker
        self.ticker_tag = _ticker
        #그날의 살수 있는 비중
        krw = get_balance("KRW")
        self.buypercent = _buypercent
        self.sellpercent = _sellpercent
        
        self.value_k = _value_k * 0.01 
        self.isMa = _isMA
        self.Reset()
        self.isInit = True

    def Reset(self):
        krw = get_balance("KRW")
        self.today_maxprice = int(krw / (self.buypercent * 0.01))
        
        #5천원이상은 않사질경우가있다 업비트 최소금액
        if self.today_maxprice < upbit_minprice:
            self.today_maxprice = 0
        else:
            self.today_maxprice = self.today_maxprice - upbit_minprice

        self.sellpercent = (self.sellpercent * 0.01)
        #구입후 판매가 이퍼센트 이하로 떨어지면은 판매를 이룰 수치
        self.isInit = True

    def Get_ticker(self):
        return self.ticker

    #현제가격 ex :10,000
    def Nowprice(self):
        if self.ticker == "":
            return 0
        nowprice = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return nowprice

    #현제가진 종목을 판다
    def Sell(self):
        #비트의 갯수
        bit_count = get_balance(self.ticker_tag)
        print("매" + bit_count)
        if bit_count > 0:
            upbit.sell_market_order(self.ticker, bit_count)

    def Buy(self):
        krw = get_balance("KRW")
        if upbit_minprice < krw:
            if self.today_maxprice > 0 and self.ticker != "":
                upbit.buy_market_order(self.ticker, self.today_maxprice) 

    #도달가 해당값이 넘어갈때 산다.
    def Get_target_price(self):
        """변동성 돌파 전략으로 매수 목표가 조회"""
        df = pyupbit.get_ohlcv(self.ticker , interval="day", count=target_dayValue)
        target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * self.value_k
        return target_price

    def GetAvaragePrice(self):

        amount = upbit.get_amount(self.ticker)
        if amount is not None:
            return amount - (amount * self.sellpercent)
        return 0

    #이동평균선
    def Get_MA(self):
        """2일 이동 평균선 조회"""
        df = pyupbit.get_ohlcv(self.ticker, interval="day", count=target_MaValue)
        ma15 = df['close'].rolling(3).mean().iloc[-1]
        return ma15

    #현제가격
    def Get_Nowprice(self):
        current_price = pyupbit.get_orderbook(tickers=self.ticker)[0]["orderbook_units"][0]["ask_price"]
        return current_price
    
    def Update(self):

        if self.isInit == False:
            self.Reset()

        nowprice = self.Get_Nowprice()
        mavalue = self.Get_MA()
        targetprice = self.Get_target_price()
        avagprice = self.GetAvaragePrice()
        try:
            if targetprice < nowprice:
                if self.isMa and mavalue < nowprice:
                    self.Buy()
                else:
                    self.Buy()

            elif avagprice != 0 and self.sellpercent != 0:
                if nowprice < avagprice:
                    self.Sell()
                    
        except Exception as e:
            print(e)
                #print("sell")
                
    def Close(self):
        self.isInit = False


#Func
def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


# Start
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

index = 0
stocklist = list()
for i in tickerName:
    s = Stock()
    s.init(tickerName[index], buyper[index], sellper[index], value_k[index], Ma[index])
    stocklist.insert(0, s)

 
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-ETC")
        end_time = start_time + datetime.timedelta(days=1)
        
        # 9:00 < 현제 < 08:59:50
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            for index, value in enumerate(stocklist):
                value.Update()
            
        else:
            for index, value in enumerate(stocklist):
                value.Sell()
                value.Close()

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)