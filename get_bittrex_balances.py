import os
import pandas as pd
from bittrex.bittrex import Bittrex, API_V2_0, API_V1_1

BITTREX_API_KEY = os.getenv('BITTREX_API_KEY')
BITTREX_API_SECRET = os.getenv('BITTREX_API_SECRET')

v1_bittrex = Bittrex('', '', api_version=API_V1_1)
v2_bittrex = Bittrex(
    BITTREX_API_KEY,
    BITTREX_API_SECRET,
    api_version=API_V2_0
)

balances = v2_bittrex.get_balances()

balance_list = []
for b in balances['result']:
    if b['Balance']['Balance'] > 0:
        coin = [
            b['Balance']['Currency'],
            b['Balance']['Available'],
            b['Balance']['Balance']
        ]
        if b['BitcoinMarket']:
            coin.append(b['BitcoinMarket']['Last'] * b['Balance']['Balance'])
        else:
            coin.append(b['Balance']['Balance'])
        balance_list.append(coin)

balance_df = pd.DataFrame(
    balance_list, columns=['currency', 'available', 'balance', 'BTC_value'])

btc_usd = v1_bittrex.get_ticker('USDT-BTC')['result']['Last']
balance_df['USD_value'] = balance_df['BTC_value'] * btc_usd

total_btc = balance_df['BTC_value'].sum()
total_usd = balance_df['USD_value'].sum()

balance_df['weight'] = balance_df['BTC_value'] / total_btc

print(balance_df.sort_values(by='BTC_value', ascending=False))
print()
print('TOTAL PORTFOLIO')
print('BTC:', total_btc)
print('USD:', total_usd)
