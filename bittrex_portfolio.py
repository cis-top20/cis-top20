import os
import pandas as pd
from bittrex.bittrex import Bittrex, API_V2_0, API_V1_1


def get_balance_list(balances):
    balance_list = []
    for b in balances['result']:
        if b['Balance']['Balance'] > 0:
            coin = [
                b['Balance']['Currency'],
                b['Balance']['Available'],
                b['Balance']['Balance']
            ]
            if b['BitcoinMarket']:
                coin.append(
                    b['BitcoinMarket']['Last'] * b['Balance']['Balance'])
            else:
                coin.append(b['Balance']['Balance'])
            balance_list.append(coin)

    return balance_list


def get_balance_df(balance_list, btc_usd_price=None):
    balance_df = pd.DataFrame(
        balance_list,
        columns=['currency', 'available', 'balance', 'BTC_value'])

    if btc_usd_price:
        balance_df['USD_value'] = balance_df['BTC_value'] * btc_usd_price
    total_btc = balance_df['BTC_value'].sum()
    balance_df['weight'] = balance_df['BTC_value'] / total_btc

    return balance_df.sort_values(by='weight')


class BittrexPortfolio(object):
    """docstring for BittrexPortfolio."""

    def __init__(self):
        self.BITTREX_API_KEY = os.getenv('BITTREX_API_KEY')
        self.BITTREX_API_SECRET = os.getenv('BITTREX_API_SECRET')
        self.v1_bittrex = Bittrex('', '', api_version=API_V1_1)
        self.v2_bittrex = Bittrex(
            self.BITTREX_API_KEY,
            self.BITTREX_API_SECRET,
            api_version=API_V2_0)

    def get_balances(self):
        """Returns a DataFrame with all available balances."""
        balances = self.v2_bittrex.get_balances()
        balance_list = get_balance_list(balances)
        btc_usd = self.v1_bittrex.get_ticker('USDT-BTC')['result']['Last']
        balance_df = get_balance_df(balance_list, btc_usd_price=btc_usd)

        return balance_df

    def get_usd_value(self):
        """Returns total portfolio value in USD."""
        balances = self.v2_bittrex.get_balances()
        balance_list = get_balance_list(balances)
        btc_usd = self.v1_bittrex.get_ticker('USDT-BTC')['result']['Last']
        return get_balance_df(balance_list, btc_usd)['USD_value'].sum()

    def get_btc_value(self):
        """Returns total portfolio value in BTC."""
        balances = self.v2_bittrex.get_balances()
        balance_list = get_balance_list(balances)
        return get_balance_df(balance_list)['BTC_value'].sum()
