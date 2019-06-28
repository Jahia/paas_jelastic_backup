#!/usr/bin/env python
import logging
import argparse
import os
import json
import re
from datetime import datetime

LOG_FORMAT = "%(asctime)s %(levelname)s: [%(funcName)s] %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

AZ_RG = "paas_backup"
# AZ_CRED = "{}/.azure/cred.json".format(os.environ['HOME'])
AZ_CRED = "/tmp/azurecred.json".format(os.environ['HOME'])

def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accesskey",
                        help="the cp access key to connect")
    parser.add_argument("--secretkey",
                        help="the cp secret key to connect")
    parser.add_argument("-a", "--action",
                        help="do you want to do ?",
                        choices=['upload', 'download',
                                 'list',
                                 'addmeta', 'delmeta',
                                 'rotate'],
                        required=True)
    parser.add_argument("--bucketname",
                        help="the bucket name you want to play with",
                        required=False)
    parser.add_argument("--backupname",
                        help="the backup name you want to play with",
                        required=False)
    parser.add_argument("-f", "--file",
                        help="the file you want to download or upload",
                        required=False)
    parser.add_argument("-k", "--keep",
                        help="how many backup do you want to keep",
                        type=int)
    # parser.add_argument("-c", "--cloudprovider",
    #                     help="the cloud provider for the operations",
    #                     required=True,
    #                     choices=['aws'])
    parser.add_argument("-t", "--timestamp",
                        help="timestamp in format %%Y-%%m-%%dT%%H:%%M:00",
                        required=False)
    parser.add_argument("-m", "--mode",
                        help="this is a manual launch or auto launch ?",
                        choices=['auto', 'manual'])
    return parser.parse_args()


def download(bucket, object_name, filename, **kwargs):
    if cp.download_file(filename, object_name=object_name, bucket=bucket):
        logging.info(r"well done \o/")
        return True
    else:
        logging.error("problem ^_^")
        return False


def upload(filename, bucket, object_name, **kwargs):
    if cp.upload_file(filename, bucket=bucket, object_name=object_name):
        logging.info("{} is now uploaded as {}:{}"
                     .format(filename, bucket, object_name))
        return True
    else:
        logging.error("A problem occured when trying to upload {} to {}:{}"
                      .format(filename, bucket, object_name))
        return False


def retention(bucket, backupname, to_keep, **kwargs):
    folders = cp.folder_list(bucket=bucket)
    if to_keep < len(folders):
        logging.info("You ask for {} backup retention but found {}"
                     .format(to_keep, len(folders)))
        to_remove = folders[:len(folders)-len(folders[-to_keep:])]
        logging.info("I should remove this: {}".format(to_remove))
        for f in to_remove:
            timestamp = re.split('_', f)[1]
            print("backupname: {}\ttimestamp: {}"
                  .format(backupname, timestamp))
            logging.info("Removing {} ({} from metadata file)"
                         .format(backupname, timestamp))
            remove_from_metadata_file(bucket, backupname, timestamp)
            if cp.delete_folder(f, bucket=bucket):
                logging.info("{}:{} and his content is now deleted"
                             .format(bucket, f))
            else:
                logging.warning("{}:{} and his content cannot be deleted"
                                .format(bucket, f))
    else:
        logging.info("You ask for {} backup retention and found {}"
                     .format(to_keep, len(folders)))


def list_backup(bucket, backupname, **kwargs):
    metadatakey = "metadata"
    tmpfile = "/tmp/backrest_metadata.tmp"
    if cp.download_file(tmpfile, object_name=metadatakey,
                        bucket=bucket, quiet=True):
        logging.info("The metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    else:
        logging.info("No metadata file yet, nothing to list")
        listbackups = {"backups": []}
    return str(json.dumps(listbackups))


def add_to_metadata_file(bucket, backupname, timestamp, mode,
                         dx_product, dx_version, **kwargs):
    metadatakey = "metadata"
    tmpfile = "/tmp/backrest_metadata.tmp"
    folder = "{}_{}_{}".format(backupname, timestamp, mode)
    if cp.download_file(tmpfile, object_name=metadatakey, bucket=bucket):
        logging.info("A existing metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    else:
        logging.info("No existing metadata file found in {}, start a new one"
                     .format(bucket))
        listbackups = {"backups": []}

    d = {"name": backupname,
         "timestamp": timestamp,
         "mode": mode,
         "size": cp.folder_size(folder, bucket=bucket),
         "product": dx_product,
         "version": dx_version
         }

    listbackups['backups'].append(d)

    with open(tmpfile, 'w+') as tmp:
        tmp.write(json.dumps(listbackups, indent=2, sort_keys=True))

    if cp.upload_file(tmpfile, bucket=bucket, object_name=metadatakey):
        return True
    else:
        return False

def remove_from_metadata_file(bucket, backupname, timestamp, **kwargs):
    metadatakey = "metadata"
    tmpfile = "/tmp/backrest_metadata.tmp"
    if cp.download_file(tmpfile, object_name=metadatakey, bucket=bucket):
        logging.info("A existing metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    else:
        logging.info("No metadata file yet, nothing to remove")
        return True

    for bck in listbackups['backups']:
        if bck['name'] == backupname and bck['timestamp'] == timestamp:
            listbackups['backups'].remove(bck)
            break

    with open(tmpfile, 'w+') as tmp:
        tmp.write(json.dumps(listbackups, indent=2, sort_keys=True))

    if cp.upload_file(tmpfile, bucket=bucket, object_name=metadatakey):
        return True
    else:
        return False


if __name__ == '__main__':
    args = argparser()

    try:
        with open('/metadata_from_HOST', 'r') as f:
            props = dict(line.strip().split('=', 1) for line in f)
            cloudprovider = props['JEL_CLOUDPROVIDER']
            if cloudprovider not in ['aws', 'azure']:
                exit(1)
            region = props['JEL_REGION']
    except:
        logging.error("A problem occured when reading /metadata_from_HOST file. Exiting")
        exit(1)


    object_name = "{}_{}_{}/{}".format(args.backupname, args.timestamp,
                                       args.mode, args.file)
    # cloudprovider = args.cloudprovider

    try:
        dx_version = os.environ['DX_VERSION']
        dx_product = os.environ['_PROVIDE']
    except:
        pass

    logging.info("You want to work with {} as cloud provider. Let's go"
                 .format(cloudprovider))

    if cloudprovider == 'aws':
        import JahiaCloud.aws as JC
        cp = JC.PlayWithIt(region_name=region)
    elif cloudprovider== 'azure':
        import JahiaCloud.Azure as JC
        import JahiaCloud.aws as AWS
        cp = JC.PlayWithIt(region_name=region, sto_cont_name=args.backupname,
                           rg=AZ_RG, sto_account=args.bucketname,
                           authpath=AZ_CRED)
        sm = AWS.PlayWithIt(region_name="eu-west-1")
        logging.info("I need to retreive Azure auth_file from Secret Manager")
        secret = json.loads(sm.get_secret('paas_azure_auth_file'))['value']
        secret = json.loads(secret)
        with open(AZ_CRED, 'w') as f:
            f.write(json.dumps(secret, indent=4, sort_keys=True))

    if args.file:
        print("blablabla {}".format(args.file))

    if args.timestamp:
        timestamp = args.timestamp
    else:
        timestamp = datetime.today().strftime('%Y-%m-%dT%H:%M:00')

    if args.action == 'upload':
        upload(args.file, args.bucketname, object_name)
        if args.keep:
            retention(args.bucketname, args.backupname, args.keep)
    elif args.action == 'download':
        download(args.bucketname, object_name, args.file)
    elif args.action == 'addmeta':
        print(add_to_metadata_file(args.bucketname, args.backupname,
                                   timestamp, args.mode,
                                   dx_product, dx_version))
    elif args.action == 'delmeta':
        print(remove_from_metadata_file(args.bucketname, args.backupname,
                                        timestamp))
    elif args.action == 'list':
        print(list_backup(args.bucketname, args.backupname))
    elif args.action == 'rotate':
        retention(args.bucketname, args.backupname, args.keep)
