import boto3
import os
import json

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import bill_breakdown, ec2_usage_monitor



def lambda_handler(event, context):
    message_text = ""
    if event['TYPE'] == 'billing':
        message_text += bill_breakdown.get_bill_breakdown()
        send_message_to_slack(message_text, ":money_with_wings:")
    elif event['TYPE'] == 'quote':
        message_text = "Daily motivational pill:\n"
        response = json.loads(urlopen(Request("https://quotes.rest/qod?language=en")).read())
        print(response)
        message_text += response['contents']['quotes'][0]['quote']
        send_message_to_slack(message_text)
    elif event['TYPE'] == 'EC2Usage':
        usages = ec2_usage_monitor.get_all_instances_usage()
        buffer_str = "EC2 Instance under-usage alert\n"
        buffer_str += "-----------------------------------------------------------------------------------------\n"
        buffer_str += "%-25s  %-15s %-20s %10s %10s\n" % ("Name", "Type" ,"Id", "Max(CPU)1day", "Region")
        buffer_str += "----------------------------------------------------------------------------------------\n"
        for usage in usages:
            if usage['Verdict'] == 'ALARM':
                buffer_str += "%-25s %-15s %-20s %8.2f %15s\n" % (usage['InstanceName'], usage['InstanceType'], usage['InstanceId'], usage['MaxUsage'], usage['Region'] )
        send_message_to_slack(buffer_str,  ":alert:")




def send_message_to_slack(message_text, emoji_text=""):
    slack_message = {
        "aws_account_id": boto3.client('sts').get_caller_identity().get('Account'),
        "aws_account_name": os.environ.get('AWS_ACCOUNT_NAME'),
        "message_text": message_text,
        "owner": os.environ.get('ACCOUNT_OWNER'),
        "emoji": emoji_text
    }
    hook_url = os.environ.get('SLACK_WEBHOOK_URL')
    print(slack_message["message_text"])
    if hook_url and message_text:
        req = Request(hook_url, json.dumps(slack_message).encode())
        try:
            response = urlopen(req)
            text = response.read()
            print("Message posted to", hook_url, text)
        except HTTPError as e:
            print("Request failed: s", e.code, e.reason)
        except URLError as e:
            print("Server connection failed: ", e.reason)
    else:
        print(slack_message)