import cyclone.web, api, collections, handler, db, files
from PIL import Image
import hashlib
from twisted.application import service, internet
from twisted.internet import defer, reactor
from twisted.python import log
from handler import Stink

class PageHandler(handler.Handler):
    reqs = {'width':1024, 'height':1024, 'size':1024*1024}

    @defer.inlineCallbacks
    def is_owner(self):
        user_id, page = (self.request.user, self['page'])
        data = yield db.row("""
            select users.id as user_id, pages.published from users, pages
                where pages.user_id = users.id
                and pages.id = %(page)s""",
            {'page': page})
        if not data: raise Stink("no page set %s" % page)
        if data['user_id'] != user_id: raise Stink("you don't own page %s" % page)
        defer.returnValue(data['published'])

    def verify(self):
        if not 'file' in self.request.files: raise Stink("you must upload an image")
        files.verify(self.request.files['file'][0]['body'], self.reqs)

    @api.POST(r"^/page/add$", redirect="/page/")
    def add(self):
        self.verify()
        published = yield self.is_owner()
        if published: raise Stink("can't add an image to a published page")
        yield files.save(self.request.files['file'][0]['body'], 'page', set_id=self['page'])

    @api.POST(r"^/page/new$", redirect="/page/")
    def new(self):
        self.verify()
        page = yield db.value("insert into pages (user_id) values (%(user_id)s) returning id", 
            {'user_id': self.request.user})
        self['page'] = page
        yield self.add()

    @api.POST(r"^/page/select$", redirect="/page/")
    def select(self):
        published = yield self.is_owner()
        if not published: raise Stink("can't select an unpublished page")
        user_id, page = (self.request.user, self['page'])
        yield db.query("update users set page = %(page)s where id = %(user_id)s",
            {'page': page, 'user_id': user_id})

    @api.POST(r"^/page/publish", redirect="/page/")
    def publish(self):
        published = yield self.is_owner()
        if published: raise Stink("this page is already published")
        yield db.query("update pages set published = true where id = %(page)s", {'page': self['page']})
        yield self.select()

    @api.GET(r"^/page/$", template="pages.html")
    def pages(self):
        data = yield db.query("""
            select users.page as active, pages.id, pages.published, files.name, files.url
            from pages, files, users
                where users.id = %(user_id)s
                and pages.user_id = users.id
                and files.set_id = pages.id""",
            {'user_id' : self.request.user})

        if not data: defer.returnValue({'published': [], 'unpublished':[]})
        published, unpublished = (collections.defaultdict(list),collections.defaultdict(list))
        for row in data: 
            if row['published']: published[row['id']].append({'url':row['url']})
            else:              unpublished[row['id']].append({'url':row['url']})
        log.msg("%s %s" % (published, unpublished))
        try: active = {'id':data[0]['active'], 'pages':published.pop(data[0]['active'])}
        except KeyError: active = None
        published   = [{'id': id, 'files': pages} for id, pages in published.iteritems()]
        unpublished = [{'id': id, 'files': pages} for id, pages in unpublished.iteritems()]
        defer.returnValue({'active':active, 'published':published, 'unpublished':unpublished})
