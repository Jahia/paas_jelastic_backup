//@auth

var baseUrl = "https://raw.githubusercontent.com/Jahia/jelastic-package-dev/master/dx7302/backup";

var storage = use("scripts/useStorageApi.js");
var userData = storage.getUserData();
var envs = prepareEnvs(userData.envs);
var backups = prepareBackups(userData.backups);

jelastic.local.returnResult({
    result: 0,
    settings: {
        fields: [{
            "caption": "Restore from",
            "type": "list",
            "name": "envName",
            "required": true,
            "default": (envs[0] || {}).value || "",
            "values": envs
        }, {
            "caption": "Backup",
            "type": "list",
            "name": "backupDir",
            "required": true,
            "dependsOn": {
                "envName" : backups
            }
        }, {
            "type" : "spacer"
        }, {
            "caption": "Restore to",
            "type": "envname",
            "name": "newEnvName",
            "required" : true,
            "dependsOn": "targetRegion"
        }, {
            "caption": "Target region",
            "type": "string",
            "name": "targetRegion",
            "default": "jelastic_default_hw_group"
        }, {
            "caption": "Root Password",
            "type": "string",
            "name": "rootPwd",
        }, {
            "caption": "Tools password",
            "type": "string",
            "name": "toolsPwd",
        }]
    }
});

function use(script) {
    var Transport = com.hivext.api.core.utils.Transport,
        body = new Transport().get(baseUrl + "/" + script + "?_r=" + Math.random());
    var debug = baseUrl + "/" + script + "?_r=" + Math.random();    

    return new (new Function("return " + body)())(session);
}

function prepareEnvs(values) {
    var aResultValues = [];

    values = values || [];

    for (var i = 0, n = values.length; i < n; i++) {
        aResultValues.push({ caption: values[i], value: values[i] });
    }

    return aResultValues;
}

function prepareBackups(backups) {
    var oResultBackups = {};
    var aValues;

    for (var envName in backups) {
        if (Object.prototype.hasOwnProperty.call(backups, envName)) {
            aValues = [];

            for (var i = 0, n = backups[envName].length; i < n; i++) {
                aValues.push({ caption: backups[envName][i], value: backups[envName][i] });
            }

            oResultBackups[envName] = aValues;
        }
    }

    return oResultBackups;
}
