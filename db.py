import os, sys, urlparse, psycopg2ct, secrets
from twisted.internet import defer
from twisted.python import log
from txpostgres import txpostgres
from psycopg2ct import extras
import psycopg2

urlparse.uses_netloc.append('postgres')
database = {
    'dbname': 'sessionland',
    'user':   'postgres',
    'password': secrets.db_pass,
    'host' : '127.0.0.1',
    'port' : 5432,
}

if os.environ.get('DATABASE_URL', None):
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    database.update({
        'dbname': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port,
    })

pool = txpostgres.ConnectionPool(None, connection_factory=extras.RealDictConnection, **database)
pool.start()

@defer.inlineCallbacks
def query(q, parameters={}):
    try:
        log.msg("db query %s:, %s" % (q, parameters))
        result = yield pool.runQuery(q, parameters)
        log.msg("returning: %s" % result)
        defer.returnValue(result)
    except psycopg2.ProgrammingError as e:
        if e.message == 'no results to fetch': defer.returnValue([])
        else: raise

@defer.inlineCallbacks
def row(*args, **kwargs):
    result = yield query(*args, **kwargs)
    if result: defer.returnValue(result[0])
    else: defer.returnValue(None)

@defer.inlineCallbacks
def value(*args, **kwargs):
    result = yield query(*args, **kwargs)
    if result: defer.returnValue(result[0].values()[0])
    else: defer.returnValue(None)
