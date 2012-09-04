from twisted.internet import defer
from twisted.python import log
import db, StringIO, files, os, psycopg2
from PIL import Image

def verify(data, reqs):
    image = Image.open(StringIO.StringIO(data))
    if 'width' in reqs and image.size[0] > reqs['width']: raise Stink('image width (%s) exceeds max (%s)' % (reqs['width'], image.size[0]))
    if 'height' in reqs and image.size[1] > reqs['height']: raise Stink('image height (%s) exceeds max (%s)' % (reqs['height'], image.size[1]))
    if 'size' in reqs and len(data) > reqs['size']: raise Stink('image size (%s bytes) exceeds max (%s bytes)' % (len(data), reqs['size']))
    return True

@defer.inlineCallbacks
def save(data, klass, set_id, name=None):
    image = Image.open(StringIO.StringIO(data))
    id = yield db.value("""insert into files (set_id, name) values (%(set_id)s, %(name)s) returning id""",
        {'set_id' : set_id, 'name': name})
    url = 'files/%s/%s.%s' % (klass, id, image.format.lower())
    yield db.query("update files set url = %(url)s where id = %(id)s",
        {'url': '/'+url, 'id':id})
    with open(url, 'w') as f: f.write(data)
