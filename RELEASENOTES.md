# Backup Package Release notes

## actual version: v0.5

### v0.5 (2019-07-02)
* [NEW]: autobackup in the `autobackup` folder
    * `auto_backup.yml`: package for create the _auto backup environement_ in Jelastic
    * `auto_backup_control.yml`: package for add/remove/list backup cron in previous env
    * `Dockerfile`: build the docker image use for the so previous env, image using:
        * `app.py`: flask restful API for interact with crontab
        * `import_package_as_user.py`: execute a package (url) in a Jelastic user context (used here for import the `update.yml`)
* [IMPROVEMENT]: `backup.yml` now can auto generate timestamp if not sent
* [BUG]: `max_allowed_packet` size problem with mysql
    * in `backup.yml` and `restore.yml`, now specify `--max_allowed_packet=1024M` when calling `mysqldump` and `mysql` client
* [BUG]: `backrest.py` was not compatible with old env not created with `_PROVIDE` environement variable
    * now when metadata is generated, the key `dx_product` will be `dx` if env var `DX_VERSION` is found on the server
    * if, hypothetically, no `DX_VERSION` was found too, to both corresponding keys in metadata file will be the value `undefined`
* [BUG]: Due to a AWS's API bug, we must not specify the `LocationConstraint` when the region is `us-east-1` and you want to create a bucket
    * see https://github.com/boto/boto3/issues/125 for more detail
    * now `backrest.py` is aware of that
* [BUG]: Local git repo not well update when moving tag to another commit
    * always `git clone` from scratch by `rm` the local repo if already there

### v0.4 (2019-06-28)
* [BUG][IMPROVEMENT]: Azure Storage Account namming convention: only alphanum characters allowed (eg: no dash)
    * `backup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `listbackup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `restore.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `backrest.py`: now the Storage Account used/created taking his name from the `bucketname` argument instead of the `backupname`

