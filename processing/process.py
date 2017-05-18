# -*- coding: UTF-8 -*-
'''
Author: bdang1@student.unimelb.edu.au
Filter tweets from a tweet_db view then save to a new couchdb on local instance
Criteria: 
- Reject retweets 
- Filter unwanted chars from text
- Get sentiment score for english tweets
'''
# +----------------------------------------------------------------------+

import getpass, couchdb, json, pprint, re, requests, sys, time
from couchdb.design import ViewDefinition
from textblob import TextBlob

pp = pprint.PrettyPrinter(indent=2)
# +----------------------------------------------------------------------+

'''
Access SENDER DB 
'''
ip_send   	 = 'localhost:5984' 
dbname_send  = 'tweet_db'
user_send 	 = ''
pw_send   	 = getpass.getpass('Enter password for database %s: ' % dbname_send)
server_send  = 'http://' + user_send + ':' + pw_send + '@' + ip_send + '/' + dbname_send + '/'
view_send 	 = '_design/for_processing/_view/new-view'

url = server_send + view_send

print "SENDER: ", url 

'''
Access to RECEIVER DB 
'''
ip_recv   	= '' # IP of the couchdb to save translation 
dbname_recv	= 'processed_tweet_db'
user_recv 	= ''
pw_recv   	= getpass.getpass('Enter password for database %s: ' % dbname_recv)
server_recv = 'http://' + user_recv + ':' + pw_recv + '@' + ip_recv + '/'

'''
try connecting to receiver database
'''
try:
	db_recv = couchdb.Server(server_recv)[dbname_recv]
	print "Successfully connected with receiver", server_recv
except Exception as err:
	print "Unsuccessfully connect with receiver", server_recv

# +----------------------------------------------------------------------+

'''
Process the tweet text to remove unwanted symbols and characters 
'''
def remove_non_letters(text):
	# regex patterns
	hashtag	 = r'#\S+' 
	email	 = r'[\w\d\._-]+@\w+(\.\w+){1,3}'
	website	 = r'http\S+|www\.\w+(\.\w+){1,3}'
	retweet  = r'RT\s@\S+' 
	mention  = r'@[\w\d]+'
	punctual = r'[_\+-\.,!@\?#$%^&*();\\/|<>"\':]+'
	weird	 = r'�+'
	newline  = r'\n'
	spaces 	 = r'\s{2,}'
	digits   = r'\d+'

	combined_patterns = r'|'.join((hashtag, email, website, retweet, mention, punctual, weird, newline, digits))
	stripped = re.sub(combined_patterns, ' ', text)
	# remove extra whitespaces 
	stripped = re.sub(spaces, ' ', stripped)
	stripped = stripped.strip()
	return stripped

def remove_emojis(text):
	emoji_pattern = re.compile( 
	u"(\ud83d[\ude00-\ude4f])|"  # emoticonsa
	u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
	u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
	u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
	u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
	"+", flags=re.UNICODE)
	# return ''.join(c for c in str if c not in emoji.UNICODE_EMOJI)
	return emoji_pattern.sub(r' ', text)

def filter_tweet(text):
	text = remove_emojis(text)
	text = remove_non_letters(text)
	if not text or len(text) == 0: 
		return ''
	else: 
		return text 

'''
Do sentiment analysis 
'''
def get_sentiment(text):
	t = TextBlob(text)
	s = t.sentiment
	return s.polarity, s.subjectivity 

def process_tweet(tweet):
	if 'retweeted_status' not in tweet:
		print "DOCTYPE: ", type(tweet)
		print '==='
		print tweet['text']
		print tweet['lang'], tweet['user']['lang']

		# -- processing -- 
		# filter text 
		fil_text  = filter_tweet(tweet['text'])
		print '- Filtered:%s' % fil_text

		# fields needed from a status
		wanted_info = {
			'coordinates' : tweet['coordinates'], 
			'created_at'  : tweet['created_at'],
			'favorite_count' : tweet['favorite_count'], 
			'lang' : tweet['lang'],
			'place': tweet['place'],
			'retweet_count': tweet['retweet_count'],
			'source': tweet['source'],
			'text': tweet['text'],
			'user': tweet['user'],
			'id_str': tweet['id_str']
		}

		# get sentiment score for eng tweet 
		if 'en' in tweet['lang']: # if tweet in English
			pol, subj = get_sentiment(fil_text) 
			community = tweet['user']['lang']
			print "- Assigned community: ", community
			print '==='

			# -- saving new doc --
			doc = {
				'_id' 			 : tweet['id_str'],
				'community_lang' : community,
				'polarity'		 : pol,
				'subjectivity'	 : subj
			}
			
		else: # if tweet not in English
			doc = {
				'_id' : tweet['id_str']
			}

		doc.update(wanted_info)
		return doc 
# +----------------------------------------------------------------------+
'''
# Load data from Couchdb
'''

def get_docs_count(db, view):
	''' get the number of tweets in the view '''
	request = db + view 
	r = requests.get(request)
	content = json.loads(r.content)
	total_docs = content['rows'][0]['value']
	return total_docs

def get_tweets(server, view, skip, limit):
	request = '?skip={}&limit={}&reduce=false'.format(skip, limit)
	r = requests.get(server + view + request)
	if r.status_code == 200:

		try:
			response = json.loads(r.content)
			docs = response['rows']
			return docs 

		except Exception as e:
			print '-- invalid json object --'
			print 'sleeping for 10 seconds'
			time.sleep(15)
			sys.stdout.flush()
			return get_tweets(server, view, skip,limit)	

	else:
		print '-- server did not respond --'
		print 'sleeping for 10 seconds then restart'
		time.sleep(15)
		sys.stdout.flush()
		return get_tweets(server, view, skip,limit)

def process_data_from_sender(db, view_name):
	# check how many docs to process in total 
	total_docs_from_view = get_docs_count(db, view_name)
	n = total_docs_from_view

	total = 0
	for k in xrange(0, n/1000+1):
		skip  = k * 1000
		limit = 1000 
		docs = []
		tweets = get_tweets(server_send, view_send, skip, limit)

		for i in tweets:
			doc = process_tweet(i['value'])
			docs.append(doc)

		db_recv.update(docs)
		sys.stdout.flush()
		total += len(docs)
		print "Updated: " + str(len(docs)) + ', total: ' + str(total)
		print '======================'

		if total == total_docs_from_view:
			sys.stdout.flush()
			return "Finishing updating " + total + "docs from " + str(n) + "docs"


if __name__ == '__main__':
	process_data_from_sender(server_send, view_send)

















