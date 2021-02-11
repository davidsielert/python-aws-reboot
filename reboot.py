import argparse
import boto3
import botocore
import jmespath
from tabulate import tabulate
import click
import time


def get_ec2_instances(names, region,filters=[]):
    """Fetches a instances id's based on a list of name(s)

        Parameters:
        names (array): list of names
        region (string): region

        Returns:
        array: Array of instance Id strings
   """
    ec2 = boto3.client("ec2", region_name=region)
    paginator = ec2.get_paginator('describe_instances')
    instanceIds = []
    #Setup filters in the future to accept more input.. possibly ENV tags or anything else useful 
    filters =  filters + [{
        'Name': 'tag:Name',
        'Values': names
    }]
    try:
        response_iterator = paginator.paginate(
            Filters=filters,
            DryRun=False,
            PaginationConfig={
                'MaxItems': 1000,
                'PageSize': 1000,
            })
        for response in response_iterator:
            instanceid_results = jmespath.search(
                "Reservations[].Instances[].InstanceId",
                response
            )
            instanceIds = instanceIds + instanceid_results
    except botocore.exceptions.ClientError as error:
        print(error)
        exit()

    return instanceIds


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def run_reboot(instance_ids, region, batch, wait, dry_run):
    """Main Entry

        Parameters:
        instance_ids (list): list of instance ids
        region (str): region name
        batch (int): batch size
        wait (int): wait time in seconds
        dry_run (bool): dry run mode

   """
    ec2 = boto3.client("ec2", region_name=region)
    if batch == 0:
        print('Rebooting Instances')
        try: 
            response = ec2.reboot_instances(
                InstanceIds=instance_ids,
                DryRun=dry_run
            )
        except botocore.exceptions.ClientError as error:
            if  error.response['Error']['Code']  == 'DryRunOperation':
                print(error)
            else:
                raise(error)

    chunked_ids = [x for x in chunks(instance_ids, batch)]
    for index in range(len(chunked_ids)):
        print(f'Rebooting batch [{index + 1}/{len(chunked_ids)}]')
        try:
            response = ec2.reboot_instances(
                InstanceIds=chunked_ids[index],
                    DryRun=dry_run
                )
            print(response)
            time.sleep(wait)
        except botocore.exceptions.ClientError as error:
            if  error.response['Error']['Code']  == 'DryRunOperation':
                print(error)
            else:
                raise(error)


def handler():
    """Main Entry - for readability

   """

    # basic args setup
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('names', metavar='Name', type=str, nargs='+',
                        help='instance Name tag to reboot')
    parser.add_argument('--region', action='store', default='us-east-1')
    parser.add_argument('--verbose', action='store_true',
                        default=False, help='Enable Verbose Output')
    parser.add_argument('--dry-run', action='store_true',
                        default=True, help='Enable Dry Run')
    parser.add_argument('--batch', action='store', type=int,default=0, help='Batch Size')
    parser.add_argument('--wait', action='store', type=int,default=500, help='wait time')
    parser.add_argument('--no-confirm', action='store_true',
                        default=False, help='Disable Confirmation ')
    parser.add_argument('--no-reboot', action='store_true',
                        default=False, help='Disable reboot ')
    args = parser.parse_args()
    instance_ids = get_ec2_instances(args.names, args.region)
    # Print instance id's if required or if found more than 1 (Production consideration)
    if args.verbose is True or args.no_reboot is True or len(instance_ids) > 1:
        print('Found the following instances')
        print(tabulate([[n] for n in instance_ids], headers=['Instance ID']))
    if args.no_reboot is True:
        exit()
    # More production considerations
    if len(instance_ids) > 1 and args.batch < 1:
        if click.confirm('WARNING: found more than one instance would you like to batch reboots?', default=True):
            args.batch = click.prompt(
                'Please enter batch size', type=int, default=5)
            args.wait = click.prompt(
                'Please enter Wait time between batches in seconds', type=int, default=500)
   
    message = f"Going to reboot {len(instance_ids)}"
    message = message + " in batch mode" if args.batch > 0 else message
    message = message + ", with dry run enabled" if args.dry_run is True else message
    message += " OK?"
    if args.no_confirm is True:
        run_reboot(instance_ids, args.region,
                   args.batch, args.wait, args.dry_run)
    elif click.confirm(message, default=False):
        run_reboot(instance_ids, args.region,
                   args.batch, args.wait, args.dry_run)


if __name__ == '__main__':
    handler()
