FROM jdeathe/centos-ssh

RUN yum -y install python36 python36-pip cronie glibc-common \
  && yum clean all \
  && mkdir /pylastic \
  && rm -rf /etc/ld.so.cache \
  && rm -rf /sbin/sln 

RUN pip3.6 install requests flask flask_restful python-crontab


COPY supervisord.conf /etc/supervisord.conf
COPY supervisord_crond.conf /etc/supervisord.d/crond.conf
COPY supervisord_flask.conf /etc/supervisord.d/flask.conf
COPY app.py /app.py
COPY pylastic/pylastic.py /pylastic/pylastic.py
COPY import_package_as_user.py /import_package_as_user.py

ENV FLASK_ENV="development" LANG="en_US.utf8" LC_ALL="en_US.utf8"

EXPOSE 8080/tcp
CMD ["/usr/bin/supervisord", "--configuration=/etc/supervisord.conf"]
