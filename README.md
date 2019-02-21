This repository contains my project at Insight Data Engineering program in New York in Winter 2019. It consists of an API and a website that monitor crypto market depth in real time.

# Introduction
## Market Depth
Traders constantly put bids and asks in the market. Market Depth plot shows the collective asks and bids in all crypto markets and can be used as a measure of market sentiment. For instance, if there is market depth imbalance, e.g. many more bids than asks, that shows the interest of traders in that coin. 

<img width="735" alt="screen shot 2019-02-20 at 9 38 18 pm" src="https://user-images.githubusercontent.com/12805440/53139531-e7450d80-3557-11e9-84c3-5afd89fce136.png">

This project aggregates asks and bids from more than 5000 markets and make it available for the user through the API or the website. Using this data, traders can find market depth imbalances and take advantage of them.



# Pipeline

<img width="1132" alt="screen shot 2019-02-20 at 9 29 21 pm" src="https://user-images.githubusercontent.com/12805440/53139131-a4366a80-3556-11e9-8450-31babca59c42.png">

# Try it out
## Website
Open the website at http://coinmarketdepth.live/. In addition to the crypto market depth plot, you can see two more plots that auto update every minute: Buy/Sell pressure and Market Depth Ratio plots:
<img width="768" alt="screen shot 2019-02-20 at 9 38 02 pm" src="https://user-images.githubusercontent.com/12805440/53139543-eca25800-3557-11e9-874d-01b5d7fc7d0e.png">

The buy/sell pressure is the amount of all asks/bids in the market. If you apply a percentage threshold of 5%, the website will only sum all orders within 5% of the price of each coin. 
<img width="739" alt="screen shot 2019-02-20 at 9 38 10 pm" src="https://user-images.githubusercontent.com/12805440/53139537-ea3ffe00-3557-11e9-95c6-b8b2cba8c7b2.png">

This plot shows the ratio of buy pressure to sell pressure over time. Market Depth Ratio is defined as:

MDR = (buy pressure - sell pressure) / (buy pressure + sell pressure)
## API
You can access the API at https://cqt23i4kek.execute-api.us-east-1.amazonaws.com/v1/r1 and can pass these parameters:
realtime: true or false, default: true

type: marketdepth or mar, no default - mandatory parameter

 percent: Percentage threshold to be considered when calculating buy/sell pressure. Default: 20
start_time: 

end_time: 

coin

Exchange       

                                             
# How to run the code
Add Redis Endpoint, DynamoDB table name, ARN for Steward and Worker lambda functions, Kinesis stream name, and region name to config.py
Then put your access keys for coinmarketcap and currencylayer APIs in credentials.py
run deployment/deploy.sh in a terminal. Then run deployment/start.sh
