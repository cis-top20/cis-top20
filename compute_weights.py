import pandas as pd
from cis.lib import capping
from coinmarketcap import Market
from bittrex import Bittrex, API_V2_0, API_V1_1

# get coinmarketcap top 50
coinmarketcap = Market()
data = coinmarketcap.ticker(limit=50)

# get all bittrex markets
my_bittrex = Bittrex(None, None, api_version=API_V1_1)  # or defaulting to v1.1 as Bittrex(None, None)
bittrex_markets = pd.DataFrame(my_bittrex.get_markets()['result'])

# get coins traded in BTC in bittrex
bittrex_coins = bittrex_markets.loc[bittrex_markets['BaseCurrency'] == 'BTC']['MarketCurrency']
bittrex_coins = bittrex_coins.append(pd.Series('BTC'))

# create blacklist
blacklist = pd.Series(['BCC', 'USDT'])

# create dataframe from coinmarketcap data
df = pd.DataFrame(data)

# remove blacklist coins and coins not in bittrex from dataframe
df = df.loc[df['symbol'].isin(bittrex_coins) & ~df['symbol'].isin(blacklist), :]

# get top 20
df = df.head(20)

# compute market weights
df['market_cap_usd'] = df['market_cap_usd'].astype(float)
df['weight'] = df['market_cap_usd']/df['market_cap_usd'].sum()

# compute capped weights
capped = capping(df, 0.1, weight_column='weight')

print(capped.loc[:, ['symbol', 'name', 'weight']])
