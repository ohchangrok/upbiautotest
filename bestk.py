import pyupbit
import numpy as np

def Get_MA(counts):
    """2일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv("KRW-ETC", interval="day", count=counts)
    ma15 = df['close'].ewm(counts).mean().iloc[-1]
    # df['ema20'] = df['Close'].ewm(20).mean()
    # df['ema100'] = df['Close'].ewm(100).mean()
    # df['ema200'] = df['Close'].ewm(200).mean()
    ma = df['close'].rolling(counts).mean().iloc[-1]
    print(ma)
    return ma15

def get_ror(k=0.5):
    df = pyupbit.get_ohlcv("KRW-LTC", count=30)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror
    
for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k)
    print("%.1f %f" % (k, ror))
    
#print( Get_MA(14))
    # 이동평균선

