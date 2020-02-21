# Backup Package Release notes

## actual version: v1.3

### v1.4 (2020-02-11)
* [NEW]: Do not try to backup stopped env
* [NEW]: Use Pypi official package *jahia-pylastic* instead of a local Pypi version

### v1.3

### v1.2 (2019-10-14)
* [FIX]: autodetecte database endpoint
    * since we can use proxsql and multi master mariadb, using old `sqldb` hostname was not working anymore
    * now the endpoint hostname is automaticaly setted
* [BUG]: fix foreign restoration
    * `backrest.py` didn't set `role` variables when launched with foreign option
        * `role` is now a third arg of `-F`
    * `restore.yml` is updated to send this new third arg when restore foreign backup
* [BUG]: fix _config_ files restoration
    * `/opt/tomcat/conf/digital-factory-config` was not restored because of bads paths in commands
* [NEW]: faster env restart after restoration
    * now get the max revision node in table JR_J_LOCAL_REVISIONS in order to create `/data/digital-factory-data/repository/revisionNode` file
    * `revisionNode.py` is responsible to create this file (wich is a 32bits binary file)
        * it can also read the binary file and return the decimal value with `-r` if needed
* [KNOW BUG]: we cannot, for now, accelerate processing launch after a restoration
    * when trying to set the `revisionNode` file, Jahia complain about rewriteURL/healthcluster
    * maybe a Jahia's bug
    * so *only browsing restart* do not need to reindexing all revision, *only processing need it*

### v1.1 (2019-07-25)
* [NEW]: new keys in metadata
    * `envname`
    * `displayname`
    * `cloudprovider` (for values `aws` or `azure`)
    * `region` (for cloudprovider region's name, eg: `eu-west-1`, `centralus`)
    * `envrole` (does the backup were from `dev` or `prod` Jelastic cluster)
    * `uid` (owner's uid of the backuped env)
* [NEW]: change in metadata files logic
    * now they are 2 buckets in eu-west-1: `jc(prod|dev)backupmetadata`
    * every Jelastic user will now use *one* file to store his backups metadata
        * now with one file, we get metadata for all user's backups accross all cloud providers and cloud's regions

### v1.0 (2019-07-16)
* [NEW][IMPROVEMENT]: functionnal `autobackup`
    * the node now get an integrated _Datadog_ agent
        * _API key_ have to be set as a setting when importing `auto_backup.yml` in order to be setted as a env var
        * a python script is now sending custom metrics to _Datadog_
            * for each env backup: env name, duration and status (_ok_, _in progress_, _error_)
        * agent will send logs from somes units (cron, `app.py`, backups, and some others) to _Datadog_
            * password are removed from the log before
    * `import_package_as_user.py` is now sending log through _systemd_ journal
    * `pylastic.py` can now use a _logger_ instance from `import_package_as_user.py` in order to send it's log through _systemd_ too
    * `/var/log/backup_*` files are now rotated, old files goes to `/var/log/backup` folder
        * if a backup is in progress, log file is not rotated
        * we can see if a log file have been rotated or not (because a backup is still in progress) in `/var/log/messages` with line tagged `backuplogrotate`
* [IMPROVEMENT]: now tag are set to _bucket_ and _storage account_ when created
    * tags `project:jahia_cloud_prod` or `project:jahia_cloud_dev` depending the cluster role

### v0.6 (2019-07-05)
* [NEW]: now it's possible to restore backup from another env, cloud provider, region, cluster env, another uid
    * for client day use:
        * if an user want to restore a env to another one, just select the source env with setting `source_env`
            * env source and target env can be in different cloud provider, region
    * for cloud masters:
        * for precise control of the source you want to be restored, do not user `source_env` settings but set all these:
            * `cloud_source`: (aws|azure)
            * `region_source`: eg: us-east-1, centralus, etc (set here the cloud region name, not the jelastic one)
            * `uid_source`: the UID of the backup's owner
            * `envrole_source`: (dev|prod) (the cluster from with the backup have been done)
* [IMPROVEMENT]: Add a `README.md` file for `autobackup`
    * contains basics informations about how to use it

### v0.5 (2019-07-04)
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
* [BUG]: `backrest.py` not properly handling Exceptions
    * replace some `if/else` statement by `try/except`, more relevant
* [BUG]: `backup.yml` and `listbackup.yml` doesn't set the correct region for AWS credentials file if AWS is not the cloud provider
    * now test if not AWS as cloud provider and then set AWS region to `eu-west-1` in `~/.aws/credentials` (the Secret Manager used for get Azure Token is there)
* [BUG]: `backup.yml` and `listbackup.yml` doesn't install need python modules for Azure
    * now install python3 modules `adal` and `azure`
* [CHANGE]: rename _Bucket_ and _Storage Account_ names
    * now that's `jc(prod|dev)${env.uid}${cloudregion}`
* [BUG]: `adal` is not installed
    * need to upgrade `pip` first whith command `python3 -m pip install --upgrade pip`

### v0.4 (2019-06-28)
* [BUG][IMPROVEMENT]: Azure Storage Account namming convention: only alphanum characters allowed (eg: no dash)
    * `backup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `listbackup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `restore.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `backrest.py`: now the Storage Account used/created taking his name from the `bucketname` argument instead of the `backupname`

