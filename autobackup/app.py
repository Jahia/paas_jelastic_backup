#!/usr/bin/env python3

import logging
import re
from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from crontab import CronTab


app = Flask(__name__)
api = Api(app)


LOG_FORMAT = "%(levelname)s: [%(funcName)s] %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


script = "source /.jelenv && export $(grep MASTER_PWD /.jelenv) && cd / && python3 /import_package_as_user.py -l \"{login}\" -p \"{password}\" -u '{url}' --settings \"{settings}\" --env {env} -s \"{sudo}\" >> /var/log/backup_{sudo}-{env}.log 2>&1"

@app.route("/")
def hello():
    return "Hello World!"


class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world', 'hehe': 'hoho'}

class ListCronJobs(Resource):
    def get(self):
        resp = {}
        crontab = CronTab(user=True)
        for job in crontab:
            comment = job.comment.split(" ")
            uid = comment[0]
            shortdomain = comment[1]
            infos = {'command': job.command,
                     'minute': job.minute.render(),
                     'hour': job.hour.render(),
                     'monthday': job.day.render(),
                     'month': job.month.render(),
                     'weekday': job.dow.render(),
                     'shortDomain': shortdomain}
            if uid not in resp:
                resp[uid] = []
            resp[uid].append(infos)
        return resp

class CronJob(Resource):
    def post(self):
        args = parser.parse_args()
        if not args.command:
            command = script.format(login='${MASTER_LOGIN}',
                                    password='${MASTER_PWD}',
                                    url=args.url,
                                    settings= args.settings.replace("'", '\\"'),
                                    env=args.envname,
                                    sudo=args.sudo)
        else:
            command = args.command
        crontab = CronTab(user=True)
        newjob = crontab.new(command=command,
                             comment='{} {}'.format(args.uid, args.envname))
        newjob.setall(args.schedule)
        logging.info('render: {}'.format(newjob.render()))
        jobs = []
        for j in crontab:
            jobs.append(j.render())
        try:
            crontab.write()
            result = 0
        except:
            result = 1
        return {'result': result}

    def delete(self):
        args = parser.parse_args()
        crontab = CronTab(user=True)
        # job = crontab.find_command(args.command)
        job = crontab.find_comment(re.compile(r' {}$'.format(args.envname)))
        crontab.remove(job)
        try:
            crontab.write()
            result = 0
        except:
            result = 1
        return {'result': result}


parser = reqparse.RequestParser()
parser.add_argument('command')
parser.add_argument('comment')
parser.add_argument('envname')
parser.add_argument('login')
parser.add_argument('password')
parser.add_argument('schedule')
parser.add_argument('settings')
parser.add_argument('sudo')
parser.add_argument('uid')
parser.add_argument('url')

api.add_resource(HelloWorld, '/api/hello')
api.add_resource(ListCronJobs, '/api/listcronjobs')
api.add_resource(CronJob, '/api/cronjob')
