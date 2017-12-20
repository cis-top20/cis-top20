import os
import pandas as pd
from coinmarketcap import Market
from bittrex.bittrex import Bittrex, API_V2_0, API_V1_1

from capping import capping


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
        columns=['symbol', 'available', 'balance', 'BTC_value'])

    if btc_usd_price:
        balance_df['USD_value'] = balance_df['BTC_value'] * btc_usd_price
    total_btc = balance_df['BTC_value'].sum()
    balance_df['current_weight'] = balance_df['BTC_value'] / total_btc

    balance_df.set_index('symbol', inplace=True)

    return balance_df.sort_values(by='current_weight', ascending=False)


class BittrexPortfolio(object):
    """docstring for BittrexPortfolio."""

    def __init__(self, n_coins=20, cap=0.1, limit=50):
        self.coinmarketcap = Market()
        self.BITTREX_API_KEY = os.getenv('BITTREX_API_KEY')
        self.BITTREX_API_SECRET = os.getenv('BITTREX_API_SECRET')
        self.v1_bittrex = Bittrex('', '', api_version=API_V1_1)
        self.v2_bittrex = Bittrex(
            self.BITTREX_API_KEY,
            self.BITTREX_API_SECRET,
            api_version=API_V2_0)
        self.blacklist = pd.Series(['USDT', 'BCC'])
        self.n_coins = n_coins
        self.cap = cap
        self.limit = limit

    def get_market_data(self):
        return self.coinmarketcap.ticker(limit=self.limit)

    def get_bittrex_markets(self):
        return self.v1_bittrex.get_markets()['result']

    def get_bittrex_balances(self):
        return self.v2_bittrex.get_balances()

    def get_btc_usd(self):
        return self.v1_bittrex.get_ticker('USDT-BTC')['result']['Last']

    def get_balances(self, bittrex_balances=None, btc_usd=None):
        """Returns a DataFrame with all available balances."""
        if not bittrex_balances:
            bittrex_balances = self.v2_bittrex.get_balances()
        if not btc_usd:
            btc_usd = self.get_btc_usd()

        balance_list = get_balance_list(bittrex_balances)
        balance_df = get_balance_df(balance_list, btc_usd_price=btc_usd)

        return balance_df

    def get_usd_value(self, bittrex_balances=None, btc_usd=None):
        """Returns total portfolio value in USD."""
        if not bittrex_balances:
            bittrex_balances = self.get_bittrex_balances()
        if not btc_usd:
            btc_usd = self.get_btc_usd()

        balance_df = self.get_balances(
            bittrex_balances=bittrex_balances,
            btc_usd=btc_usd)

        return balance_df['USD_value'].sum()

    def get_btc_value(self, bittrex_balances=None):
        """Returns total portfolio value in BTC."""
        if not bittrex_balances:
            bittrex_balances = self.v2_bittrex.get_balances()

        balance_df = self.get_balances(bittrex_balances=bittrex_balances)

        return balance_df['BTC_value'].sum()

    def get_capping(self, market_data=None, bittrex_markets=None):
        """Returns portfolio capping objective."""
        if not market_data:
            market_data = self.get_market_data()
        if not bittrex_markets:
            bittrex_markets = self.get_bittrex_markets()

        bittrex_markets = pd.DataFrame(bittrex_markets)
        bittrex_coins = bittrex_markets.loc[
            bittrex_markets['BaseCurrency'] == 'BTC']['MarketCurrency']
        bittrex_coins = bittrex_coins.append(pd.Series('BTC'))

        df = pd.DataFrame(market_data)
        df = df.loc[
            df['symbol'].isin(bittrex_coins) &
            ~df['symbol'].isin(self.blacklist), :]

        df = df.head(self.n_coins)

        # TODO: create a mapping of the coin symbols somewhere
        df['symbol'] = df['symbol'].apply(lambda x: x if x != 'BCH' else 'BCC')

        # compute market weights
        df['market_cap_usd'] = df['market_cap_usd'].astype(float)
        df['weight'] = df['market_cap_usd']/df['market_cap_usd'].sum()

        # compute capped weights
        capped = capping(df, self.cap, weight_column='weight')
        return capped[['symbol', 'weight']].set_index('symbol')

    def check_rebalancing(
            self, bittrex_balances=None, btc_usd=None,
            market_data=None, bittrex_markets=None):
        if not bittrex_balances:
            bittrex_balances = self.get_bittrex_balances()
        if not btc_usd:
            btc_usd = self.get_btc_usd()
        if not market_data:
            market_data = self.get_market_data()
        if not bittrex_markets:
            bittrex_markets = self.get_bittrex_markets()

        bal = self.get_balances(
            bittrex_balances=bittrex_balances, btc_usd=btc_usd)
        cap = self.get_capping(
            market_data=market_data, bittrex_markets=bittrex_markets)
        portfolio_btc_value = self.get_btc_value(
            bittrex_balances=bittrex_balances)

        df = pd.concat([bal, cap], axis=1)

        df['current_weight'].fillna(0, inplace=True)
        df['weight'].fillna(0, inplace=True)
        df['weight_diff'] = df['weight'] - df['current_weight']
        df['order_type'] = df['weight_diff'].apply(
            lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else None))
        df['order_BTC_quantity'] = abs(df['weight_diff'] * portfolio_btc_value)
        df['order_quantity'] = df['order_BTC_quantity'] / \
            df['BTC_value'] * df['available']

        return df.sort_values(by='BTC_value', ascending=False)[[
            'available', 'BTC_value', 'order_type',
            'order_quantity', 'order_BTC_quantity'
        ]]
