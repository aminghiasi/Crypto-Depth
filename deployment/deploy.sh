# Adding lambda master function to AWS
aws lambda delete-function --function-name lambda_master
rm -rf lambda_master.zip package outfile.txt
mkdir package

zip lambda_master.zip lambda_master.py markets.txt config.py

aws lambda create-function \
--function-name lambda_master \
--runtime python3.7 \
--role arn:aws:iam::551434500781:role/service-role/Role \
 --handler lambda_master.lambda_handler  \
--timeout 300 \
--zip-file fileb://lambda_master.zip

# Adding lambda master function to AWS
aws lambda delete-function --function-name lambda_steward
rm -rf lambda_steward.zip package outfile.txt
mkdir package

zip lambda_steward.zip lambda_steward.py config.py

aws lambda create-function \
--function-name lambda_steward \
--runtime python3.7 \
--role arn:aws:iam::551434500781:role/service-role/Role \
 --handler lambda_steward.lambda_handler  \
--timeout 300 \
--zip-file fileb://lambda_steward.zip


# Adding lambda worker function to AWS
aws lambda delete-function --function-name lambda_worker
rm -rf lambda_worker.zip package outfile.txt lambda_master.zip
mkdir package
cd package
pip install ccxt -t .
zip -r9 ../lambda_worker.zip .  ../config.py

cd ..
zip -g lambda_worker.zip lambda_worker.py


aws lambda create-function --function-name lambda_worker --runtime python3.7  --role arn:aws:iam::551434500781:role/service-role/Role  --handler lambda_worker.lambda_handler  --timeout 60 --zip-file fileb://lambda_worker.zip


# Adding lambda function that is called by the AWS API Gateway
aws lambda delete-function --function-name API_Lambda
rm -rf API_Lambda.zip package outfile.txt
mkdir package
cd package
pip install redis -t .
zip -r9 ../API_Lambda.zip .  ../config.py
cd ..
zip -g API_Lambda.zip API_Lambda.py

aws lambda create-function \
--function-name API_Lambda \
--runtime python3.7 \
--role arn:aws:iam::551434500781:role/service-role/Role \
 --handler API_Lambda.lambda_handler  \
--timeout 10 \
--zip-file fileb://API_Lambda.zip \
--vpc-config SubnetIds=subnet-0bef42b019410805b,SecurityGroupIds=sg-0bee118ea544b4a91
