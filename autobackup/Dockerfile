FROM centos:centos7


RUN yum -y update \
  && yum -y install epel-release cronie glibc-common \
  && yum -y install python36 python36-pip python36-devel gcc systemd-devel \
  && yum clean all

RUN python3 -m pip install --upgrade pip \
  && python3 -m pip install requests flask flask_restful python-crontab cysystemd jahia-pylastic


COPY app.py /app.py
COPY import_package_as_user.py /import_package_as_user.py
COPY launch_api.service /etc/systemd/system/launch_api.service
COPY dd_setapikey.service /etc/systemd/system/dd_setapikey.service
COPY rsyslog_api.conf /etc/rsyslog.d/api.conf
COPY dd_global.yaml /tmp/dd_global.yaml

RUN systemctl enable launch_api.service \
  && sed 's/^\(CRONDARGS=\)/\1"-s"/' -i /etc/sysconfig/crond

RUN DD_INSTALL_ONLY=true DD_API_KEY=FALSE_KEY bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/datadog-agent/master/cmd/agent/install_script.sh)" \
  && echo "sed unit file" \
  && sed 's/^\(User=\).*$/\1root/' -i /usr/lib/systemd/system/datadog-agent.service \
  && echo "add log conf to dd agent" \
  && cat /tmp/dd_global.yaml >> /etc/datadog-agent/datadog.yaml \
  && echo "create folder" \
  && mkdir /etc/datadog-agent/conf.d/journald.d \
  && systemctl enable dd_setapikey

COPY dd_backup.yaml /etc/datadog-agent/conf.d/backup.yaml
COPY dd_backup.py /etc/datadog-agent/checks.d/backup.py
COPY dd_journald.yaml /etc/datadog-agent/conf.d/journald.d/conf.yaml
COPY logrotate_backup /etc/logrotate.d/backup


EXPOSE 8080/tcp
CMD /usr/sbin/init
