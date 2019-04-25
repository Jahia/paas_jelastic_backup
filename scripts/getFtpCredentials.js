//@auth

var baseUrl = "${baseUrl}";

var storage = use("backup/scripts/useStorageApi.js");

var userData = storage.getUserData();
var ftpHost = storage.getFtpHost();    
var ftpUser = userData.credentials.ftpUser;
var ftpPassword = userData.credentials.ftpPassword;
return {result: 0, ftpUser: ftpUser, ftpHost: ftpHost, ftpPassword: ftpPassword};

function use(script) {
    var Transport = com.hivext.api.core.utils.Transport,
        body = new Transport().get(baseUrl + "/" + script + "?_r=" + Math.random());
    var debug = baseUrl + "/" + script + "?_r=" + Math.random();    

    return new (new Function("return " + body)())(session);
}
