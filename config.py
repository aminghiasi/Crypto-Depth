region_name = 'us-east-1'

# Redis endpoint
redis_endpoint = 'real-time-orders.kr2igu.0001.use1.cache.amazonaws.com'

# DynamoDB table name
dynamodb_table_name = 'crypto_market_depth'

# Steward lambda function arn
steward_arn = 'arn:aws:lambda:us-east-1:551434500781:function:lambda_steward'

# Worker lambda function arn
worker_arn = 'arn:aws:lambda:us-east-1:551434500781:function:lambda_worker'

kinesis_stream_name = 'orders'

# Maximum percentage to keep in market depth
market_depth_max_percentage = 20.
market_depth_increment = 0.5
