# Unomi Package Release notes

## actual version: v0.4

### v0.4 (2019-06-28)
* [BUG][IMPROVEMENT]: Azure Storage Account namming convention: only alphanum characters allowed (eg: no dash)
    * `backup.yml` : `bucketname` argument sending to `backrest.py` is now in the form `jahiacloud${env.uid}`
    * `backrest.py`: now the Storage Account used/created taking his name from the `bucketname` argument instead of the `backupname`

