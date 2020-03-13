# Scheduled Backup

This is to create a _Jelastic_ environment that will can handle scheduled environment backup througt an API and a crontab.

## Docker Image
[jahia/paas_autobackup](https://hub.docker.com/repository/docker/jahia/paas_autobackup)

## Create Env
Only *one* _scheduled backup env_ is needed by _Jelastic_ cluster.

Use the `auto_backup.yml` package to create it.

Use the package's settings to set login and password that will be used to connected to _Jelastic_.

## Using the env's API through a package
The package `auto_backup_control.yml` can be use to interact with the API.


### Add a new scheduled backup

Setting name | comment
-------------|-----------------------------------------------------------------------------
action       | `add`
schedule     | _cron_ schedule style<br>eg: `* */8 * * *`
envname      | the _envName_ you want to get scheduled backup<br>eg: `mysuperenv`
region       | the _Jelastic_'s region where the targeted env is<br>eg: `default_hn_region`
sudo         | the targeted env's owner mail<br>eg: `iamanuser@mydomain.com`
uid          | the targeted env's owner UID<br>eg: `21135`
backupname   | how to call this scheduled backup<br>eg: `myregularautobackup`
retention    | how many backups do we keep<br>eg: `15`


### Del a scheduled backup

Setting name | comment
-------------|-----------------------------------------------------------------------------
action       | `del`
envname      | for which _envName_ do you want to remove backup<br>eg: `mysuperenv`


### List scheduled backup

Setting name | comment
-------------|-----------------------------------------------------------------------------
action       | `list`
