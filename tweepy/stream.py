'''
python stream.py 
	--ckey ***RM5WNj25gXq3m6TJX2K*** 
	--csecret ***7sC3ij17HGVSK6VaxWbPEx72GX33UJGufSnDRFKUGfUf*** 
	--atoken ***140447908122624-mA6fRa345bNZXESj6V125HILoJYS*** 
	--asecret ***bVWOxYgldsGqPFjjUXlslupUHgAkTFoYyibGY91*** 
	--host localhost
	--port 5984
	--member admin 
	--pw password 
	--dbname test1 
	--keywords audusd,eurusd 
	--debug
'''

import tweepy
import json
import couchdb
import time
from argparse import ArgumentParser

parser = ArgumentParser(description='Start up a twitter stream and store tweets in a CouchDB')
parser.add_argument('--ckey',help='Consumer Key for twitter',required=True)
parser.add_argument('--csecret',help='Consumer Secret for twitter',required=True)
parser.add_argument('--atoken',help='Access Token for twitter',required=True)
parser.add_argument('--asecret',help='Access Token Secret for twitter',required=True)
parser.add_argument('--port', default=5984, help='CouchDB port number (%(default)s)', type=int)
parser.add_argument('--host', help='CouchDB host address (%(default)s)', default='localhost', type=str)
parser.add_argument('--member', help='CouchDB member name', default='', type=str)
parser.add_argument('--pw', help='CouchDB member pw', default='', type=str)
parser.add_argument('--dbname', help='CouchDB database name', required=True, type=str)
parser.add_argument('--keywords',help='(Optional) Key words for twitter, e.g., keyword1,keyword2,...')
parser.add_argument('--debug', help='Print debug messages to screen', action='store_true')
args = parser.parse_args()

# Authentication details. To  obtain these visit dev.twitter.com
consumer_key = args.ckey
consumer_secret = args.csecret
access_token = args.atoken
access_token_secret = args.asecret

# try and connect to the couchdb instance
try:
	if args.member is '':
		server = 'http://' + args.host + ':' + str(args.port) + '/'
	else:
		server = 'http://'+args.member+':'+args.pw+'@'+args.host+':'+str(args.port)+'/'
	# db = pycouchdb.Server(server).database(args.dbname)
	tweetdb = couchdb.Server(server)[args.dbname]
	if args.debug is True: print('connection successful')
except Exception as e:
	print('Connection unsuccessful')
	sys.exit()

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):
    def on_data(self, data):
        # Twitter returns data in JSON format - we need to decode it first
        decoded = json.loads(data)
        # Also, we convert UTF-8 to ASCII ignoring all bad characters sent by users
        # print '@%s: %s' % (decoded['user']['screen_name'], decoded['text'].encode('ascii', 'ignore'))
        # print json.dumps(decoded['user']['screen_name'], indent=4)
        # print json.dumps(decoded,indent=4)
        try:
        	# set the doc id
            doc = {
                '_id':decoded['id_str']
            }
            # update the rest of the json object into doc
            doc.update(decoded)
            if args.debug is True:
            	print doc
            # put the doc in the db
            print tweetdb.save(doc)
            print ''
        except Exception as e:
            print e
            # print json.dumps(decoded,indent=4)
            print '' 
        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    '''
    110.95,-54.83,159.29,-11.35 # aus coords
    144.5937,-38.59,145.5125,-37.5113 # melbourne coords
    http://stackoverflow.com/questions/22889122/how-to-add-a-location-filter-to-tweepy-module
    http://boundingbox.klokantech.com/
    https://dev.twitter.com/streaming/overview/request-parameters#locations
    http://stackoverflow.com/questions/35268154/get-location-specific-tweets-from-twitter-using-tweepy?noredirect=1&lq=1
    '''
    l = StdOutListener()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    if args.keywords == None:
    	print 'Streaming tweets from Australia.'
    	print ''
    else:
    	key_words = args.keywords.split(',')
    	print 'Streaming tweets with ', key_words

    while True:
        try:
            # There are different kinds of streams: public stream, user stream, multi-user streams
            # In this example follow #programming tag
            # For more details refer to https://dev.twitter.com/docs/streaming-apis
            stream = tweepy.Stream(auth, l)
            if args.keywords == None:
            	stream.filter(locations=[110.95,-54.83,159.29,-11.35])
            else:
            	stream.filter(track=key_words)
        except:
            print 'sleeping for 15 mins'
            print ''
            time.sleep(60*15)
            continue
