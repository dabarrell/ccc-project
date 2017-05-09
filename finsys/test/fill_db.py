import couchdb
from random import randint
import time, datetime

db = couchdb.Server('http://115.146.93.197:5984/')['test']
# for i in xrange(80):
# 	try:
# 		dt = datetime.datetime(2017,randint(1,5),randint(0,30),randint(0,23),randint(0,59),randint(0,59))
# 		doc = {'datetime':dt.strftime('%a %b %d %H:%M:%S %Y')}
# 		print doc
# 		print db.save(doc)
# 	except:
# 		pass

for row in db.view('_design/js/_view/test2',startkey='2017-04-04 15:00:00',endkey='2017-04-04 23:59:59'):
	print row
