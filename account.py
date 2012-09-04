# coding: utf-8
import cyclone.web, api, sys, collections, pprint, options, db, StringIO, os, urllib, user, datetime, files, handler, avatar
from twisted.python import log
from twisted.internet import reactor, defer
from twisted.application import service, internet
from PIL import Image
import hashlib

from handler import Stink

class AccountHandler(handler.Handler):
    @api.POST(r"^/account/$", last=True)
    def account(self):
        ret = yield getattr(self, self.request.arguments['action'][0])()
        defer.returnValue(ret)

    @api.POST("^/account/register$", last=True)
    def register(self):
        log.msg('register args: %s' % self.request.arguments)
        username, password = self['username'], self['password']
        salt = os.urandom(16).encode('hex')
        hash = hashlib.sha256(password + salt).hexdigest()
        user_id = yield db.value("""
            insert into users (username, hash, salt) 
                values (%(username)s, %(hash)s, %(salt)s) returning id""",
                {'username':username, 'hash':hash, 'salt':salt})

        data = yield self.login()

        avatar_handler = avatar.AvatarHandler(self.application, self.request)
        avatar_handler['name'] = 'chill'
        yield avatar_handler.new()
        yield avatar_handler.select()
        data['message'] = 'registered your account'
        defer.returnValue(data)

    @api.POST(r"^/account/login$", last=True)
    def login(self):
        username, password = self['username'], self['password']
        salt_hash = yield db.row("""
            select id, salt, hash from users where username = %(username)s""", 
            {'username':username})

        if not salt_hash: raise Stink("no user named %s" % username)
        
        user_id, salt, hash = tuple((salt_hash[key] for key in ('id', 'salt', 'hash')))
        if hashlib.sha256(password + salt).hexdigest() == hash:
            token = os.urandom(16).encode('hex')
            yield db.query("""
                insert into tokens (user_id, token) values (%(user_id)s, %(token)s)""",
                {'user_id':user_id, 'token':token})
            self.set_cookie('token', token)
        else: raise Stink("bad password")
        self.request.user = yield db.value("""select user_id from tokens where token = %(token)s""", {'token':token})
        defer.returnValue({'message' : 'logged in', 'token':token, 'user': {'id': self.request.user}})

    @api.GET(r"^/account/logout$", template="logout.html")
    def logout(self):
        yield db.query("""
            delete from tokens where token = %(token)s""",
            {'token':self['token']})
        self.clear_cookie('token')
        defer.returnValue({"message": 'logged out'})
