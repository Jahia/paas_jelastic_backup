#!/bin/bash

USER=$1

ENV_LIST=$(ls -Qm /backups/${USER})

OUTPUT_JSON="{\"result\": 0, \"envs\": [${ENV_LIST}], \"backups\": {"

if [ -n "$ENV_LIST" ]; then

    for i in $(ls /backups/${USER})
    do
        DIRECTORY_LIST=$(ls -Qm /backups/${USER}/${i})
        OUTPUT_JSON="${OUTPUT_JSON}\"${i}\":[${DIRECTORY_LIST}],"
    done

    OUTPUT_JSON=${OUTPUT_JSON::-1}
fi

echo $OUTPUT_JSON}}
