import cyclone.web, collections, db, json, datetime, pprint
from twisted.python import log
from twisted.internet import defer

class Stink(Exception): pass
def dthandler(obj):
    if isinstance(obj, datetime.datetime): return obj.isoformat() 
    raise Stink("obj can't be json serialized: %s", type(obj), obj)
def dumps(obj):return json.dumps(obj, default=dthandler)

class Handler(cyclone.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.api = collections.defaultdict(list)
        for call in (getattr(self, call) for call in dir(self) if callable(getattr(self, call))):
            if hasattr(call, 'method'): 
                self.api[call.method].append(call)

        log.msg('routes:')
        for method in self.api.keys():
            for call in self.api[method]:
                log.msg('%s %s template:%s redirect:%s last:%s' % (method, call.route.pattern, call.template, call.redirect, call.last))

    def print_routes(self):
        for call in (getattr(self, call) for call in dir(self) if callable(getattr(self, call))):
            if hasattr(call, 'method'): 
                log.msg('%s supports %s on %s' % (call.route.pattern, call.method, call.template))

    def arg(self, key, default=None):
        return self.__getitem__(key, default)

    def __getitem__(self, key, default=None):
        if key in self.request.arguments: 
            return self.request.arguments[key][0]
        elif self.get_cookie(key): return self.get_cookie(key)
        return default
    
    def __setitem__(self, key, value):
        self.request.arguments[key] = [value]

    def args(self, all=False):
        if all: return dict([(key, self.request.arguments[key]) for key in self.request.arguments] + (self.request.cookies.items() or []))
        else: return dict([(key, self.request.arguments[key][0]) for key in self.request.arguments] + (self.request.cookies.items() or []))

    @defer.inlineCallbacks
    def process(self, method, merge = {}):
        import sessionland
        log.msg("process %s %s %s" % (method, self.request.path, self.args()))
        if self.request.path.endswith('.json'):
            path = self.request.path[:-5]
            render = False
        else: 
            path = self.request.path
            render = True

        self.request.user = yield db.value("""select user_id from tokens where token = %(token)s""", {'token':self['token']})
        data = {'user':{'id':self.request.user}}

        for call in self.api[method]:
            match = call.route.match(path)
            if match: 
                log.msg('calling %s: %s' % (call.route.pattern, call.__name__))
                try:
                    result = yield call(*match.groups())
                    data.update(merge)
                    if result: data.update(result)
                    log.msg('got data:\n%s' % pprint.pformat(data))
                    if render: 
                        if call.last: self.redirect(self.arg('last'), status=303)
                        elif call.redirect: self.redirect(call.redirect, status=303)
                        else:
                            data['last'] = self.request.path
                            data['data'] = dumps(data)
                            log.msg('getting template: %s' % call.template)
                            self.write(sessionland.jinja.get_template(call.template).render(**data))
                    else: 
                        log.msg("return JSON: "+dumps(data))
                        self.write(dumps(data))
                except Stink as e:
                    log.msg('request args: %s, message: %s' % (self.request.arguments, e.message))
                    data = {'message': e.message}
                    if render: 
                        if 'last' in self.request.arguments:
                            self.request.path = self.request.arguments['last'][0]
                            yield self.process('GET', merge=data)
                        else: self.write(e.message)
                    else: 
                        log.msg("return JSON: "+dumps(data))
                        self.write(dumps(data))
                return

    @defer.inlineCallbacks
    def get(self): 
        yield self.process('GET')

    @defer.inlineCallbacks
    def post(self): 
        yield self.process('POST')
