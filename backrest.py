#!/usr/bin/env python
import logging
import argparse
import os
import json
import re

LOG_FORMAT = "%(asctime)s %(levelname)s: [%(funcName)s] %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


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
                        required=True)
    parser.add_argument("--backupname",
                        help="the backup name you want to play with",
                        required=True)
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


def download(bucket, object_name, filename):
    cp = JC.PlayWithIt(region_name=region)
    if cp.download_file(bucket, filename, object_name):
        logging.info(r"well done \o/")
        return True
    else:
        logging.error("problem ^_^")
        return False


def upload(filename, bucket, object_name):
    cp = JC.PlayWithIt(region_name=region)
    if cp.upload_file(filename, bucket, object_name):
        logging.info("{} is now uploaded as {}:{}"
                     .format(filename, bucket, object_name))
        return True
    else:
        logging.error("A problem occured when trying to upload {} to {}:{}"
                      .format(filename, bucket, object_name))
        return False


def retention(bucket, backupname, to_keep):
    cp = JC.PlayWithIt(region_name=region)
    folders = cp.folder_list(bucket)
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
            if cp.delete_folder(bucket, f):
                logging.info("{}:{} and his content is now deleted"
                             .format(bucket, f))
            else:
                logging.warning("{}:{} and his content cannot be deleted"
                                .format(bucket, f))
    else:
        logging.info("You ask for {} backup retention and found {}"
                     .format(to_keep, len(folders)))


def list_backup(bucket, backupname):
    metadatakey = "metadata"
    tmpfile = "/tmp/backrest_metadata.tmp"
    cp = JC.PlayWithIt(region_name=region)
    if cp.download_file(bucket, tmpfile, metadatakey):
        logging.info("The metadata file have been downloaded from {}"
                     .format(bucket))
        with open(tmpfile, 'r') as f:
            listbackups = json.load(f)
    else:
        logging.info("No metadata file yet, nothing to list")
        listbackups = {"backups": []}
    return str(listbackups)


def add_to_metadata_file(bucket, backupname, timestamp, mode,
                         dx_product, dx_version):
    metadatakey = "metadata"
    tmpfile = "/tmp/backrest_metadata.tmp"
    cp = JC.PlayWithIt(region_name=region)
    folder = "{}_{}_{}".format(backupname, timestamp, mode)
    if cp.download_file(bucket, tmpfile, metadatakey):
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
         "size": cp.folder_size(bucket, folder),
         "product": dx_product,
         "version": dx_version
         }

    listbackups['backups'].append(d)

    with open(tmpfile, 'w+') as tmp:
        tmp.write(json.dumps(listbackups, indent=2, sort_keys=True))

    if cp.upload_file(tmpfile, bucket, metadatakey):
        return True
    else:
        return False

def remove_from_metadata_file(bucket, backupname, timestamp):
    metadatakey = "metadata"
    tmpfile = "/tmp/backrest_metadata.tmp"
    cp = JC.PlayWithIt(region_name=region)
    if cp.download_file(bucket, tmpfile, metadatakey):
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

    if cp.upload_file(tmpfile, bucket, metadatakey):
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

    dx_version = os.environ['DX_VERSION']
    dx_product = os.environ['_PROVIDE']


    if cloudprovider == 'aws':
        import JahiaCloud.aws as JC

    logging.info("You want to work with {} as cloud provider. Let's go"
                 .format(cloudprovider))

    if args.file:
        print("blablabla {}".format(args.file))

    if args.action == 'upload':

        upload(args.file, args.bucketname, object_name)
        if args.keep:
            retention(args.bucketname, args.backupname, args.keep)
    elif args.action == 'download':
        download(args.bucketname, object_name, args.file)
    elif args.action == 'addmeta':
        print(add_to_metadata_file(args.bucketname, args.backupname,
                                   args.timestamp, args.mode,
                                   dx_product, dx_version))
    elif args.action == 'delmeta':
        print(remove_from_metadata_file(args.bucketname, args.backupname,
                                        args.timestamp))
    elif args.action == 'list':
        print(list_backup(args.bucketname, args.backupname))
    elif args.action == 'rotate':
        retention(args.bucketname, args.backupname, args.keep)
