#!/usr/bin/env python

import requests
import json
import urllib
import logging

requests.packages.urllib3.disable_warnings()

# try:
#     logging = logging.getLogger('jahiacloudbackup')
# except:
#     pass

class Jelastic():
    """Instanciate a connexion to Jelastic through is API
       :param hostname: the endpoint to you Jelastic cluster
       :param login: the login of your user
       :param password: the user's password
       :type hostname: string
       :type login: string
       :type password: string

       :Example:
           >>> jel = Jelastic("my.jelastic.com",
                              "myuser",
                              "mypass")
           >>> jel.signIn
    """
    def __init__(self, hostname=None,
                 login=None, password=None,
                 session=None, token=None):
        self.hostname = "https://" + hostname
        self.login = login
        self.password = password
        self.session = session
        if token and not session:
            self.token = token
            self.session = token
        else:
            self.token = token
        self.uid = None

        self.s = requests.Session()
        self.s.headers = {'User-Agent': 'pylastic/0.1'}
        self.s.verify = False

        try:
            self.logging = logging.getLogger('jahiacloudbackup')
        except:
            self.logging = logging

        self.logging.info("A new Jelastic object is instancied.")

    def signIn(self):
        """Signin to the Jelastic API"""
        url = self.hostname + "/1.0/users/authentication/rest/signin"
        resp = self.s.post(url, data={'login': self.login,
                                        'password': self.password})
        self.logging.info("login: {}".format(self.login))
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot authenticate. Code: {}"
                          .format(str(resp.text)))
            return resp
        else:
            self.logging.info("Authentication successful.")
            self.session = json.loads(resp.text)['session']
            self.usersAccountGetUserInfo()
            return self.session
    def signOut(self):
        """Sign out to the Jelastic API"""
        url = self.hostname + "/1.0/users/authentication/rest/signout"
        resp = self.s.post(url, data={'session': self.session})
        self.logging.info("logout: {}".format(self.login))
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot sign out. Code: {}"
                          .format(str(resp.text)))
            return resp
        else:
            self.logging.info("Sign out successful.")
            return True
    def getSessionAttribute(self):
        self.logging.info("\n\thostname({})\n\tlogin({})\n\tpassword({})\n\tsession({})\n\ttoken({})\n\tuid({})"
                     .format(self.hostname,
                             self.login,
                             self.password,
                             self.session,
                             self.token,
                             self.uid))

    # Development Scripting
    def devScriptEval(self, urlpackage=None, shortdomain=None,
                      region=None, settings=None):
        url = self.hostname + "/1.0/development/scripting/rest/eval"
        payload={'session': self.session,
                 'appid': 'appstore',
                 'script': 'InstallApp',
                 'manifest': urlpackage,
                 'settings': json.dumps(settings)
                 }
        package = requests.get(urlpackage)
        if region:
            self.logging.info("You specified {} region".format(region))
            payload['region'] = region
        if package.text.find('type: update') >= 0:
            self.logging.info("{} is an update package".format(urlpackage))
            envinfo = self.envControlGetEnvInfo(shortdomain)
            payload['targetAppid'] = envinfo['env']['appid']
        else:
            self.logging.info("{} is an install package".format(urlpackage))
            payload['shortdomain'] = shortdomain
        #print(payload)
        # print(self.usersAccountGetUserInfo())
        resp = self.s.post(url, data=payload)
        print(resp.text)
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Something is wrong. Code: {}"
                          .format(str(resp.text)))
            return resp
        else:
            return resp

    # Environment Group
    def envGroupGetGroups(self, envname):
        url = self.hostname + "/1.0/environment/group/rest/getgroups"
        resp = self.s.post(url, data={'session': self.session,
                                        'envName': envname})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Something is wrong. Code: {}"
                          .format(str(resp.text)))
        else:
            return json.loads(resp.text)

    # Environment Control
    def envControlGetNodeGroups(self, envname):
        url = self.hostname + "/1.0/environment/control/rest/getnodegroups"
        resp = self.s.post(url, data={'session': self.session,
                                        'envName': envname})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Something is wrong. Code: {}"
                          .format(str(resp.text)))
        else:
            return json.loads(resp.text)

    def envControlGetContainerNodeTags(self, envname, nodeid):
        url = self.hostname + "/1.0/environment/control/rest/getcontainernodetags"
        resp = self.s.post(url, data={'session': self.session,
                                        'envName': envname,
                                        'nodeId': nodeid})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Something is wrong. Code: {}"
                          .format(str(resp.text)))
        else:
            return json.loads(resp.text)

    def envControlGetEnvInfo(self, envname):
        url = self.hostname + "/1.0/environment/control/rest/getenvinfo"
        resp = self.s.post(url, data={'session': self.session,
                                        'envName': envname})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Something is wrong. Code: {}"
                          .format(str(resp.text)))
        else:
            return json.loads(resp.text)

    def envControlGetEnvs(self):
        url = self.hostname + "/1.0/environment/control/rest/getenvs"
        resp = self.s.post(url, data={'session': self.session})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Something is wrong. Code: {}"
                          .format(str(resp.text)))
        else:
            return json.loads(resp.text)

    # System
    def sysAdminGetUsersByStatus(self):
        url = self.hostname + "/1.0/system/admin/rest/getusersbystatus"
        resp = self.s.get(url, params={'session': self.session,
                                         'status': '0'})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot retrieve list of users. Code:"
                          + str(resp.text))
        else:
            return json.loads(resp.text)

    def sysAdminSignAsUser(self, usermail, n=10):
        url = self.hostname + "/1.0/system/admin/rest/signinasuser"
        resp = self.s.get(url, params={'session': self.session,
                                         'login': usermail,
                                         'appid': 'cluster'})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot sign in as user {}: Code: {}"
                          .format(usermail, str(resp.text)))
        else:
            if 'session' not in json.loads(resp.text) and n>0:
                print(resp.text)
                self.logging.warning("\nsession: {}\ntoken: {}"
                                .format(self.session, self.token))
                self.logging.warning("Auth problem, retrying {} time..."
                                .format(n))
                self.sysAdminSignAsUser(usermail, n=n-1)
            return json.loads(resp.text)['session']


    # Users
    def usersAuthGetSessions(self):
        url = self.hostname + "/1.0/users/authentication/rest/getsessions"
        resp = self.s.get(url, params={'session': self.session,
                                       'appid': 'cluster'})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot retrieve current user sessions. Code:"
                          + str(resp.text))
        else:
            return json.loads(resp.text)

    def usersAccountGetUserInfo(self):
        url = self.hostname + "/1.0/users/account/rest/getuserinfo"
        resp = self.s.get(url, params={'session': self.session,
                                       'appid': 'cluster'})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot retrieve current user info. Code:"
                          + str(resp.text))
        else:
            self.login = json.loads(resp.text)['email']
            self.uid = json.loads(resp.text)['uid']
            return json.loads(resp.text)

    def usersAuthSigninByToken(self, n=10):
        url = self.hostname + "/1.0/users/authentication/rest/signinbytoken"
        resp = self.s.get(url, params={'token': self.token,
                                         'session': self.token,
                                         'userHeaders': 'None'})
        if json.loads(resp.text)['result'] != 0:
            self.logging.error("Cannot authenticate. Code: {}"
                          .format(resp.text))
        else:
            if 'session' not in json.loads(resp.text) and n>0:
                print(resp.text)
                self.logging.warning("Auth problem, retrying {} time..."
                                .format(n))
                self.usersAuthSigninByToken(n=n-1)
            self.logging.info("Token authentication successful.")
            self.session = json.loads(resp.text)['session']
            self.usersAccountGetUserInfo()
            return json.loads(resp.text)
