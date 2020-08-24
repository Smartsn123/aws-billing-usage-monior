# aws-billing-usage-monior
This repo creates a package that can help you track the underused resources on your aws accounts to reduce the cost using slack integration.
It is a python script with boto3 which pulls out details from the aws cost analyzer/ ec2/ ecs and setus up proper messages/ checks to notify user.

After checking and composing the alaram message as per rules defined, it calls slack webhook to post the data into slack channel.

# How to deploy

## Create a channel webhook using slack workflow for webhook: 
https://slack.com/intl/en-in/help/articles/360041352714-Create-workflows-using-webhooks#:~:text=Workflows%20in%20Slack%20start%20in,from%20another%20service%20into%20Slack).


## Use Web-hook  url generated above inside lamda code by setting lambda env variables : 
https://github.com/Smartsn123/aws-billing-usage-monior/tree/master/billing
copy the code inside folder billing into the lambda directory.


## Schedule lambda run usin cloudwatch -> rules : 
https://blog.shikisoft.com/3-ways-to-schedule-aws-lambda-and-step-functions-state-machines/
Schedule the lambda trigger as shown above usinng cron or some cloudwatch event.
