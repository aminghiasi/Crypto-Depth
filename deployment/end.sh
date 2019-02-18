aws events remove-targets --rule Call-Lambda-Master --ids "1"
aws events delete-rule --name "Call-Lambda-Master"
aws kinesis delete-stream --stream-name orders 

