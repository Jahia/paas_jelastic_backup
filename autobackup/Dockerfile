FROM centos:centos7
ARG DD_API_KEY


RUN yum -y update \
  && yum -y install epel-release cronie glibc-common \
  && yum -y install python36 python36-pip \
  && yum clean all \
  && mkdir /pylastic 

RUN python3 -m pip install --upgrade pip \
  && python3 -m pip install requests flask flask_restful python-crontab


COPY app.py /app.py
COPY pylastic/pylastic.py /pylastic/pylastic.py
COPY import_package_as_user.py /import_package_as_user.py
COPY launch_api.service /etc/systemd/system/launch_api.service
COPY rsyslog_api.conf /etc/rsyslog.d/api.conf

RUN systemctl enable launch_api.service \
  && sed 's/^\(CRONDARGS=\)/\1"-s"/' -i /etc/sysconfig/crond

RUN DD_INSTALL_ONLY=true DD_API_KEY=$DD_API_KEY bash -c "$(curl -L https://raw.githubusercontent.com/DataDog/datadog-agent/master/cmd/agent/install_script.sh)" \
  && cp /usr/lib/systemd/system/datadog-agent.service /etc/systemd/system/datadog-agent.service \
  && sed 's/^\(User=\).*$/\1root/' \
  && systemctl enable datadog-agent

COPY dd_backup.yaml /etc/datadog-agent/conf.d/backup.yaml


EXPOSE 8080/tcp
CMD /usr/sbin/init
