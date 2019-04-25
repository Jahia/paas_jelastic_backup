import org.apache.commons.lang3.text.StrSubstitutor;

StrSubstitutor = org.apache.commons.lang3.text.StrSubstitutor;
Transport = com.hivext.api.core.utils.Transport

var config = {};
config.storageEnvName = '${env.envName}';

function replaceText(text, values) {
    return new StrSubstitutor(values, "${", "}").replace(text);
};

function createScript(scriptName) {
    var url = "https://raw.githubusercontent.com/Jahia/jelastic-package-dev/master/dx7302/backup/scripts/storage/" + scriptName;

    try {
        scriptBody = new Transport().get(url);

        scriptBody = replaceText(scriptBody, config);

        jelastic.dev.scripting.DeleteScript(scriptName);

        resp = jelastic.dev.scripting.CreateScript(scriptName, "js", scriptBody);

        java.lang.Thread.sleep(1000);

        jelastic.dev.scripting.Build(scriptName);
    } catch (ex) {
        resp = {
            error: toJSON(ex)
        };
    }

    return resp;
};

var db = jelastic.data.base;
var tableName = "ftpJahiaUserCredentials";
var typeExists = db.GetType(tableName);

if (typeExists.result != 0) {
    db.DefineType(appid, signature, tableName, {
        uid: 'int',
        ftpUser: 'string',
        ftpPassword: 'string'
    }, "uid");
}

var scriptsToInstall = ["GetBackups", "GetEnvs", "GetUserData", "InitFtpCredentials", "lib/JahiaStorage"], script;
for (var i=0; i < scriptsToInstall.length; i++) {
    createScript(scriptsToInstall[i]);
}

return {result: 0}
