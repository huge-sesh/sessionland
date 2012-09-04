# coding: utf-8
# twisted application: sessionland.tac

import cyclone.web, api, sys, options
from twisted.python import log
from twisted.internet import reactor, defer
from twisted.application import service, internet

log.startLogging(sys.stdout)
from jinja2 import Environment, PackageLoader
jinja = Environment(
    autoescape=lambda name: True, 
    loader=PackageLoader('sessionland', 'templates'), 
    extensions=['jinja2.ext.autoescape'])

import avatar, page, post, account   
class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"^/static/(.*)$", cyclone.web.StaticFileHandler, {"path": "static"}),
            (r"^/files/(.*)$", cyclone.web.StaticFileHandler, {"path": "files"}),
            (r"^/avatar/.*$", avatar.AvatarHandler),
            (r"^/page/.*$", page.PageHandler),
            (r"^/account/.*$", account.AccountHandler),
            (r"^/.*$", post.PostHandler),
        ]

        settings = {
            "static_path": "./static",
            "template_path": "./template",
            "debug": True,
        }

        cyclone.web.Application.__init__(self,
            handlers, **settings)

if __name__ == "__main__":
    reactor.listenTCP(options.port, Application(), interface=options.bind)
    reactor.run()
