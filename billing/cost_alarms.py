import boto3
import os
import json

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import bill_breakdown, ec2_usage_monitor


sparks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇']  # Leaving out the full block because Slack doesn't like it: '█'


def sparkline(datapoints):
    lower = min(datapoints)
    upper = max(datapoints)
    width = upper - lower
    n_sparks = len(sparks) - 1

    line = ""

    for dp in datapoints:
        scaled = 1 if width == 0 else (dp - lower) / width
        which_spark = int(scaled * n_sparks)
        line += (sparks[which_spark])
    while len(line) < 7:
        line += sparks[0]
    return line


def lambda_handler(event, context):
    message_text = ""
    if event['TYPE'] == 'billing':
        message_text += bill_breakdown.get_bill_breakdown()
    elif event['TYPE'] == 'quote':
        message_text = "Daily motivational pill:\n"
        response = json.loads(urlopen(Request("https://quotes.rest/qod?language=en")).read())
        print(response)
        message_text += response['contents']['quotes'][0]['quote']
    elif event['TYPE'] == 'EC2Usage':
        usages = ec2_usage_monitor.get_all_instances_usage()
        for usage in usages:
            if usage['Verdict'] == 'ALARM':
                message_text += "\n-----------------------------------------------------------\n"
                message_text += "\n".join([key + ": " + val for key, val in usage.items()])
        if message_text:
            message_text += ":rotating_light:"

    slack_message = {
        "aws_account_id": boto3.client('sts').get_caller_identity().get('Account'),
        "aws_account_name": os.environ.get('AWS_ACCOUNT_NAME'),
        "message_text": message_text,
        "owner": os.environ.get('ACCOUNT_OWNER')
    }
    hook_url = os.environ.get('SLACK_WEBHOOK_URL')
    print(slack_message["message_text"])
    if hook_url:
        req = Request(hook_url, json.dumps(slack_message).encode())
        try:
            response = urlopen(req)
            text = response.read()
            print("Message posted to", hook_url)
        except HTTPError as e:
            print("Request failed: s", e.code, e.reason)
        except URLError as e:
            print("Server connection failed: ", e.reason)
    else:
        print(slack_message)