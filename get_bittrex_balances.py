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

balances_df = pd.DataFrame(
    [
        [
            b['Balance']['Currency'],
            b['Balance']['Available'],
            b['Balance']['Balance'],
            b['BitcoinMarket']['Last'] * b['Balance']['Balance'],
        ] for b in balances['result']
        if b['Balance']['Balance'] > 0 and b['BitcoinMarket']
    ],
    columns=['currency', 'available', 'balance', 'BTC_value']
)

btc_usd = v1_bittrex.get_ticker('USDT-BTC')['result']['Last']
balances_df['USD_value'] = balances_df['BTC_value'] * btc_usd

print(balances_df.sort_values(by='BTC_value', ascending=False))
print()
print('TOTAL PORTFOLIO')
print('BTC:', balances_df['BTC_value'].sum())
print('USD:', balances_df['USD_value'].sum())
