from unittest import result
from flask import Flask, g, request
from elasticsearch import Elasticsearch
import os
import time
from google_play_scraper import reviews, Sort
from app_store_scraper import AppStore
from datetime import datetime, timedelta
import play_scraper

es = Elasticsearch(['https://search-appreviews-analytics-sqvmnsmyuymtg4iielcvmisngy.ap-south-1.es.amazonaws.com'],http_auth=('elastic', 'tiw0nAfK2I+ahLxc89Dx'))

def prefix_route(route_function, prefix='', mask='{0}{1}'):
	'''
		Defines a new route function with a prefix.
		The mask argument is a `format string` formatted with, in that order:
		prefix, route
	'''
	def newroute(route, *args, **kwargs):
		'''New function to prefix the route'''
		return route_function(mask.format(prefix, route), *args, **kwargs)
	return newroute

app = Flask(__name__)
app.route = prefix_route(app.route, '/apps')
port = int(os.environ.get('PORT', 33507))
print(app)
FETCH_LIMIT = 1000

@app.before_request
def before_request():
	g.start = time.time()

@app.after_request
def after_request(response):
	diff = time.time() - g.start
	print("Response time", diff)
	return response

@app.route("/")
def hello():
	return "Server's Up!"

@app.route("/<platform>/<app_id>/get_reviews")
def search(platform,app_id):
	reviews_list = []
	def recursive_fetch_ps_reviews(reviews_list, continuation_token=None):
		print(reviews_list)
		result, continuation_token = reviews(
			app_id,
			lang='en',
			country = country,
			sort = Sort.NEWEST,
			count=150,
			continuation_token=continuation_token
		)
		reviews_list.extend(result)
		print(reviews_list)
		last_review = reviews_list[-1]
		if last_review['at']<=req_date:
			return
		recursive_fetch_ps_reviews(reviews_list,continuation_token)

	days = request.args.get('days') or 5
	country = request.args.get('country') or 'us'
	today = datetime.today()
	req_date = today - timedelta(days=days)
	if platform == 'ios':
		print(country)
		my_app = AppStore(
			country=country,        # required, 2-letter code
			app_name=app_id, # required, found in app's url
			#app_id=989540920    # technically not required, found in app's url
			)
		my_app.review(
			after=req_date
		)
		print(my_app.reviews)
		reviews_list = my_app.reviews
	elif platform == 'android':
		recursive_fetch_ps_reviews(reviews_list)

	return {"count":len(reviews_list),"reviews": reviews_list}

@app.route("/<platform>/<appId>/index_reviews")
def index_reviews(platform,appId):
	query_params = request.args
	days_required = query_params.get("daysRequired")
	if not days_required:
		days_required = 5
	
	return query_params

# @app.route("/search/<platform>/<name>")
# def search_apps(platform, name):
# 	  if(platform == "android"):
#       	play_scraper.search()

if __name__ == "__main__":
	  app.run(debug=True,port=port)
