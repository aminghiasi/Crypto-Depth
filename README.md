Crypto-Depth is a real-time pipeline that aggregates markets depth for 5000+ crypto markets.

# Overview
Traders constantly put asks and bids on a crypto coin. The Market Depth plot shows the collective asks and bids on a coin and can be used as a measure of market sentiment. For instance, if there is a market depth imbalance, e.g. many more bids than asks, that shows that traders are interest in that coin.

<img width="960" alt="screen shot 2019-02-23 at 7 37 38 pm" src="https://user-images.githubusercontent.com/12805440/53293484-7e9da100-37a2-11e9-9138-de77d4ba1732.png">


Crypto-Depth is a server-less platform that provides traders market depth data using AWS Lambda, Kinesis, DynamoDB, and API Gateway. It features:
* A dashboard to analyze market depth for crypto
* Monitoring of 5000+ crypto markets
* A real-time and historical api for trading bots

This repository has what you need to stand up your own version of Crypro-Depth in your own AWS projects.

[Slide Deck](https://docs.google.com/presentation/d/14pjAVgnJGYHm2wY2WbIjx3lpbVU8mi2FC4btlx4BGwU/edit#slide=id.g4f463f984c_2_0)

<img width="1132" alt="screen shot 2019-02-23 at 7 09 08 pm" src="https://user-images.githubusercontent.com/12805440/53293442-b3f5bf00-37a1-11e9-8c38-798be6115b1a.png">


# Requirments
* AWS Account and Python 3.7
* [CoinMarketCap](https://coinmarketcap.com/api/) API Key
* [Currencylayer](https://currencylayer.com) API Key

# Installation
```bash
git clone https://github.com/aminghiasi/Crypto-Depth.git
```
Add Redis Endpoint, DynamoDB table name, ARN for Steward and Worker lambda functions, Kinesis stream name, and region name to config.py
Then put your access keys for coinmarketcap and currencylayer APIs in credentials.py and do:
```bash
. ./deployment/deploy.sh
. ./deployment/run.sh
```

# Getting Started
Open the website at http://coinmarketdepth.live/. In addition to the crypto market depth plot, you can see two more plots that auto update every minute: Buy/Sell pressure and Market Depth Ratio plots:
<img width="886" alt="screen shot 2019-02-23 at 7 38 44 pm" src="https://user-images.githubusercontent.com/12805440/53293495-c9b7b400-37a2-11e9-8e42-420ed7f7d324.png">



The buy/sell pressure is the amount of all asks/bids in the market. If you apply a percentage threshold of 5%, the website will only sum all orders within 5% of the price of each coin. 

<img width="952" alt="screen shot 2019-02-23 at 7 40 48 pm" src="https://user-images.githubusercontent.com/12805440/53293505-f2d84480-37a2-11e9-8031-e485f96bdd9b.png">


This plot shows the ratio of buy pressure to sell pressure over time. Market Depth Ratio is defined as:

MDR = (buy pressure - sell pressure) / (buy pressure + sell pressure)


# Documention
You can access the API at https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1 and can pass these parameters:

<img width="868" alt="screen shot 2019-02-23 at 7 34 44 pm" src="https://user-images.githubusercontent.com/12805440/53293466-1a7add00-37a2-11e9-9992-7f7c9f086fed.png">


# Credits
Crypto-Depth was made as a project at Insight Data Engineering by Amin Ghiasi in the Winter 2019 NY session. It is available as open source for anyone to use and modify.

