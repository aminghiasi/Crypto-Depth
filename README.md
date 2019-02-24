Crypto-Depth is a real-time pipeline that aggregates markets depth for 5000+ crypto markets.

# Overview
Traders constantly put asks and bids on a crypto coin. The Market Depth plot shows the collective asks and bids on a coin and can be used as a measure of market sentiment. For instance, if there is a market depth imbalance, e.g. many more bids than asks, that shows that traders are interest in that coin. <p align="center">
<img width="700" alt="screen shot 2019-02-23 at 7 37 38 pm" src="https://user-images.githubusercontent.com/12805440/53293484-7e9da100-37a2-11e9-9138-de77d4ba1732.png">
</p>


Crypto-Depth is a server-less platform that provides traders market depth data using AWS Lambda, Kinesis, DynamoDB, and API Gateway. It features:
* A dashboard to analyze market depth for crypto
* Monitoring of 5000+ crypto markets
* A real-time and historical api for trading bots

This repository has what you need to stand up your own version of Crypro-Depth in your own AWS projects.

[Slide Deck](https://docs.google.com/presentation/d/14pjAVgnJGYHm2wY2WbIjx3lpbVU8mi2FC4btlx4BGwU/edit#slide=id.g4f463f984c_2_0)

# Pipeline
<img width="1132" alt="screen shot 2019-02-23 at 7 09 08 pm" src="https://user-images.githubusercontent.com/12805440/53293442-b3f5bf00-37a1-11e9-8c38-798be6115b1a.png">


# Requirments
* AWS Account and Python 3.7
* [CoinMarketCap](https://coinmarketcap.com/api/) API Key
* [Currencylayer](https://currencylayer.com) API Key

# Installation
```bash
git clone https://github.com/aminghiasi/Crypto-Depth.git
```
Add your Redis Endpoint, DynamoDB table name, ARN for Steward and Worker lambda functions, Kinesis stream name, and region name to config.py.

Then put your access keys for coinmarketcap and currencylayer APIs in credentials.py and do:
```bash
. ./deployment/deploy.sh
. ./deployment/run.sh
```

# Getting Started
Open the website at http://coinmarketdepth.live/. Everything  auto-updates every minute. You can see three plots: crypto market depth plot, Buy/Sell pressure and Market Depth Ratio plots. crypto market depth plot is explained above. 

The buy/sell pressure is the amount of all asks/bids in the market over time. If you apply a percentage threshold of 5%, the website will only sum all orders within 5% of the price of each coin. <p align="center">
<img width="786" alt="screen shot 2019-02-23 at 8 31 03 pm" src="https://user-images.githubusercontent.com/12805440/53293850-f6bb9500-37a9-11e9-8abe-b25b7840d47a.png">

</p>

This plot shows the ratio of buy pressure to sell pressure over time. Market Depth Ratio is defined as:

MDR = (buy pressure - sell pressure) / (buy pressure + sell pressure)<p align="center">
<img width="823" alt="screen shot 2019-02-23 at 8 29 47 pm" src="https://user-images.githubusercontent.com/12805440/53293839-ca077d80-37a9-11e9-975c-f0f8026a652a.png">
</p>




# API
You can access the API at https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1 and can pass these parameters:<p align="center">
<img width=“600” alt="screen shot 2019-02-23 at 8 28 03 pm" src="https://user-images.githubusercontent.com/12805440/53293828-8b71c300-37a9-11e9-8c4b-814c4ad62a96.png">
</p>


# Credits
Crypto-Depth was made as a project at Insight Data Engineering by Amin Ghiasi in the Winter 2019 NY session. It is available as open source for anyone to use and modify.
