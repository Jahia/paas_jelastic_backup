#!/usr/bin/env python
import logging
import argparse
import json
import JahiaCloud.aws as AWS
import JahiaCloud.Azure as AZ

LOG_FORMAT = "%(asctime)s %(levelname)s: [%(funcName)s] %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

AZ_RG = "paas_backup"
# AZ_CRED = "{}/.azure/cred.json".format(os.environ['HOME'])
AZ_CRED = "/tmp/azurecred"

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accesskey",
                        help="the cp access key to connect")
    parser.add_argument("--secretkey",
                        help="the cp secret key to connect")
    parser.add_argument("--bucketname",
                        help="the bucket name you want to play with",
                        required=False)
    parser.add_argument("--backupname",
                        help="the backup name you want to play with",
                        required=False)
    parser.add_argument("-c", "--cloudprovider",
                        help="the backup cloudprovider"
                        )
    return parser.parse_args()


if __name__ == '__main__':
    args = argparser()
    try:
        with open('/metadata_from_HOST', 'r') as f:
            props = dict(line.strip().split('=', 1) for line in f)
            region = props['JEL_REGION']
            role = props['JEL_ENV_ROLE']
    except:
        logging.error("A problem occured when reading /metadata_from_HOST file. Exiting")
        exit(1)

    if args.cloudprovider == 'aws':
        cp = AWS.PlayWithIt(region_name=region, env=role)
        if not cp.test_if_bucket_exist(args.bucketname):
            cp.create_bucket(args.bucketname)
    else:
        aws_sm_md = AWS.PlayWithIt(region_name="eu-west-1")
        cp = AZ.PlayWithIt(region_name=region, sto_cont_name=args.backupname,
                           rg=AZ_RG, sto_account=args.bucketname,
                           authpath=AZ_CRED, env=role)
        logging.info("I need to retreive Azure auth_file from Secret Manager")
        secret = json.loads(aws_sm_md.get_secret('paas_azure_auth_file'))['value']
        secret = json.loads(secret)
        with open(AZ_CRED, 'w') as f:
            f.write(json.dumps(secret, indent=4, sort_keys=True))
        if not cp.check_if_sto_acc_exist():
            cp.create_sto_account()
        if not cp.test_if_obj_exist(object_name=cp.sto_cont_name):
            cp.create_sto_container()
        account_key = cp.get_sto_account_key()
        with open(AZ_CRED, 'w') as f:
            f.write(account_key)
