import urllib, urllib2
import json

def run_query(search_terms):

	# parameters for the search request
	root_url = 'https://www.googleapis.com/customsearch/v1'
	
	# API Key code.google.apis/...
	key = 'AIzaSyC_yIeKcGli66Q7XKkHtLNDQI_jKG_Y-jE'

	query = urllib.quote_plus(search_terms)
	
	# Unique Search Engine ID google.com/cse/manage/all
	cx = '005421112075098740461:hrjteff646o'
	# Construct the URL / search request
	search_url = "%s?key=%s&cx=%s&q=%s" % (root_url, key, cx,query )
	results = {'items':[]}
	try:
		response = urllib2.urlopen(search_url).read()
		# Convert the response to json and parse out the fields (title, url, and snippet)
		json_response = json.loads(response)
		results['total'] = json_response['queries']['request'][0]['totalResults']
		results['terms'] = search_terms
		rank = 1
		for item in json_response['items']:
			results['items'].append({'title':item['title'],'url':item['link'],'snippet':item['snippet'], 'rank':rank})
			rank += 1
	except urllib2.URLError, e:
		print "Error when querying Google Custom Search API", e

	return results