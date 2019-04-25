function BackupManager(config) {
    /**
     * Implements backup management of the Jahia environment
     * @param {{
     *  session : {String}
     *  baseUrl : {String}
     *  uid : {Number}
     *  cronTime : {String}
     *  scriptName : {String}
     *  envName : {String}
     *  envAppid : {String}
     *  maintenanceHost : {String}
     *  elasticSearchHost : {String}
     *  ftpHost : {String}
     *  [ftpUser] : {String}
     *  [ftpPassword] : {String}
     *  [backupCount] : {String}
     * }} config
     * @constructor
     */

    var Response = com.hivext.api.Response,
        EnvironmentResponse = com.hivext.api.environment.response.EnvironmentResponse,
        ScriptEvalResponse = com.hivext.api.development.response.ScriptEvalResponse,
        Transport = com.hivext.api.core.utils.Transport,
        Random = com.hivext.api.utils.Random,
        SimpleDateFormat = java.text.SimpleDateFormat,
        StrSubstitutor = org.apache.commons.lang3.text.StrSubstitutor,
        Scripting = com.hivext.api.development.Scripting,

        me = this,
        nodeManager,
        session;

    config = config || {};
    session = config.session;
    nodeManager = new NodeManager(config.envName);

    me.invoke = function (action) {
        var actions = {
            "install"         : me.install,
            "uninstall"       : me.uninstall,
            "backup"          : me.backup,
            "get-credentials" : me.getCredentials
        };

        if (!actions[action]) {
            return {
                result : Response.ERROR_UNKNOWN,
                error : "unknown action [" + action + "]"
            }
        }

        return actions[action].call(me);
    };

    me.install = function () {
        var resp;

        if (!config.ftpUser) {
            resp = me.exec(me.initFtpCredentials);
            if (resp.result !== 0) return resp;
        }

        return me.exec([
            [ me.createScript   ],
            [ me.clearScheduledBackups ],
            [ me.scheduleBackup ]
        ]);
    };

    me.uninstall = function () {
        return me.exec(me.clearScheduledBackups);
    };

    me.backup = function () {
        var backupDir = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss").format(new Date()),
            lftp = new Lftp(config.ftpHost, config.ftpUser, config.ftpPassword),
            isManual = !getParam("task");

        if (isManual) {
            backupDir += "-manual";
        }

        return me.exec([
            [ me.checkEnvStatus ],
            [ me.cmd, [
                lftp.cmd([
                    "mkdir %(envName)",
                    "mkdir %(envName)/%(backupDir)"
                ]),
                'tar -zcf data.tar.gz /data',
                'mysqldump --user=${DB_USER} --password=${DB_PASSWORD} -h mysqldb --single-transaction --quote-names --opt --databases --compress jahia > jahia.sql',
                lftp.cmd([
                    "cd %(envName)/%(backupDir)",
                    "put data.tar.gz",
                    "put jahia.sql"
                ])
            ], {
                nodeGroup : "proc",
                envName : config.envName,
                maintenanceUrl : _("http://%(host)/modules/tools/maintenance.jsp?fullReadOnlyMode", { host : config.maintenanceHost }),
                backupDir : backupDir
            }]

            // [ me.cmd, [
            //     "CT='Content-Type:application/json'",
            //     "curl -H $CT -X PUT -d '{\"type\":\"fs\",\"settings\":{\"location\":\"all\"}}' '%(elasticSearchUrl)'",
            //     "curl -H $CT -X DELETE '%(elasticSearchUrl)/snapshot'",
            //     "curl -H $CT -X PUT '%(elasticSearchUrl)/snapshot?wait_for_completion=true'",
            //     "tar -zcf es.tar.gz /var/lib/elasticsearch/backup/*",

            //     lftp.cmd([
            //         "cd %(envName)/%(backupDir)",
            //         "put es.tar.gz"
            //     ]),
            //     'number_of_backups=$(' + lftp.cmd("ls %(envName)/") + '| wc -l)',
            //     '[ "${number_of_backups}" -gt "%(backupCount)" ] && { let "number_for_deletion = ${number_of_backups} - %(backupCount)"; backups_for_deletion=$(' + lftp.cmd("ls %(envName)") + ' | awk \'{print $9}\'|head -$number_for_deletion ); } || true',
            //     '[ -n "$backups_for_deletion" ] && { for i in $backups_for_deletion; do ' + lftp.cmd([ "cd %(envName)/", "rm -r $i" ]) + '; done ; } || true;'
            // ], {
            //     nodeGroup: "es",
            //     envName : config.envName,
            //     elasticSearchUrl : _("http://%(host):9200/_snapshot/all", { host : config.elasticSearchHost }),
            //     backupCount : config.backupCount,
            //     backupDir : backupDir
            // }]
        ]);
    };

    me.checkEnvStatus = function checkEnvStatus() {
        if (!nodeManager.isEnvRunning()) {
            return {
                result : EnvironmentResponse.ENVIRONMENT_NOT_RUNNING,
                error : _("env [%(name)] not running", {name : config.envName})
            };
        }

        return { result : 0 };
    };

    me.getCredentials = function () {
        return {
            result : 0,
            ftpUser : config.ftpUser,
            ftpPassword : config.ftpPassword
        };
    };

    me.initFtpCredentials = function initFtpCredentials() {
        var resp = new StorageApi(session).initFtpCredentials();
        var credentials = resp.credentials || {};

        config.ftpUser = credentials.ftpUser;
        config.ftpPassword = credentials.ftpPassword;

        return resp;
    };

    me.createScript = function createScript() {
        var url = me.getScriptUrl("backup-main.js"),
            scriptName = config.scriptName,
            scriptBody,
            resp;

        try {
            scriptBody = new Transport().get(url);

            scriptBody = me.replaceText(scriptBody, config);

            //delete the script if it already exists
            jelastic.dev.scripting.DeleteScript(scriptName);

            //create a new script
            resp = jelastic.dev.scripting.CreateScript(scriptName, "js", scriptBody);

            java.lang.Thread.sleep(1000);

            //build script to avoid caching
            jelastic.dev.scripting.Build(scriptName);
        } catch (ex) {
            resp = { result : Response.ERROR_UNKNOWN, error: toJSON(ex) };
        }

        return resp;
    };


    me.scheduleBackup = function scheduleBackup() {
        var quartz = new CronToQuartzConverter().convert(config.cronTime);

        for (var i = quartz.length; i--;) {
            var resp = jelastic.utils.scheduler.CreateEnvTask({
                appid: appid,
                envName: config.envName,
                session: session,
                script: config.scriptName,
                trigger: "cron:" + quartz[i],
                params: { task: 1, action : "backup" }
            });

            if (resp.result !== 0) return resp;
        }

        return { result: 0 };
    };

    me.clearScheduledBackups = function clearScheduledBackups() {
        var envAppid = config.envAppid,
            resp = jelastic.utils.scheduler.GetTasks(envAppid, session);

        if (resp.result != 0) return resp;

        var tasks = resp.objects;

        for (var i = tasks.length; i--;) {
            if (tasks[i].script == config.scriptName) {
                resp = jelastic.utils.scheduler.RemoveTask(envAppid, session, tasks[i].id);

                if (resp.result != 0) return resp;
            }
        }

        return resp;
    };

    me.getFileUrl = function (filePath) {
        return config.baseUrl + "/backup/" + filePath + "?_r=" + Math.random();
    };

    me.getScriptUrl = function (scriptName) {
        return me.getFileUrl("scripts/" + scriptName);
    };

    me.cmd = function cmd(commands, values, sep) {
        return nodeManager.cmd(commands, values, sep, true);
    };

    me.replaceText = function (text, values) {
        return new StrSubstitutor(values, "${", "}").replace(text);
    };

    me.exec = function (methods, oScope, bBreakOnError) {
        var scope,
            resp,
            fn;

        if (!methods.push) {
            methods = [ Array.prototype.slice.call(arguments) ];
            onFail = null;
            bBreakOnError = true;
        }

        for (var i = 0, n = methods.length; i < n; i++) {
            if (!methods[i].push) {
                methods[i] = [ methods[i] ];
            }

            fn = methods[i][0];
            methods[i].shift();

            log(fn.name + (methods[i].length > 0 ?  ": " + methods[i] : ""));
            scope = oScope || (methods[methods.length - 1] || {}).scope || this;
            resp = fn.apply(scope, methods[i]);

            log(fn.name + ".response: " + resp);

            if (resp.result != 0) {
                resp.method = fn.name;
                resp.type = "error";

                if (resp.error) {
                    resp.message = resp.error;
                }

                if (bBreakOnError !== false) break;
            }
        }

        return resp;
    };

    function NodeManager(envName, nodeId, baseDir, logPath) {
        var ENV_STATUS_TYPE_RUNNING = 1,
            me = this,
            envInfo;

        me.isEnvRunning = function () {
            var resp = me.getEnvInfo();

            if (resp.result != 0) {
                throw new Error("can't get environment info: " + toJSON(resp));
            }

            return resp.env.status == ENV_STATUS_TYPE_RUNNING;
        };

        me.getEnvInfo = function () {
            var resp;

            if (!envInfo) {
                resp = jelastic.env.control.GetEnvInfo(envName, session);
                if (resp.result != 0) return resp;

                envInfo = resp;
            }

            return envInfo;
        };

        me.cmd = function (cmd, values, sep, disableLogging) {
            var resp,
                command;

            values = values || {};
            values.log = values.log || logPath;
            cmd = cmd.join ? cmd.join(sep || " && ") : cmd;

            command = _(cmd, values);

            if (!disableLogging) {
                log("cmd: " + command);
            }

            if (values.nodeGroup) {
                resp = jelastic.env.control.ExecCmdByGroup(envName, session, values.nodeGroup, toJSON([{ command: command }]), true, false, "root");
            } else {
                resp = jelastic.env.control.ExecCmdById(envName, session, nodeId, toJSON([{ command: command }]), true, "root");
            }

            return resp;
        };
    }

    function Lftp (ftpHost, user, password) {
        this.cmd = function (command) {
            return _('/usr/bin/lftp -u %(user),%(password) -e "set ssl:verify-certificate no; set ftp:ssl-force true; %(cmd); quit" %(ftpHost)', {
                ftpHost : ftpHost,
                user : user,
                password : password,
                cmd : command.join ? command.join(";") : command
            });
        };
    }

    /**
     * @param session
     * @param [storageAppid]
     * @param [ftpHost]
     * @constructor
     */
    function StorageApi(session, storageAppid, ftpHost) {
        var SOURCE = "remote-storage";

        this.getUserData = function getUserData() {
            return this.eval("GetUserData");
        };

        this.getEnvs = function getEnvs() {
            return this.eval("GetEnvs");
        };

        this.getBackups = function getBackups(envName) {
            return this.eval("GetBackups", {
                envName: envName
            });
        };

        this.initFtpCredentials = function initFtpCredentials() {
            return this.eval("InitFtpCredentials");
        };

        this.getStorageAppid = function () {
            return storageAppid;
        };

        this.getFtpHost = function getFtpHost() {
            return ftpHost;
        };

        this.eval = function (method, params) {
            var resp = jelastic.development.scripting.Eval(appid + "/" + storageAppid, session, method, params || {});
            resp = resp.response || resp;

            if (resp.result !== 0) {
                resp.method = method;
                resp.source = SOURCE;
            }

            return resp;
        };

        this.initSettings = function () {
            var resp = jelastic.development.scripting.Eval(appid + "/settings", session, "GetSettings", {
                settings : "JAHIA_STORAGE_APPID,JAHIA_STORAGE_FTP_HOST"
            });

            resp = resp.response || resp;

            if (resp.result !== 0) {
                throw new Error("Cannot get settings [JAHIA_STORAGE_APPID, JAHIA_STORAGE_FTP_HOST]: " + toJSON(resp));
            }

            if (!storageAppid) {
                storageAppid = resp.settings.JAHIA_STORAGE_APPID;

                if (!storageAppid) {
                    throw new Error("JAHIA_STORAGE_APPID setting not found");
                }
            }

            if (!ftpHost) {
                ftpHost = resp.settings.JAHIA_STORAGE_FTP_HOST;

                if (!ftpHost) {
                    throw new Error("JAHIA_STORAGE_FTP_HOST setting not found");
                }
            }
        };

        this.initSettings();
    }

    function CronToQuartzConverter() {
        this.getQuartz = function (cron) {
            var data = [];
            var quartzEntry;

            // check for cron magic entries
            quartzEntry = parseCronMagics(cron);

            if (quartzEntry) {
                data.push(quartzEntry);
            } else {

                // if cron magic entries not found, proceed to parsing normal cron format
                var crontabEntry = cron.split(' ');
                quartzEntry = parseCronSyntax(crontabEntry);

                data.push(quartzEntry);

                if (crontabEntry[2] !== '*' && crontabEntry[4] !== '*') {

                    crontabEntry[2] = '*';

                    quartzEntry = parseCronSyntax(crontabEntry);
                    data.push(quartzEntry);
                }

            }

            return data;
        };

        this.convert = function (cron) {
            var arr = this.getQuartz(cron);

            for (var i = 0, l = arr.length; i < l; i++) {
                arr[i] = arr[i].join(' ');
            }

            return arr;
        };

        function advanceNumber(str) {

            var quartzCompatibleStr = '';
            var num;
            str.split('').forEach(function (chr) {

                num = parseInt(chr);

                // char is an actual number
                if (!isNaN(num)) {
                    // number is in allowed range
                    if (num >= 0 && num <= 7) {
                        quartzCompatibleStr += num + 1;
                    } else {
                        // otherwise default to 1, beginning of the week
                        quartzCompatibleStr = 1;
                    }
                } else {
                    quartzCompatibleStr += chr;
                }



            });

            return quartzCompatibleStr;
        }

        function parseCronSyntax(crontabEntry) {

            var quartzEntry = [];

            // first we initialize the seconds to 0 by default because linux CRON entries do not include a seconds definition
            quartzEntry.push('0');

            // quartz scheduler can't handle an OR definition, and so it doesn't support both DOM and DOW fields to be defined
            // for this reason we need to shift one of them to be the value or * and the other to be ?
            var toggleQuartzCompat = false;

            crontabEntry.forEach(function (item, index, array) {


                // index 0 = minutes
                // index 1 = hours
                // these cron definitions should be compatible with quartz so we push them as is
                if (index === 0 || index === 1) {
                    quartzEntry.push(item);
                }

                // index 2 = DOM = Day of Month
                if (index === 2) {
                    if (item !== '?') {
                        toggleQuartzCompat = true;
                    }

                    if (item === '*') {
                        toggleQuartzCompat = false;
                        item = '?';
                    }

                    quartzEntry.push(item);
                }

                // index 3 = Month
                if (index === 3) {
                    quartzEntry.push(item);
                }

                // index 4 = DOW = Day of Week
                if (index === 4) {

                    // day of week needs another adjustments - it is specified as 1-7 in quartz but 0-6 in crontab
                    var itemAbbreviated = advanceNumber(item);

                    if (toggleQuartzCompat === true) {
                        quartzEntry.push('?');
                    } else {
                        quartzEntry.push(itemAbbreviated);
                    }
                }

                if (index >= 5) {
                    return true;
                }

            });

            quartzEntry.push('*');

            return quartzEntry;

        }

        function parseCronMagics(crontab) {

            var quartzEntry = false;

            // @hourly
            if (crontab.indexOf('@hourly') === 0) {
                quartzEntry = ['0', '0', '*', '*', '*', '?', '*'];
            }

            // @daily and @midnight
            if (crontab.indexOf('@daily') === 0 || crontab.indexOf('@midnight') === 0) {
                quartzEntry = ['0', '0', '0', '*', '*', '?', '*'];
            }

            // @weekly
            if (crontab.indexOf('@weekly') === 0) {
                quartzEntry = ['0', '0', '0', '?', '*', '1', '*'];
            }

            // @monthly
            if (crontab.indexOf('@monthly') === 0) {
                quartzEntry = ['0', '0', '0', '1', '*', '?', '*'];
            }

            // @yearly and @annually
            if (crontab.indexOf('@yearly') === 0 || crontab.indexOf('@annually') === 0) {
                quartzEntry = ['0', '0', '0', '1', '1', '?', '*'];
            }

            return quartzEntry || false;
        }
    }

    function log(message) {
        return jelastic.marketplace.console.WriteLog(appid, session, message);
    }

    function _(str, values) {
        return new StrSubstitutor(values || {}, "%(", ")").replace(str);
    }
}