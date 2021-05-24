import pyupbit
access = "Xoh8dtxxCuxP8xlEB0Uqtw5BiuvPkvHadYVvfRkn"
secret = "aQNEOL0Lq3znbn545Mx4AWSPyxPOJutKgMIFzMSk"


upbit = pyupbit.Upbit(access, secret)

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


krw = get_balance("KRW")
print(krw)