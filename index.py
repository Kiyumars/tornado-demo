import sys
import logging
import random
import json
import urllib2
from bson.objectid import ObjectId

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



class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("home.html", title='title',  movie=None, critics_score=None, audience_score=None )


class TestHandler(tornado.web.RequestHandler):
	def get(self):
		print "We are in TestHandler"
		try:
			actor_name = self.get_argument('actor_entered')
			print actor_name
			players_entry = self.get_argument('players')
			print players_entry
			players_list = players_entry.split(',')
			# players = {"Philip": 0, "Michael": 0}
			players = {}
		except:
			self.redirect("/")
		for player in players_list:
			players[player.strip()] = 0
		print players


		game_id = db.game_input.insert({"Players": players, "Actor": actor_name})
		print game_id
		self.render("game_test.html", actor_name=actor_name, players=players, game_id=game_id)


class ScoreHandler(tornado.web.RequestHandler):
	def get(self):
		print "We are in ScoreHandler"
		try:
			game_id = self.get_argument("game_id")
		except:
			self.redirect("/")
		print game_id
		game_entry = db.game_input.find({"_id": ObjectId(game_id)})
		players = game_entry[0]["Players"]
		for player in players:
			players[player] += int(self.get_argument(player))
		print players

		print db.game_input.update({"_id": ObjectId(game_id)}, {"Players": players})
		self.render("score_update.html", players=players, game_id=game_id)

class Game():
	def __init__(self):
		self.players = None
		self.movie_list = None

	def pop_movie_from_list(self):
		return self.movie_list.pop(random.randrange(len(self.movie_list)))

	def update_player_scores(self, score_update):
		for player in self.players:
			self.players[player] += score_update[player] 


class GameHandler(tornado.web.RequestHandler):
	def get(self):
		print "We are in GameHandler."
		actor_name = self.get_argument('actor_entered')
		print actor_name
		actor_object = get_actor_object_from_imdb(actor_name)
		print actor_object
		# actor_db_entry_id = enter_actor_in_caching_db(actor_object)
		# print actor_db_entry_id
		movie_available = return_appropriate_movie(actor_object)
		print movie_available
		if not movie_available:
			print "No more movies available from that actor. Exiting the game. Please play again soon, but choose a more prolific actor."
			sys.exit()
		movie, critics_score, audience_score = movie_available
		# actor_name = "Nicolas Cage"
		players_entry = self.get_argument('players')
		players_list = players_entry.split(',')
		players = {}
		# players = {"Philip": 0, "Michael": 0}
		for player in players_list:
			players[player.strip()] = 0

		print players
		
		self.render("game_round.html", title='title', 
					movie=movie, critics_score=critics_score, audience_score=audience_score)


	def post(self):
		pass

def get_actor_object_from_imdb(actor_name):
	actor_object = imd.search_person(actor_name)[0]
	imd.update(actor_object)
	
	return actor_object


def enter_actor_in_caching_db(actor_object):
	pass


def male_or_female(actor):
	print "We are in male_or_female"
	if actor['actor']:
		return actor['actor']
	else:
		return actor['actress']


def pick_random_movie_object(movie_list):
	return movie_list.pop(random.randrange(len(movie_list) - 1 ) )


def return_appropriate_movie(actor_object):
	print "We are in return_appropriate_movie"
	movie_list = male_or_female(actor_object)
	print movie_list

	if len(movie_list) < 1:
		return False

	useful = False
	while not useful:
		print "One round in the while loop of return_appropriate_movie"
		movie = pick_random_movie_object(movie_list)
		print movie['title']
		if not movie_has_relevant_keys(movie):
			continue
		print "We moved beyond movie_has_relevant_keys"
		has_reviews = check_for_rt_reviews(movie.movieID)
		print has_reviews
		if not has_reviews:
			continue
		critics_score, audience_score, rt_id = has_reviews
		if not has_more_than_five_reviews(rt_id):
			continue
		useful = True
	print "We are returning a movie. Hopefully"
	print movie
	return movie, critics_score, audience_score


def pop_movie(GameObject):
	cond = False
	while not cond:
		movie = GameObject.pop_movie_from_list()
		if before_1990(movie):
			print "Popped a movie before 1990"
			return movie
			cond = True
		else:
			print "Did not find movie before 1990"	


def before_1990(movie):
	if movie['year'] < 1990:
		return True
	else:
		return False

def movie_has_relevant_keys(movie):
	print "We are in movie_has_relevant_keys"
	if "year" not in movie.keys():
		return False
	update_movie_info(movie)
	print movie.keys()
	if not all(key in movie.keys() for key in ("director", "plot outline", "plot",
												 "cast", "full-size cover url")):
		print "Not all keys"
		return False
	else:
		print "Has all keys()"
		return True


def check_for_rt_reviews(movieID):
	"""remove movies that have no reviews"""
	print "We are in check_for_rt_reviews"
	result = request_rt_ratings(movieID)
	print result
	if not result:
		return False
	critics, audience, rt_movie_id = result
	if critics < 0 or not critics or not audience:
		return False
	elif not has_more_than_five_reviews(rt_movie_id):
		return False
	else:
		return critics, audience, rt_movie_id

def request_json_from_rt(movieID, request_type):
	"""send a json request to RT.com for the movie's ratings scores"""
	print "What is the request type? in request_json_from_rt"
	print request_type

	key= '5wzpmvz79dzzj8g5exucf8qv'
	if request_type == "movie_alias":
		print "movie_alias"
		url_string = "http://api.rottentomatoes.com/api/public/v1.0/" + request_type + ".json?apikey=" + key + "&type=imdb&id=" + movieID
		print url_string
	elif request_type == "reviews":
		print "reviews"
		url_string = "http://api.rottentomatoes.com/api/public/v1.0/movies/" + movieID +"/reviews.json?apikey=" + key
		print url_string
	else:
		print "something went wrong with request_json_from_rt"
		sys.exit()

	return json.load(urllib2.urlopen(url_string))


def request_rt_ratings(movieID):
	"""send a json request to RT.com for the movie's ratings scores"""
	json_data = request_json_from_rt(movieID, "movie_alias")
	
	return parse_json_for_scores(json_data)

def parse_json_for_scores(json_data):
	"""parse json from RT.com's response if it has ratings scores"""
	if 'ratings' in json_data:
		critics_score = json_data['ratings']['critics_score']
		audience_score = json_data['ratings']['audience_score']
		rt_movie_id = json_data['id']
		print "Print RT movie id"
		print rt_movie_id
		return critics_score, audience_score, rt_movie_id
	else:
		return False


def has_more_than_five_reviews(movie_id):
	total_reviews = request_number_of_rt_reviews(movie_id)
	if total_reviews < 5:
		return False
	else:
		return True

def request_number_of_rt_reviews(imdb_id):
	json_data = request_json_from_rt(str(imdb_id), "reviews")
	print "Printing JSON Data"
	print json_data

	print parse_json_for_total_reviews_number(json_data)
	return parse_json_for_total_reviews_number(json_data)

def parse_json_for_total_reviews_number(json_data):
	return int(json_data['total'])


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


def search_info_on_imdb(actor_name):
		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)
		return actor_object, get_released_movies(actor_object)
		# movie, critics_score, audience_score = get_one_movie()
		# return movie, critics_score, audience_score
		# return actor_object


def enter_actor_in_db(actor, movie_list):
	print str(len(movie_List)) + " movies in total to enter into database."
	split_name = actor['canonical name'].split(",")
	total_movie_dict = []

	for movie in movie_List:
		update_movie_info(movie)

		movie_dict = {'Title': movie['title'], 
						'Year': movie['year'],
			 			'Director': str(movie['director'][0]['name']),
			 			'Plot Outline': movie['plot outline'],
			 			'Plot': movie['plot'],
			 			# 'Poster': movie['full-size cover url']  
			 			}

		cast = ''
		for actor in movie['cast'][:5]:
			cast += actor['name'] + ", "
		movie_dict['Cast'] = cast
		total_movie_dict.append(movie_dict)
		print "Finished " + str(len(total_movie_dict)) + " of " + str(len(MOVIE_LIST)) + " movies."

	db.actors.insert({
						"IMDb PersonID": actor.personID, 
						"Last Name": split_name[0].strip(),
						"First Name": split_name[1].strip(),
						# "Birth year": actor['birth date'],
						# "Biography": actor['bio'],
						"Movies": total_movie_dict

						})
	print "Finished saving all of the movies from this actor/actress."


def search_movieIDs_on_mongodb(actor_id):
	# movie_info = []
	movie_ids = []

	movies_with_actor = db.movie_list.find({'PersonID': actor_id}, {'MovieID': 1, '_id': 0 })
	for entry in movies_with_actor:
		movie_ids.append(entry['MovieID'])

	return movie_ids

	# for movieID in movie_ids:
	# 	movie_entry = db.movie_list.find({'MovieID': movieID})
	# 	movie_info.append(movie_entry)


def actor_in_db(actor_name):
	actor_PersonID = False
	split_name = actor_name.split(' ')
	print split_name
	#remove count from number_actors_in_db
	number_actors_in_db = db.actors.find({ "$and": [{'Last Name': split_name [1].strip()},
													{'First Name': split_name[0].strip()} ] }).count() 
	print number_actors_in_db	
 	
 	if number_actors_in_db > 0:
 		return True
 		# actor_search = db.actors.find({'Last Name': str(split_name[1]), 
			# 								'First Name': str(split_name[0])} , 
			# 								{'PersonID': 1, '_id': 0})
 		# for actor in actor_search:
			# actor_personID = actor['PersonID']
 		# return True, actor_personID
 	else:
 		# return False, False
 		return False




class Movie():
	def __init__(self, MovieID):
		self.MovieID = MovieID
		
		entry_in_mongo = db.actors.find({'MovieID': self.movieID})
		for entry in entry_in_mongo:
			self.title = entry['Title']
			self.year = entry['Year']
			self.director = entry['Director']
			self.cast = entry['cast']
			self.plot_outline = entry['plot_outline']
			self.plot = entry['Plot']
			self.critics_score = entry['Critics Rating']
			self.audience_score = entry['Audience Rating']





def update_movie_info(movie):
	print "updating movie"
	return imd.update(movie)


def enter_filmography(actor_id, filmography, critics_score, audience_score):
	for movie in filmography:
		db.actor_filmography.insert({
									"actor_id": actor_id,
									"movie_id": movie['id']
									})
	for movie in filmography:
		if not movie_in_db():
			db.movie_id.insert({"IMDb id": movie.movieID,
								"title": movie["title"],
								"Release": movie['year'],
								"Plot outline": movie['plot outline'],
								"Full Plot": movie['plot'],
								"Poster": movie["full-size cover url"],
								"RT Critics Score": critics_score,
								"RT Audience Score": audience_score

								})


def enter_movies_in_db():
	for movie in MOVIE_LIST:
		db.movie_list.insert({'MovieID': movie.movieID,
								'Title': movie['title'],
								'Year': movie['year'],
								'Plot outline': movie['plot outline'],
								'Plot': movie['plot'],
								'Director': str(movie['director'][0]),
								'Poster': movie['full-size cover url']
								})



application = tornado.web.Application([
										(r"/", MainHandler),
										(r"/game", GameHandler),
										(r"/game_test", TestHandler),
										(r"/score_update", ScoreHandler)
										# (r"/nextround", RoundHandler)
										],
										static_path="static",
										debug=True)

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.ioloop.IOLoop.instance().start()
