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
            settings: "JAHIA_STORAGE_APPID,JAHIA_STORAGE_FTP_HOST"
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
