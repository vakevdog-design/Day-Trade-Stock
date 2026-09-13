import requests 
from dotenv import dotenv_values

config = dotenv_values(".env")
# accesses the value inside of .env
finnhub_key = config["FINNHUB_KEY"]
# accesses the actual api key
alpaca_api_key = config['ALPACA_API_KEY']
# accesses the actual api key
alpaca_secret = config['ALPACA_SECRET_KEY']
# access the actual api key

master_list = requests.get(
    "https://finnhub.io/api/v1/stock/symbol",
    params = {
    'exchange': "US",
    'token': finnhub_key
    }
)
# uses the finnhub api to make a master list of all us stocks
stocks = master_list.json()
# this takes the collected information and stores it in stocks to be ready for usage
filtered_stocks = []
# this is an empty list
for stock in stocks:
    if stock['mic'] in ['XNAS', 'XNYS', 'BATS'] and stock['type'] == 'Common Stock':
            filtered_stocks.append(stock['symbol'])
# Filter the master list to U.S. common stocks traded on NASDAQ, NYSE, or BATS.
# This removes securities such as ETFs amd stocks traded on other exchanges
candidates = []
# this creates an empty list
all_data = {}
# this creates an empty dictionary
for i in range(0, len(filtered_stocks), 100):
    batch = filtered_stocks[i:i + 100]
# Process the stocks in abtches of 100 to reduce the number of API trequests
# and avoid requesting thousands of stocks individually
    response = requests.get(
        "https://data.alpaca.markets/v2/stocks/snapshots",
        params = {
            'symbols': ','.join(batch),
            "feed": "iex"
        },
        headers = {
            "APCA-API-KEY-ID": alpaca_api_key,
            'APCA-API-SECRET-KEY': alpaca_secret
        }
    )
# response extracts the information from the stocks that were iterated over
    data = response.json()
    all_data.update(data)
    # data stores the information from response
    #Save this batch's data into all_data so information from previous batches
    # is preserved instead of being overwritten by the next API response
    for stock in batch:
        #iterates over the batch of 100 stocks
        if stock not in data:
            continue
        # Skip stocks for which Alpaca did not retrun snapshot data
        today = data[stock].get('dailyBar')
        # Retrieve today's daily bar, which contains the stock's open, high, and low
        #close, volume, and other daily trading information
        yesterday = data[stock].get('prevDailyBar')
        # Retrieve the previous trading day's daily bar for comparison
        #.get() says retrieve the data if it is there
        if today is None or yesterday is None:
            continue
            # this asks if today or yesterday is not in the information, then skip those stocks
        if (today['o'] > 5 and today['v'] >= 500_000 and today['o'] < yesterday['c']):
            candidates.append(stock)
            # Keep stocks that:
            # 1. Opened above $5
            # 2. Have at least 500,000 shares of IEX volume
            # 3. Opened below the previous day's close (gap-down)
market_cap_candidates = {}
# creates an empty dictionary
for stock in candidates:
# iterates over the candidates list and individualizes each item as stock
    response = requests.get(
         "https://finnhub.io/api/v1/stock/profile2",
         params = {
              'symbol': stock,
              'token': finnhub_key
         }
    )
    profile = response.json()
    market_cap = profile.get('marketCapitalization')
# response retrieves the stock data for the stocks that passed all the previous filters
#profile stores that data
#market_cap retrieves the market cap data and stores it in the variable marker_cap
    if market_cap is not None and market_cap > 500:
        market_cap_candidates[stock] = market_cap
# Finnhub reports market capitalization in millions of dollars,
# so a value above 500 represents a market cap greater than $500 million
# Store the ticker and market cap for stocks that pass this filter
print('======================')
print("Day Trading Candidates")
print('======================')
print("TICKER | Prev Close | Open | Gap | Current | Intraday | IEX Volume | Market Cap | Today's High | Today's Low")
#this is the heading for the final dispalyed terminal window
for stock in market_cap_candidates:
    #this iterates over all the stocks in market_cap_candidates
    today = all_data[stock]['dailyBar']
    #all data is accessed and accesses the daily bar of stock info for today
    yesterday = all_data[stock]['prevDailyBar']
    #all data which contains all the information of the stocks accesses the previous day's daily bar of stock info
    market_cap = market_cap_candidates[stock]
# Stores the stocks'market cap info in the variable market_cap
    gap_percent = ( 
    (today['o'] - yesterday['c']) / yesterday['c'])* 100
# Calculate the percentage difference between today's opening price
# and yesterday's closing price.
    intraday_percent = (
        (today['c'] - today['o']) / today['o']
    ) * 100
# Calculate the percentage change from today's opening price
# to the current daily close.
    print(f"{stock} | ${yesterday['c']} | ${today['o']} | {gap_percent:.2f}% | {today['c']} | {intraday_percent:.2f}% | {today['v']} | ${market_cap:.2f}M | {today['h']} | {today['l']}")

