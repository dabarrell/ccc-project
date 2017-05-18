#  COMP90024 Project - Team 33
#  David Barrell (520704), Bobby Koteski (696567), Steve Dang (807773)

import couchdb, sys, json
import collections

db = couchdb.Server('http://***REMOVED***@115.146.93.170:5984/')['tweet_all10gb']

def get_no_docs_in_view(db,view_name):
	res = db.view(view_name,reduce=True)
	return res.rows[0].value

def get_list_of_tweets(db,view_name):
	tweets = []
	for row in db.view(view_name,reduce=False):
		tweets.append(row.key)
	return tweets

def run():
	views = {
		'deakin_uni':None,
		'latrobe_uni':None,
		'melb_uni':None,
		'monash_caulfield':None,
		'monash_uni':None,
		'rmit':None,
		'swinburne_uni':None,
		'vic_uni':None
	}

	for view in views.keys():
		view_format = '_design/{}/_view/new-view'.format(
			view
		)
		tweet_count = get_no_docs_in_view(db,view_format)
		views[view] = {'tweet_count':tweet_count}
		views[view]['full_view_name'] = view_format

	for key in views.keys():
		tmp_tweets = get_list_of_tweets(db,
			views[key]['full_view_name']
		)
		views[key]['tweets'] = tmp_tweets
		# print key, views[key]['tweet_count'], len(tmp_tweets)
	# merge monash
	# print views['monash_caulfield'].keys()
	views['monash_uni']['tweets'] += views['monash_caulfield']['tweets']
	views['monash_uni']['tweet_count'] += views['monash_caulfield']['tweet_count']
	del views['monash_caulfield']

	# count positive and negative tweets
	for key in views.keys():
		pos, neg, neutral = [], [], []
		for t in views[key]['tweets']:
			# print key, t['sentiment'], t['text']
			if t['sentiment'] >= 0.25:
				pos.append(t['sentiment'])
			elif t['sentiment'] <= -0.25:
				neg.append(t['sentiment'])
			else:
				neutral.append(t['sentiment'])
		views[key]['pos'] = pos
		views[key]['neg'] = neg
		views[key]['neutral'] = neutral
		print '{},{},{},{},{:0.2f},{:0.2f}'.format(
			key,
			len(views[key]['pos']),
			len(views[key]['neg']),
			views[key]['tweet_count'],
			len(views[key]['pos'])/float(views[key]['tweet_count']) * 100.0,
			len(views[key]['neg'])/float(views[key]['tweet_count']) * 100.0
		)

	# make a bar chart of pos unis
	pos = []
	neg = []
	uni = []
	for key in views.keys():
		uni.append(key)
		pos.append(
			len(views[key]['pos'])/float(views[key]['tweet_count']) * 100.0
		)
		neg.append(
			len(views[key]['neg'])/float(views[key]['tweet_count']) * 100.0
		)

	pos_sorted = [x for (x,y) in sorted(zip(pos,uni),reverse=True)]
	uni_sorted = [y for (x,y) in sorted(zip(pos,uni),reverse=True)]

	# import numpy as np
	# from matplotlib import pyplot as plt

	# fig = plt.figure(figsize=(15,10))
	# y_pos = np.arange(len(uni_sorted))
	# plt.bar(y_pos,pos_sorted)
	# plt.ylabel('Proportion of Positive Tweets')
	# plt.xlabel('University')
	# plt.xticks(y_pos,uni_sorted)
	# plt.title('Positivity at Unis')
	# fig.savefig('positive.png')

	neg_sorted = [x for (x,y) in sorted(zip(neg,uni),reverse=True)]
	uni_sorted = [y for (x,y) in sorted(zip(neg,uni),reverse=True)]

	# fig = plt.figure(figsize=(15,10))
	# y_pos = np.arange(len(uni_sorted))
	# plt.bar(y_pos,neg_sorted,color='r')
	# plt.ylabel('Proportion of Negative Tweets')
	# plt.xlabel('University')
	# plt.xticks(y_pos,uni_sorted)
	# plt.title('Negativity at Unis')
	# fig.savefig('negative.png')

	d = {
		'positive':{'unis':[y for (x,y) in sorted(zip(pos,uni),reverse=True)],
					'percent':pos_sorted},
		'negative':{'unis':[y for (x,y) in sorted(zip(neg,uni),reverse=True)],
					'percent':neg_sorted}
	}
	new_d = {}
	for key in d.keys():
		# print d[key]
		new_d[key] = []
		for x,y in zip(d[key]['unis'],d[key]['percent']):
			# print key,x,y
			new_d[key].append({x:y})

	# od = collections.OrderedDict(new_d)
	return json.dumps(new_d)

if __name__ == '__main__':
	print run()
