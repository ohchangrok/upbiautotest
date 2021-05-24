import time
import pyupbit
import datetime

access = "z09K0F8ExBX2GOEKjinRFZ8ytSucvQK22FB5TyFY"
secret = "96ommUjoqjwFjTXVKgLxHXEXfqGhacOdUjZVBYIp"

# 가중치
value = 0.1
# 비트티커
ticker_tag = "KRW-ETC"
# 해당값을 곱했을시에 5000원이 넘는 숫자
won = 0.09
#최소금액
min_won = 5000

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """7일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    ma15 = df['close'].rolling(2).mean().iloc[-1]
    return ma15

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

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]
def get_currnt_pricecount(ticker):
    """현제 보유갯수"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_size"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

toDay_Price = 0
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(ticker_tag)
        end_time = start_time + datetime.timedelta(days=1)
        
        # 9:00 < 현제 < 08:59:50
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(ticker_tag, value)
            ma15 = get_ma15(ticker_tag)
            current_price = get_current_price(ticker_tag)
            #etc_count = get_balance("ETC")
            # EM선
            #if target_price < current_price and ma15 < current_price:
            if target_price < current_price:
                krw = get_balance("KRW")
                #구입
                if krw > min_won:
                    upbit.buy_market_order(ticker_tag, krw - min_won) 
                    #toDay_Price = krw - min_won
            #elif current_price < etc_count * won:
            #    upbit.sell_market_order(ticker_tag, etc_count)
            #    toDay_Price = 0
        else:
            etc_count = get_balance("ETC")
            if etc_count > 0:
                upbit.sell_market_order(ticker_tag, etc_count)
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)