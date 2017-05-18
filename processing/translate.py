# -*- coding: UTF-8 -*-
'''
David Barrell (520704), Bobby Koteski (696567), Steve Dang (807773)
Read tweets from a view, translate with Google API and save it back to the same Couchdb
'''
# +----------------------------------------------------------------------+

import getpass, couchdb, json, pprint, re, requests, sys, time
from textblob import TextBlob
from google.cloud import translate 

pp = pprint.PrettyPrinter(indent=2)
# +----------------------------------------------------------------------+

''' Access the view from source database '''
ip_send   	 = 'localhost:5984'
dbname_send  = 'processed_tweet_db'
user_send 	 = ''
pw_send 	 = ''
server_send  = 'http://' + user_send + ':' + pw_send + '@' + ip_send + '/' + dbname_send + '/'
view_tweets  = '_design/for_translation/_view/new-view'
view_quotas  = '_design/non-eng-tweets/_view/new-view'

''' Access to receiver database '''
ip_recv   	= ''
dbname_recv	= 'processed_tweet_db'
user_recv 	= ''
pw_recv		= ''
server_recv = 'http://' + user_recv + ':' + pw_recv + '@' + ip_recv + '/'

''' Try connecting to receiver database '''
try:
	db_recv = couchdb.Server(server_recv)[dbname_recv]
	print "Successfully connected with receiver", server_recv
except Exception as err:
	print "Unsuccessfully connect with receiver", server_recv

# +----------------------------------------------------------------------+

''' Process the tweet text to remove unwanted symbols and characters '''
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
	u"(\ud83d[\ude00-\ude4f])|"  # emoticons
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

''' Do sentiment analysis '''
def get_sentiment(text):
	t = TextBlob(text)
	s = t.sentiment
	return s.polarity, s.subjectivity 

# +----------------------------------------------------------------------+
''' Translate a text to English with Google Translation API '''
def translate_text(text, target='en'):
    translate_client = translate.Client()
    try:
    	result 			 = translate_client.translate(text, target_language=target)
    	translation  	 = result['translatedText']
    	source_lang 	 = result['detectedSourceLanguage']
    	return translation, source_lang
    except Exception as err:
    	print "Something wrong from Google API!"
    	return '', ''

# +----------------------------------------------------------------------+
''' Load data from Couchdb Map Reduce Views '''
def request_map_reduce_view(server, view):
	''' request a map reduce view from couchdb '''
	request = '?&reduce=true&group=true'
	r = requests.get(server + view + request)
	response = json.loads(r.content)
	docs = response['rows']
	return docs 

def get_translation_quotas(server, view_quotas):
	''' get counts of langs and set quotas for each language '''
	result = request_map_reduce_view(server, view_quotas)

	all_non_eng_langs = []
	for i in result:
		lang = i['key']
		num  = i['value']
		all_non_eng_langs.append((lang, num))

	all_non_eng_langs.sort(key=lambda tup: tup[1], reverse=True)

	percent_translated = 1
	quotas = {}
	for i in all_non_eng_langs:
		quotas[i[0]] = int(i[1]*percent_translated)
	return quotas 

# +----------------------------------------------------------------------+
''' Load data from Couchdb '''

def get_docs_count(db, view):
	''' get the number of tweets in the view '''
	request = db + view 
	r = requests.get(request)
	content = json.loads(r.content)
	total_docs = content['rows'][0]['value']
	return total_docs

def get_tweets(server, view, skip, limit):
	''' get doc from a Couchdb view '''
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
			time.sleep(10)
			sys.stdout.flush()
			return get_tweets(server, view, skip,limit)	

	else:
		print '-- server did not respond --'
		print 'sleeping for 10 seconds then restart'
		time.sleep(10)
		sys.stdout.flush()
		return get_tweets(server, view, skip,limit)

def translate_tweets_from_view(db, view, quota, db_recv):
	''' translate tweets and update translation, community, sentiment to the doc '''
	# check how many docs to process in total 
	total_docs_from_view = get_docs_count(db, view)
	n = total_docs_from_view

	print "Total docs from view: ", n
	quotas 	 = quota
	progress = {}

	# initialize progress
	for k in quotas.keys():
		progress[k] = 0

	tweet_allowance = 70428 # total tweets translated for US$ 200
	chars_allowance = 1999000 # total chars translated for $US 200
	
	tweets_translated = 0
	chars_translated = 0

	total_queried = 0
	for k in xrange(0, n/1000+1):
		skip  = k * 1000
		limit = 1000 

		docs = get_tweets(db, view, skip, limit)
		total_queried += len(docs)

		for doc in docs :
			tweet  = doc['value']
			doc_id = doc['id']
			doc_db = db_recv.get(doc_id)

			# check if this tweet is already translated
			if 'community_lang' not in tweet:

				''' translate the tweet '''
				lang = tweet['lang']

				# check if there's any remaining quota for this language 
				if 'en' not in lang:
					if progress[lang] < quotas[lang]:
						text = tweet['text']

						# filter the text 
						fil_text = filter_tweet(text)

						print "- Language   : ", lang
						print "- Text       : ", text
						print "- Filter     : ", fil_text
						if fil_text != '' and fil_text.isspace() == False:

							# translate the text 
							chars_query = len(fil_text) # how many chars sent to Google API
							translation, source_lang = translate_text(fil_text)

							# record Google API usage 
							tweets_translated += 1
							chars_translated += chars_query

							if translation != '' and source_lang != '':
								pol, subj = get_sentiment(translation)

								# assign new value for the doc and update db  
								doc_db['translation'] 	 = translation
								if source_lang == lang:
									community = source_lang
								else:
									community = lang 
								doc_db['community_lang'] = community
								doc_db['polarity']		 = pol 
								doc_db['subjectivity']	 = subj 
								db_recv.save(doc_db)

								# update progress 
								progress[lang] = progress.get(source_lang, 0) + 1
								
								print "- Translation: ", translation
								print "- Source_lang: ", source_lang
								print "- Community  : ", community
								print "- Sentiment  : ", pol, subj

								print "- Chars used : ", chars_query
								print "- Progress   : ", progress[lang], " / ", quotas[lang], "quota"
							else:
								print "- Google can't translate this tweet. LAME!"

							print '='*25

							if tweets_translated >= tweet_allowance or chars_translated >= chars_allowance:
								sys.stdout.flush()
								return "Out of all quotas. Finished updating " + str(tweets_translated) + "tweets"
					else:
						print "The language ", lang, " has reached the language quota of ", quotas[lang]

		if tweets_translated == total_queried:
			sys.stdout.flush()
			print "Translated ", tweets_translated, " tweets"
			print "Already queried all tweets from the view. FINISHED!"
			print '======================'
			return 
					

		




# +----------------------------------------------------------------------+

if __name__ == '__main__':
	
	# get quotas to translate for each language 
	quotas = get_translation_quotas(server_send, view_quotas)

	# translate 
	translate_tweets_from_view(server_send, view_tweets, quotas, db_recv)


	




















