import os
import re
import json
from time import time

# the following try/except block will make the custom check compatible with any Agent version
try:
    # first, try to import the base class from old versions of the Agent...
    from checks import AgentCheck
except ImportError:
    # ...if the above failed, the check is running in Agent version 6 or later
    from datadog_checks.checks import AgentCheck

# content of the special variable __version__ will be shown in the Agent status page
__version__ = "1.0.0"


# class HelloCheck(AgentCheck):
#     def check(self, instance):
#         self.gauge('hello.world', 1, tags=['TAG_KEY:TAG_VALUE'])


launchtime = int(str(time()).split('.')[0])

class CheckBackup(AgentCheck):
    def check(self, instance):
        l = os.listdir('/var/log')
        lb = [l[i] for i in range(len(l)) if l[i].startswith('backup_')]
        # self.gauge('backup.number', len(lb))
        nb_cron = sum(1 for line in open('/var/spool/cron/root') if line.strip())
        self.gauge("backup.job", nb_cron)

        cpat = re.compile('.+BACKUP START[\w\W]+?(BACKUP END:.+$|(?=BACKUP START))')
        spat = '.+BACKUP START[\w\W]+?(BACKUP END:.+$|(?=BACKUP START))'
        successpat = 'the backup package return is ok'

        # pass

        for f in lb:
            filemtime = int(str(os.stat('/var/log/' + f).st_mtime).split('.')[0])

            # f like backup_user@domain_envname.log
            f1=re.sub("(^backup_|\.log$)", "", f)
            envCustomer=re.sub(r"(^.+@.+\..[a-z]+)-.+$", r"\1", f1, re.IGNORECASE)
            envName=re.sub(r"(^.+@.+\..[a-z]+)-(.+$)", r"\2", f1, re.IGNORECASE)
            tags = ['customer:' + envCustomer,
                    'envname:' + envName,
                    'service:' + envName]

            # 15s is the defaut interval between check
            if launchtime - filemtime > 60:
                # self.service_check('backup.status', AgentCheck.UNKNOWN,
                #                    message="no recent log",
                #                    tags=tags)
                continue

            with open('/var/log/' + f, 'r') as curfile:
                log = curfile.read()

            #bl = re.findall(spat, log, re.MULTILINE)
            bl = re.split('BACKUP START', log)
            last = bl[len(bl)-1]

            if re.search(successpat, last):
                self.service_check('backup.status', AgentCheck.OK,
                                   tags=tags)

                try:
                    # to be in seconds
                    d = json.loads(last.splitlines()[-1])['debug']['time'] / 1000
                    self.gauge('backup.duration',
                               str(d), tags=tags)

                except:
                    self.gauge('backup.duration',
                               0, tags=tags)

            else:
                if re.search('\Werror\W', last, re.IGNORECASE):
                    self.service_check('backup.status', AgentCheck.CRITICAL,
                                        message="Backup Problem",
                                        tags=tags)
                else:
                    self.service_check('backup.status', AgentCheck.WARNING,
                                        message="Backup in progress",
                                        tags=tags)

                try:
                    # to be in seconds
                    d = json.loads(last.splitlines()[-1])['debug']['time'] / 1000
                    self.gauge('backup.duration',
                               str(d), tags=tags)
                except:
                    self.gauge('backup.duration',
                               0, tags=tags)
