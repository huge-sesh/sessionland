import argparse, os, sys, urlparse

parser = argparse.ArgumentParser()
parser.add_argument('--bind', type=str, default='127.0.0.1', help='bind to ip')
parser.add_argument('--port', type=int, default=8888, help='port to listen/send on')

for option, value in vars(parser.parse_args()).iteritems():
    globals()[option] = value

if os.getenv('PORT'):
    globals()['port'] = int(os.getenv('PORT'))

if 'database' not in globals():
    database = {}

if 'DATABASE_URL' in os.environ:
    url = urlparse.urlparse(os.environ['DATABASE_URL'])

    # Ensure default database exists.
    database = database.get('default', {})

    # Update with environment configuration.
    database.update({
        'name': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port,
    })
