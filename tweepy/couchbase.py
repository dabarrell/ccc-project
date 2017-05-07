
import requests
import json
import couchdb
import sys
import time

URL_DB = 'http://Administrator:aurinRootfery@130.56.251.175:80/'
URL_VIEW = 'pools/default/buckets/melbourne/'
PROCESS = 1000
# r = requests.get("http://Administrator:aurinRootfery@130.56.251.175:80/pools/default/buckets/melbourne/docs?inclusive_end=true&skip=0&include_docs=false&limit=5")
# print r.content

def get_item_count():
	''' get the number of tweets in the db '''
	r = requests.get(URL_DB + URL_VIEW)
	content = json.loads(r.content)
	item_count = content['basicStats']['itemCount']
	return int(item_count)

def get_tweets(skip,limit,sleep=8):
	''' get and return json objects '''
	request = 'docs?inclusive_end=true&skip={}&include_docs=true&limit={}'.format(
		skip,limit
	)
	# print request
	r = requests.get(URL_DB + URL_VIEW + request)
	if r.status_code == 200:
		try:
			return json.loads(r.content)
		except Exception as e:
			print '-- invalid json object --'
			print 'sleeping for {} seconds. relax!'.format(sleep)
			time.sleep(sleep)
			sys.stdout.flush()
			return get_tweets(skip,limit,sleep=sleep*2)
	else:
		print '-- server did not respond --'
		print 'sleeping for {} seconds. relax!'.format(sleep)
		time.sleep(sleep)
		sys.stdout.flush()
		return get_tweets(skip,limit,sleep=sleep*2)

# store into 115.146.93.170:5984
db_url = 'http://steve_100GB:steveisawesome@localhost:5984/'
db = couchdb.Server(db_url)['foreign2']

n = get_item_count()
print 'processing!!! ...time to relax!'

for k in xrange(0,n/PROCESS+1):
	skip = k * PROCESS
	collection = []
	docs = get_tweets(skip,PROCESS)
	if docs is not None and 'rows' in docs:
		for doc in docs['rows']:
			t = doc['doc']['json']
			if 'retweeted_status' not in t:
				if 'en' not in t['lang'] or 'en' not in t['user']['lang']:
					# print t['lang'], t['user']['lang']
					# print t
					# print ''
					# sys.stdout.flush()
					collection.append(t)
		# mass update to the db
		print 'processed:', skip + PROCESS, 'tweets. relax!' 
		db.update(collection)
		sys.stdout.flush()
		# sys.exit()
	else:
		print 'something went wrong from', skip, '-', skip + PROCESS, 'relax!'
