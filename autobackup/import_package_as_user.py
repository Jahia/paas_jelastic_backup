#!/usr/bin/env python3

import logging
import argparse
import json
import re
from pylastic import *
from cysystemd import journal

LOG_FORMAT = "%(asctime)s %(levelname)s: [%(funcName)s] %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


try:
    with open('/metadata_from_HOST', 'r') as f:
        props = dict(line.strip().split('=', 1) for line in f)
        cloudprovider = props['JEL_CLOUDPROVIDER']
        if cloudprovider not in ['aws', 'azure']:
            logging.error("that will not working on {}".format(cloudprovider))
            exit(1)
        cluster_role = props['JEL_ENV_ROLE']
        if cluster_role == 'dev':
            JELHOST = "app.dev.j.jahia.com"
        elif cluster_role == 'prod':
            JELHOST = "app.j.jahia.com"
except:
    logging.error("Problem when reading /metadata_from_HOST. Exiting")
    exit(1)

logging.info("This is a {} cluster, used DNS will be {}."
             .format(cluster_role, JELHOST))


def argparser():
    parser = argparse.ArgumentParser()
    masterlog = parser.add_argument_group('master login')
    masterlog.add_argument("-l", "--login",
                           help="master login name")
    masterlog.add_argument("-p", "--password",
                           help="master password")
    masterlog.add_argument("-t", "--token",
                           help="master token")
    target = parser.add_argument_group('target')
    target.add_argument("-s", "--sudo",
                        help="target user email")
    target.add_argument("-e", "--env",
                        help="target env")
    target.add_argument("-r", "--region",
                        help="region unique name")
    package = parser.add_argument_group('package')
    package.add_argument("-u", "--url",
                         help="package url")
    package.add_argument("--settings",
                         help="package settings (dict format)")
    cluster = parser.add_argument_group('Jelastic Cluster')
    cluster.add_argument("-j", "--jelastic",
                         default=JELHOST,
                         help="Jelastic Cluster DNS")
    return parser.parse_args()

args = argparser()

# logging = logging.getLogger(name=re.split('[@.]', args.sudo)[1])
logging = logging.getLogger(name='jahiacloudbackup')
logging.addHandler(journal.JournaldLogHandler(identifier=(args.env)))
logging.info("BACKUP START")

def importPackage(classname):
    try:
        resp = classname.devScriptEval(urlpackage=args.url,
                                       shortdomain=args.env,
                                       settings=json.loads(args.settings))
    except:
        logging.error("BACKUP END: An error was returning during package execution")
        if userSess:
            userSess.signOut()
        if adminSess:
            adminSess.signOut()
        quit(1)
    return resp


if args.token:
    adminSess = Jelastic(args.jelastic, token=args.token)
    adminSess.getSessionAttribute()
    print(adminSess.usersAccountGetUserInfo())
    adminSess.getSessionAttribute()
elif args.login and args.password:
    adminSess = Jelastic(args.jelastic, login=args.login,
                         password=args.password)
    adminSess.getSessionAttribute()
    adminSess.signIn()
    print(adminSess.usersAccountGetUserInfo())
    adminSess.getSessionAttribute()
else:
    print("you failed")
    quit(1)

if args.sudo:
    userToken = adminSess.sysAdminSignAsUser(args.sudo)
    userSess = Jelastic(args.jelastic, login=args.sudo,
                        session=userToken)
    resp = importPackage(userSess)
else:
    importPackage(adminSess)

if userSess:
    userSess.signOut()
if adminSess:
    adminSess.signOut()
r = json.loads(resp.text)
if r['response']['result'] == 0:
    logging.info("BACKUP END: the backup package return is ok")
else:
    logging.error("BACKUP END: An error was return by the backup package: {}".format(resp.text))
