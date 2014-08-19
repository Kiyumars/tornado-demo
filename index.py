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
from pymongo import MongoClient

imd = imdb.IMDb()
rt = RT()
client = MongoClient()
db = client.mydb

MOVIE_LIST = None
# PLAYERS = {}
PLAYER = ""

def get_released_movies(actor):
	"""only include movies before current year, to exclude unreleased films"""
	movie_list = []
	
	try:
		for movie in actor['actor']:			
			if 'year' not in movie.keys() or movie['year'] >= 2014:
				continue
			else:
				movie_list.append(movie)
			#some movies don't have year values. Perhaps find another way to handle error
	except KeyError:
		for movie in actor['actress']:
			if 'year' not in movie.keys() or movie['year'] >= 2014:
					continue
			else:
				movie_list.append(movie)


	return movie_list


def get_one_movie():
	"""Pick movie for the coming round if movie has reviews"""
	# global MOVIE_LIST
	movie_choice = MOVIE_LIST.pop(random.randrange(len(MOVIE_LIST)))
	has_reviews, critics, audience = reviews_exist(movie_choice.movieID)
	
	if not has_reviews:
		return get_one_movie()
	else:
		update_movie_info(movie_choice)
		return movie_choice, critics, audience


def reviews_exist(movieID):
	"""remove movies that have no reviews or just one positive review on RT.com"""
	critics, audience = request_rt_ratings(movieID)
	if critics < 0 or critics == 100 or not critics:
		return False, False, False
	else:
		return True, critics, audience


def start_new_round(movie_choice):
	critics, audience = request_rt_ratings(movie_choice.movieID)
	movie_info = print_movie_info(movie_choice, critics, audience)

	return movie_info


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



class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("home.html", title='title',  movie=None, critics_score=None, audience_score=None )

	def post(self):
		global MOVIE_LIST
		actor_name = self.get_argument('actorName')
		actor_in_db(actor_name)

		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)

		MOVIE_LIST = get_released_movies(actor_object)
		movie, critics_score, audience_score = get_one_movie()

		self.render("game_round.html", title='title',  movie=movie, critics_score=critics_score, audience_score= audience_score)


def actor_in_db(actor_name):
	split_name = actor_name.split(' ')
	print split_name
	actor_query = db.actors.find({'Last Name': str(split_name[1])}, {'IMDb PersonID': 1, '_id': 0})
	print actor_query[0]['IMDb PersonID']



class ActorHandler(tornado.web.RequestHandler):
	def post(self):
		global MOVIE_LIST
		actor_name = self.get_argument('actorName')
		actor_in_db(actor_name)

		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)
		MOVIE_LIST = get_released_movies(actor_object)
	


class RoundHandler(tornado.web.RequestHandler):
	def post(self):
		movie, critics_score, audience_score = get_one_movie()
		self.render("game_round.html", title='title', movie=movie, critics_score=critics_score, audience_score= audience_score)


class MovieObject():
	def __init__(self, MovieID, title, year, director, cast, plot_outline, plot, critics_score, audience_score):
		self.MovieID = MovieID
		self.title = title
		self.year = year
		self.director = director
		self.cast = cast
		self.plot_outline = plot_outline
		self.plot = plot
		self.critics_score = critics_score
		self.audience_score = audience_score


class ActorObject():
	def __init__(self, PersonID, lname, fname, birth):
		self.PersonID = PersonID
		self.lname = lname
		self.fname = fname
		self.birth = birth
		# self.filmography = filmography
		# self.death = death
		# self.bio = bio


def test_save_actorObject(actor):
	split_name = actor['canonical name'].split(",")
	db.actors.insert({
						"IMDb PersonID": actor.personID, 
						"Last Name": split_name[0],
						"First Name": split_name[1],
						"Birth year": actor['birth date']

						})


application = tornado.web.Application([
										(r"/", MainHandler),
										(r"/getactor", ActorHandler),
										(r"/nextround", RoundHandler)
										],
										static_path="static",
										autoreload=True)

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.ioloop.IOLoop.instance().start()
