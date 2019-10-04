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
AZ_CRED = "/tmp/azurecred.json"

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
    parser.add_argument("--displayname",
                        help="the env displayname (for metadata)",
                        required=False)
    parser.add_argument("-f", "--file",
                        help="the file you want to download or upload",
                        required=False)
    parser.add_argument("-k", "--keep",
                        help="how many backup do you want to keep",
                        type=int)
    parser.add_argument("-F", "--foreign",
                        help="if backup is from another cloud/region/role, eg: aws,eu-west-1,prod"
                        )
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
    f = cp.folder_list(bucket=bucket)
    metabucket = kwargs['metabucket']
    uid = kwargs['uid']
    folders = []
    for e in f:  # this is for remove only auto backup for a backupname
        if re.search('{}_.*_auto/?$'.format(backupname), e):
            folders.append(e)
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
            remove_from_metadata_file(metabucket, backupname, timestamp,
                                      uid=uid)
            if cp.delete_folder(f, bucket=bucket):
                logging.info("{}:{} and his content is now deleted"
                             .format(bucket, f))
            else:
                logging.warning("{}:{} and his content cannot be deleted"
                                .format(bucket, f))
    else:
        logging.info("You ask for {} backup retention and found {}"
                     .format(to_keep, len(folders)))


def list_backup(bucket, **kwargs):
    metadatakey = "{}_backup_metadata.json".format(kwargs['uid'])
    tmpfile = "/tmp/backrest_metadata.tmp"
    try:
        cp.download_file(tmpfile, object_name=metadatakey,
                         bucket=bucket, quiet=True)
        logging.info("The metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    except:
        logging.info("No metadata file yet, nothing to list")
        listbackups = {"backups": []}
    return str(json.dumps(listbackups))


def add_to_metadata_file(bucket, backupname, timestamp, mode,
                         dx_product, dx_version, **kwargs):
    metadatakey = "{}_backup_metadata.json".format(kwargs['uid'])
    tmpfile = "/tmp/backrest_metadata.tmp"
    folder = "{}_{}_{}".format(backupname, timestamp, mode)
    try:
        cp.download_file(tmpfile, object_name=metadatakey, bucket=bucket)
        logging.info("A existing metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    except:
        logging.info("No existing metadata file found in {}, start a new one"
                     .format(bucket))
        listbackups = {"backups": []}


    d = {"name": backupname,
         "timestamp": timestamp,
         "mode": mode,
         "size": cp.folder_size(folder, bucket=kwargs['frombucket']),
         "product": dx_product,
         "version": dx_version,
         "cloudprovider": cloudprovider,
         "region": region,
         "envrole": role
         }

    try:
        d['envname'] = os.environ['envName']
    except:
        pass
    try:
        d['displayname'] = kwargs['displayname']
    except:
        pass
    try:
        d['uid'] = kwargs['uid']
    except:
        pass

    listbackups['backups'].append(d)

    with open(tmpfile, 'w+') as tmp:
        tmp.write(json.dumps(listbackups, indent=2, sort_keys=True))

    try:
        cp.upload_file(tmpfile, bucket=bucket, object_name=metadatakey)
        return True
    except:
        return False

def remove_from_metadata_file(bucket, backupname, timestamp, **kwargs):
    metadatakey = "{}_backup_metadata.json".format(kwargs['uid'])
    tmpfile = "/tmp/backrest_metadata.tmp"
    try:
        cp.download_file(tmpfile, object_name=metadatakey, bucket=bucket)
        logging.info("A existing metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    except:
        logging.info("No metadata file yet, nothing to remove")
        return True

    for bck in listbackups['backups']:
        if bck['name'] == backupname and bck['timestamp'] == timestamp:
            listbackups['backups'].remove(bck)
            break

    with open(tmpfile, 'w+') as tmp:
        tmp.write(json.dumps(listbackups, indent=2, sort_keys=True))

    try:
        cp.upload_file(tmpfile, bucket=bucket, object_name=metadatakey)
        return True
    except:
        return False


if __name__ == '__main__':
    args = argparser()


    if args.foreign:
        cloudprovider = args.foreign.split(',')[0]
        region = args.foreign.split(',')[1]
        role = args.foreign.split(',')[2]
        logging.info("you specify a foreign env: {} on {}"
                     .format(region, cloudprovider))
    else:
        try:
            with open('/metadata_from_HOST', 'r') as f:
                props = dict(line.strip().split('=', 1) for line in f)
                cloudprovider = props['JEL_CLOUDPROVIDER']
                if cloudprovider not in ['aws', 'azure']:
                    exit(1)
                region = props['JEL_REGION']
                role = props['JEL_ENV_ROLE']
        except:
            logging.error("A problem occured when reading /metadata_from_HOST file. Exiting")
            exit(1)


    object_name = "{}_{}_{}/{}".format(args.backupname, args.timestamp,
                                       args.mode, args.file)
    # cloudprovider = args.cloudprovider

    try:
        dx_version = os.environ['DX_VERSION']
        dx_product = 'dx'
    except:
        dx_version = dx_product = 'undefined'


    def getuid():
        try:
            uid = re.sub(r'^jc(dev|prod)(?P<uid>[0-9]+).*$',
                         r'\g<uid>',
                         args.bucketname)
        except:
            logging.error("Cannot find UID in bucketname ({})"
                          .format(args.bucketname))
            exit(1)
        return uid

    def setmetabucketname():
        return "jc{}backupmetadata".format(role)

    logging.info("You want to work with {} as cloud provider. Let's go"
                 .format(cloudprovider))

    if cloudprovider == 'aws':
        import JahiaCloud.aws as JC
        cp = JC.PlayWithIt(region_name=region, env=role)
    elif cloudprovider == 'azure':
        import JahiaCloud.Azure as JC
        import JahiaCloud.aws as AWS
        cp = JC.PlayWithIt(region_name=region, sto_cont_name=args.backupname,
                           rg=AZ_RG, sto_account=args.bucketname,
                           authpath=AZ_CRED, env=role)
        sm = AWS.PlayWithIt(region_name="eu-west-1")
        logging.info("I need to retreive Azure auth_file from Secret Manager")
        secret = json.loads(sm.get_secret('paas_azure_auth_file'))['value']
        secret = json.loads(secret)
        with open(AZ_CRED, 'w') as f:
            f.write(json.dumps(secret, indent=4, sort_keys=True))

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
        uid = getuid()
        metabucket = setmetabucketname()
        print(add_to_metadata_file(metabucket, args.backupname,
                                   timestamp, args.mode,
                                   dx_product, dx_version,
                                   displayname=args.displayname,
                                   uid=uid, frombucket=args.bucketname))
    elif args.action == 'delmeta':
        uid = getuid()
        metabucket = setmetabucketname()
        print(remove_from_metadata_file(metabucket, args.backupname,
                                        timestamp, uid=uid))
    elif args.action == 'list':
        uid = getuid()
        metabucket = setmetabucketname()
        print(list_backup(metabucket, uid=uid))
    elif args.action == 'rotate':
        uid = getuid()
        metabucket = setmetabucketname()
        retention(args.bucketname, args.backupname, args.keep,
                  metabucket=metabucket, uid=uid)
