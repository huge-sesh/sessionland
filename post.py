# coding: utf-8
import cyclone.web, api, sys, collections, pprint, handler, options, db, StringIO, os, urllib, user, datetime, files
from twisted.python import log
from twisted.internet import reactor, defer
from twisted.application import service, internet
from PIL import Image
import hashlib

from handler import Stink
PATH_LIMIT = 10000

class PostHandler(handler.Handler):
    @defer.inlineCallbacks
    def user(self):
        user = yield db.query("""
            select files.name, files.id as file_id, files.url
            from users, avatars, files
                where users.avatar = avatars.id
                and files.set_id = avatars.id
                and users.id = %(user_id)s
                order by file_id asc""", {'user_id': self.request.user})
        if not user: defer.returnValue(None)
        defer.returnValue({'id': self.request.user, 'avatar' : [{'name':row['name'], 'id':row['file_id'], 'url':row['url']} for row in user]})

    @api.POST(r"^/post$", last=True)
    def post_message(self):
        forum, thread, content, avatar = (self['forum'], self['thread'], self['content'], self['avatar'])
        if not self.request.user: raise Stink('must be logged in/token must be valid')
        if not avatar: raise Stink('must specify avatar id')
        if not (forum or thread): raise Stink('must specify forum id or thread')
        if forum and thread: raise Stink('pick one, a forum or a thread to post to')
        if forum:
            page = yield db.value("select page from users where id = %(forum)s", {'forum':forum})
            if not page: raise Stink("can't post a thread to a forum with no page")
            yield db.query("""
                insert into ops (user_id, content, forum_id, avatar_id, dt, page_id)
                values (%(user_id)s, %(content)s, %(forum)s, %(avatar)s, now(), %(page)s)""",
                {'user_id': self.request.user, 'content':content, 'forum': forum, 'avatar': avatar, 'page':page})
        else:     
            yield db.query("""
                insert into posts (user_id, content, thread_id, avatar_id, dt)
                values (%(user_id)s, %(content)s, (select id from ops where content = %(thread)s), %(avatar)s, now())""",
                {'user_id': self.request.user, 'content':content, 'avatar': avatar, 'thread': thread})
        defer.returnValue({'success' : True})

    @api.GET(r"^/(\d*)$", template="thread.html")
    def forum(self, forum_id):
        forum_id = forum_id or 1
        threads = yield db.query("""
            with recent_threads AS (
                select posts.thread_id, max(posts.dt) as last_post from posts, ops
                    where posts.thread_id = ops.id
                    and ops.forum_id = %(forum_id)s
                    group by posts.thread_id
                    order by last_post desc
            )
            select ops.*, recent_threads.last_post, files.url as avatar_url from ops, recent_threads, files 
                where files.id = ops.avatar_id
                and ops.id = recent_threads.thread_id
            """, {'forum_id':forum_id})
        page = yield db.query("""
            select files.id, files.url from files, users 
                where users.id = %(forum_id)s
                and files.set_id = users.page""", {'forum_id': forum_id})
        user = yield self.user()
        defer.returnValue({
            'user':user,
            'forum':forum_id, 
            'page' : page,
            'threads': [
                {
                    'id': thread['id'], 
                    'content': thread['content'], 
                    'dt': thread['last_post'], 
                    'user': {
                        'id':thread['user_id'], 
                        'avatar':thread['avatar_url']
                    }
                } for thread in threads]})

    @api.GET(r"^/(.+)$", template="thread.html")
    def thread(self, path):
        content = urllib.unquote(path)
        comparator = '<'
        if self['comparator'] == 'gt': comparator = '>'
        posts = yield db.query("""
            select ops.page_id, posts.thread_id, posts.content, posts.dt, posts.user_id, files.url as avatar_url
            from posts, ops, files, users 
                where posts.thread_id = ops.id 
                and ops.content = %%(content)s
                and posts.user_id = users.id
                and files.id = posts.avatar_id
                and posts.dt %(comparator)s %%(dt)s
                order by posts.dt desc 
                limit 10
                """ % {'comparator': comparator}, 
                {'content':content, 'dt':self.arg('dt', '3000-01-01T01:01:01') })
        if not posts: raise Stink('no thread named %s' % path)
        page = yield db.query("""
            select files.id, files.url from files, pages 
                where files.set_id = %(page)s
                and pages.id = %(page)s""", 
                {'page': posts[0]['page_id']})
        user = yield self.user()
        defer.returnValue({'user': user, 'thread': content, 'page' : page, 'posts' : list(reversed(
            [{'content': post['content'], 'dt': post['dt'], 'user':{'avatar': post['avatar_url'], 'id':post['user_id']}} for post in posts]
            ))})
