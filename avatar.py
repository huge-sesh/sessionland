import api, collections, handler, db, files
from PIL import Image
from twisted.application import service, internet
from twisted.internet import defer, reactor
from twisted.python import log

from handler import Stink

class AvatarHandler(handler.Handler):
    reqs = {'width':150, 'height':400, 'size':512*1024}

    @defer.inlineCallbacks
    def is_owner(self):
        user_id = yield db.value("""
            select users.id from users, avatars
                where avatars.user_id = users.id
                and avatars.id = %(avatar)s""",
            {'avatar': self['avatar']})
        if not user_id: raise Stink("no avatar set %s" % self['avatar'])
        if user_id != self.request.user: raise Stink("you don't own avatar %s" % self['avatar'])
        defer.returnValue(True)

    def verify(self):
        if not self['name']: raise Stink("images need a name")
        if not 'file' in self.request.files: raise Stink("you have to upload a file")
        files.verify(self.request.files['file'][0]['body'], self.reqs)

    @api.POST(r"^/avatar/add$", redirect="/avatar/")
    def add(self):
        self.verify()
        yield self.is_owner()
        yield files.save(self.request.files['file'][0]['body'], 'avatar', 
            set_id=self['avatar'], name=self['name'])

    @api.POST(r"^/avatar/new$", redirect="/avatar/")
    def new(self):
        self.verify()
        avatar = yield db.value("insert into avatars (user_id) values (%(user_id)s) returning id", 
            {'user_id': self.request.user})
        self['avatar'] = avatar
        yield self.add()

    @api.POST(r"^/avatar/select$", redirect="/avatar/")
    def select(self):
        yield self.is_owner()
        user_id, avatar = (self.request.user, self['avatar'])
        yield db.query("update users set avatar = %(avatar)s where id = %(user_id)s",
            {'avatar': avatar, 'user_id': user_id})

    @api.GET(r"^/avatar/", template="avatars.html")
    def avatars(self):
        data = yield db.query("""
            select users.avatar as active, avatars.id, files.name, files.url
            from avatars, files, users
                where users.id = %(user_id)s
                and avatars.user_id = users.id
                and files.set_id = avatars.id""",
            {'user_id' : self.request.user})

        if not data: defer.returnValue({})
        sets = collections.defaultdict(list)
        for row in data: sets[row['id']].append({'name':row['name'], 'url':row['url']})
        active = {'id':data[0]['active'], 'avatars':sets.pop(data[0]['active'])}
        inactive = [{'id': id, 'avatars': avatars} for id, avatars in sets.iteritems()]
        defer.returnValue({'active':active, 'inactive':inactive})
