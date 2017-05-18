import couchdb, sys, json
# import numpy as np
# from matplotlib import pyplot as plt

db = couchdb.Server('http://***REMOVED***@115.146.87.112:5984/')['processed_tweet_db']

def get_no_docs_in_view(db,view_name):
	res = db.view(view_name,reduce=True)
	return res.rows[0].value

def get_list_of_tweets(db,view_name):
	tweets = []
	for row in db.view(view_name,reduce=False):
		tweets.append(row.key)
	return tweets

def run():
	tweets = get_list_of_tweets(db,'_design/community-langs/_view/new-view')

	lang = {}
	for t in tweets:
		if t['community_lang'] not in lang:
			lang[t['community_lang']] = {'scores':[t['polarity']]}
		else:
			lang[t['community_lang']]['scores'].append(t['polarity'])

	for key in lang.keys():
		lang[key]['pos'] = 0
		lang[key]['neg'] = 0
		for score in lang[key]['scores']:
			if score >= 0.25:
				lang[key]['pos'] += 1
			elif score <= -0.25:
				lang[key]['neg'] += 1
		lang[key]['total'] = len(lang[key]['scores'])
		lang[key]['mean_score'] = sum(lang[key]['scores'])/float(len(lang[key]['scores']))
		del lang[key]['scores']
	
	if 'Select Language...' in lang:
		del lang['Select Language...']
	print 'language,mean score,positive,negative,total'
	for key in lang.keys():
		print '{},{},{},{},{}'.format(
			key,lang[key]['mean_score'],lang[key]['pos'],lang[key]['neg'],lang[key]['total']
		)
	return json.dumps(lang)

if __name__ == '__main__':
	print run()
