import boto3

all_regions = ['ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-southeast-1', 'ap-southeast-2',
               'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'sa-east-1',
               'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

def get_all_instances_usage(threshold_usage_percentage=5):
    from datetime import datetime, timedelta
    instances_usage_list = []
    for region_name in all_regions:
        ec2client = boto3.client('ec2', region_name=region_name)
        cloudwatch = boto3.client('cloudwatch', region_name=region_name)

        seconds_in_one_day = 60 * 60  # 1 hour  # used for granularity
        monitor_days = 1

        response = ec2client.describe_instances()
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                # This sample print will output entire Dictionary object
                # print(instance)
                # This will print will output the value of the Dictionary key 'InstanceId'
                print(instance["InstanceId"], instance.get('KeyName'), instance['InstanceType'])
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': instance["InstanceId"]
                        }
                    ],
                    MetricName='CPUUtilization',
                    StartTime=datetime.now() - timedelta(days=monitor_days),
                    EndTime=datetime.now(),
                    Period=seconds_in_one_day,
                    Statistics=[
                        'Maximum'
                    ]
                )
                print(response['Datapoints'], "\n\n")
                instances_usage_list.append({'InstanceId': instance["InstanceId"],
                                             'InstanceName': instance.get('KeyName'),
                                             'InstanceType': instance['InstanceType'],
                                             'Region': region_name,
                                             'IntervalInSecs': seconds_in_one_day,
                                             'Verdict': 'NO-ALARM',
                                             'Message': ''})
                if response['Datapoints']:
                    all_low = True
                    for dp in response['Datapoints']:
                        if dp['Maximum'] > threshold_usage_percentage:
                            all_low = False
                            break
                    if all_low:
                        instances_usage_list[-1]['Verdict'] = 'ALARM'
                        instances_usage_list[-1]['Message'] = 'Usage below {}% for {} days'.format(threshold_usage_percentage,
                                                                                                   monitor_days)

    return instances_usage_list