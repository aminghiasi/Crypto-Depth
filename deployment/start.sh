aws events put-rule --name "Call-Lambda-Master" --schedule-expression "rate(1 minute)"
aws events put-targets --rule Call-Lambda-Master --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:551434500781:function:lambda_master"
aws kinesis create-stream --stream-name orders --shard-count 1

