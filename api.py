from twisted.python import log
from twisted.internet import defer
import re

def set_route(call, method, route, **kwargs):
    call = defer.inlineCallbacks(call)
    call.method = method
    call.route = re.compile(route)
    call.template = kwargs.get('template', None)
    call.last = kwargs.get('last', False)
    call.redirect = kwargs.get('redirect', None)
    return call

GET = lambda route, **kwargs: lambda call: set_route(call, 'GET', route, **kwargs)
POST = lambda route, **kwargs: lambda call: set_route(call, 'POST', route, **kwargs)
