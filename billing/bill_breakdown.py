import boto3
from collections import defaultdict
import datetime
import os

n_days = 7
today = datetime.datetime.today()
week_ago = today - datetime.timedelta(days=n_days)

def get_bill_breakdown():
    message_text = ""
    client = boto3.client('ce')
    query = {
        "TimePeriod": {
            "Start": week_ago.strftime('%Y-%m-%d'),
            "End": today.strftime('%Y-%m-%d'),
        },
        "Granularity": "DAILY",
        "Filter": {
            "Not": {
                "Dimensions": {
                    "Key": "RECORD_TYPE",
                    "Values": [
                        "Credit",
                        "Refund",
                        "Upfront",
                        "Support",
                    ]
                }
            }
        },
        "Metrics": ["UnblendedCost"],
        "GroupBy": [
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            },
        ],
    }
    result = client.get_cost_and_usage(**query)
    buffer = "-------------------------------------------------------------\n"
    buffer += "%-40s %-7s %10s\n" % ("Aws Service", "Last 7d", "Yday($)")
    buffer += "-------------------------------------------------------------\n"
    cost_per_day_by_service = defaultdict(list)
    # Build a map of service -> array of daily costs for the time frame
    for day in result['ResultsByTime']:
        for group in day['Groups']:
            key = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])

            cost_per_day_by_service[key].append(cost)
    # Sort the map by yesterday's cost
    most_expensive_yesterday = sorted(cost_per_day_by_service.items(), key=lambda i: i[1][-1], reverse=True)
    for service_name, costs in most_expensive_yesterday[:5]:
        buffer += "%-40s %s %10.2f\n" % (service_name, sparkline(costs), costs[-1])
    other_costs = [0.0] * n_days
    for service_name, costs in most_expensive_yesterday[5:]:
        for i, cost in enumerate(costs):
            other_costs[i] += cost
    buffer += "%-40s %s %10.2f\n" % ("Other aws services", sparkline(other_costs), other_costs[-1])
    total_costs = [0.0] * n_days
    for day_number in range(n_days):
        for service_name, costs in most_expensive_yesterday:
            try:
                total_costs[day_number] += costs[day_number]
            except IndexError:
                total_costs[day_number] += 0.0
    buffer += "-------------------------------------------------------------\n"
    buffer += "%-40s %s %10.2f\n" % ("Total cost incurred", sparkline(total_costs), total_costs[-1])
    credits_expire_date = os.environ.get('CREDITS_EXPIRE_DATE')
    if credits_expire_date:
        credits_expire_date = datetime.datetime.strptime(credits_expire_date, "%m/%d/%Y")

        credits_remaining_as_of = os.environ.get('CREDITS_REMAINING_AS_OF')
        credits_remaining_as_of = datetime.datetime.strptime(credits_remaining_as_of, "%m/%d/%Y")

        credits_remaining = float(os.environ.get('CREDITS_REMAINING'))

        days_left_on_credits = (credits_expire_date - credits_remaining_as_of).days
        allowed_credits_per_day = credits_remaining / days_left_on_credits

        relative_to_budget = (total_costs[-1] / allowed_credits_per_day) * 100.0

        if relative_to_budget < 60:
            emoji = ":white_check_mark:"
        elif relative_to_budget > 110:
            emoji = ":rotating_light:"
        else:
            emoji = ":warning:"

        summary = "%s Yesterday's cost of $%5.2f is %.0f%% of credit budget $%5.2f for the day." % (
            emoji,
            total_costs[-1],
            relative_to_budget,
            allowed_credits_per_day,
        )
    else:
        summary = "Yesterday's cost was $%5.2f." % (total_costs[-1])
    message_text += "Daily AWS Account billing details:\n({}/{})\n".format(
        boto3.client('sts').get_caller_identity().get('Account'),
        os.environ.get('AWS_ACCOUNT_NAME')) + summary + "\n" + buffer + "\n"
    return message_text
