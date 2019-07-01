# Backup Package Release notes

## actual version: v0.5

### v0.5 (2019-07-01)
* [NEW]: autobackup in the `autobackup` folder
    * `auto_backup.yml`: package for create the _auto backup environement_ in Jelastic
    * `auto_backup_control.yml`: package for add/remove/list backup cron in previous env
    * `Dockerfile`: build the docker image use for the so previous env, image using:
        * `app.py`: flask restful API for interact with crontab
        * `import_package_as_user.py`: execute a package (url) in a Jelastic user context (used here for import the `update.yml`)
* [IMPROVEMENT]: `backup.yml` now can auto generate timestamp if not sent
* [BUG]: `max_allowed_packet` size problem with mysql
    * in `backup.yml` and `restore.yml`, now specify `--max_allowed_packet=1024M` when calling `mysqldump` and `mysql` client

### v0.4 (2019-06-28)
* [BUG][IMPROVEMENT]: Azure Storage Account namming convention: only alphanum characters allowed (eg: no dash)
    * `backup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `listbackup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `restore.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `backrest.py`: now the Storage Account used/created taking his name from the `bucketname` argument instead of the `backupname`

