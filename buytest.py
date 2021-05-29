import pyupbit
access = ""
secret = ""
upbit = pyupbit.Upbit(access, secret)
upbit.buy_market_order("KRW-ETC", 5000) 
#print(krw['NoneType'])
# def get_ror(k=0.5):
#     df = pyupbit.get_ohlcv("KRW-ETC")
#     df['range'] = (df['high'] - df['low']) * k
#     df['target'] = df['open'] + df['range'].shift(1)

#     df['ror'] = np.where(df['high'] > df['target'],
#                          df['close'] / df['target'],
#                          1)

#     ror = df['ror'].cumprod()[-2]
#     return ror


# for k in np.arange(0.1, 1.0, 0.1):
#     ror = get_ror(k)
#     print("%.1f %f" % (k, ror))
# def Get_Ohlcy_Ema7():
#     df30 = pyupbit.get_ohlcv("KRW-ETC", interval="minute1", count= 30)
    # lastindex = df30.count()-1
    # df7 = df30.iloc[lastindex-7:lastindex]
    # df15 = df30.iloc[lastindex-15:lastindex]
    # ema7 = df7['close'].ewm(7).mean()
    # ema15 = df15['close'].ewm(15).mean()
    # print(ema7)
    # print(ema15)
    

# def Get_Ohlcy_Ema15():
#     df15 = pyupbit.get_ohlcv("KRW-ETC", interval="minute1", count= 15)
#     ema15 = df15['close'].ewm(15).mean()#.iloc[-1]
#     return ema15

def Get_onlcy_ema(ticker, inter):
    df20 = pyupbit.get_ohlcv(ticker, interval=inter, count= 20)
    lastindex = len(df20)
    ema7_1minus = df20.iloc[lastindex-8:lastindex-1]['close'].mean()
    ema7 = df20.iloc[lastindex-7:lastindex]['close'].mean()
    ema15_1minus = df20.iloc[lastindex-15:lastindex]['close'].mean()
    ema15 = df20.iloc[lastindex-15:lastindex]['close'].mean()       

    if ema7 > ema15 and ema7_1minus > ema15_1minus: #2틱상승
        return 2
        print("")
    elif ema7 > ema15 and ema7_1minus < ema15_1minus: #1틱상승
        return 1
    elif ema7 < ema15 and ema7_1minus > ema15_1minus: #1틱하락
        return -1
    else: #2틱하락
        return -2
        

v = Get_onlcy_ema("KRW-ETC",'minute1')
print(v)