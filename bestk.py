import pyupbit
import numpy as np

access = "z09K0F8ExBX2GOEKjinRFZ8ytSucvQK22FB5TyFY"
secret = "96ommUjoqjwFjTXVKgLxHXEXfqGhacOdUjZVBYIp"


def get_ror(k=0.1):
    df = pyupbit.get_ohlcv("KRW-ETC")
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0032
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror


for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k)
    print("%.1f %f" % (k, ror))