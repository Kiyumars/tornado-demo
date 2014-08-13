import logging
import random
import json
import urllib2
import sys

import tornado.ioloop
import tornado.web
import tornado.autoreload

from rottentomatoes import RT
import imdb

imd = imdb.IMDb()
rt = RT()
MOVIE_LIST = None
# PLAYERS = {}
PLAYER = ""

def get_released_movies(actor):
	"""only include movies before current year, to exclude unreleased films"""
	movie_list = []
	for movie in actor['actor']:
		try:
			if movie['year'] >= 2014:
				continue
			else:
				movie_list.append(movie)
		#some movies don't have year values. Perhaps find another way to handle error
		except KeyError:
			continue

	return movie_list


def get_one_movie():
	"""Pick movie for the coming round if movie has reviews"""
	movie_choice = MOVIE_LIST.pop(random.randrange(len(MOVIE_LIST)))
	has_reviews = reviews_exist(movie_choice.movieID)
	
	if not has_reviews:
		get_one_movie()
	else:
		update_movie_info(movie_choice)
		movie_info = start_new_round(movie_choice)
		print "get_one_movie function, movie_info is: "
		print movie_info
		return movie_info


def reviews_exist(movieID):
	"""remove movies that have no reviews or just one positive review on RT.com"""
	critics, audience = request_rt_ratings(movieID)
	if critics < 0 or critics == 100 or not critics:
		return False
	else:
		return True


def start_new_round(movie_choice):
	critics, audience = request_rt_ratings(movie_choice.movieID)
	movie_info = print_movie_info(movie_choice, critics, audience)
	print "In start_new_round function, movie_info is "
	print movie_info

	return movie_info
	# get_and_calc_player_guesses(critics, movie_choice)

	#only start bonus round if critics score and audience score differ, otherwise
	#update player scores and ask to start a new round.
	# if critics != audience:	
	# 	start_bonus_round(critics, audience)	
	# elif critics == audience:
	# 	for player in player_scores:
	# 		player_scores[player] += player_guesses[player]
	# 		print player_names[player] + " now has a total score of " + str(player_scores[player]) + " points.\n"
	# 		want_another_round()
	# else:
	# 	print "Something went wrong with the start_bonus_round function."


def update_movie_info(movie):
	imd.update(movie)


def request_rt_ratings(movieID):
	"""send a json request to RT.com for the movie's ratings scores"""
	key= '5wzpmvz79dzzj8g5exucf8qv'
	url_string = "http://api.rottentomatoes.com/api/public/v1.0/movie_alias.json?apikey=" + key + "&type=imdb&id=" + movieID
	
	json_data = json.load(urllib2.urlopen(url_string))
	critics, audience = parse_json(json_data)

	return critics, audience


def parse_json(json_data):
	"""parse json from RT.com's response if it has ratings scores"""
	if 'ratings' in json_data:
		critics_score = json_data['ratings']['critics_score']
		audience_score = json_data['ratings']['audience_score']
		return critics_score, audience_score
	else:
		return False, False


def print_movie_info(movie, critics_score, audience_score):
	possible_info = ['title', 'year', 'plot outline','full-size cover url']
	game_content_html = ''

	for movie_key in possible_info:
		if movie_key in movie.keys():
			info_html = str(movie_key) + ": " + str(movie[movie_key]) + "<br>"
			game_content_html += info_html
	print game_content_html
	
	critics_html = "Critics Rating: " + str(critics_score) + " <br>"
	audience_html = "Audience Rating: " + str(audience_score) + " <br>"
	game_content_html += critics_html
	game_content_html += audience_html
	
	print "In print_movie_info, game_content_html is "
	print game_content_html
	return game_content_html


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("home.html", title='title',  movie_info=[], player_name='')

	def post(self):
		global MOVIE_LIST
		player_name = self.get_argument('player_name')
		print player_name
		movie_info = get_one_movie()

		print "Something is happening here: "
		print movie_info
		print type(movie_info)
		# import pdb; pdb.set_trace()
		self.render("home.html", title='title',  movie_info=movie_info, player_name=player_name)


class ActorHandler(tornado.web.RequestHandler):
	def post(self):
		global MOVIE_LIST
		actor_name = self.get_argument('actorName')
		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)
		MOVIE_LIST = get_released_movies(actor_object)
		print "Finished movie list"


application = tornado.web.Application([
										(r"/", MainHandler),
										(r"/getactor", ActorHandler),
										],
										static_path="static")

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.autoreload.watch('home.html')
	# tornado.autoreload.watch('static/home.js')
	tornado.ioloop.IOLoop.instance().start()
