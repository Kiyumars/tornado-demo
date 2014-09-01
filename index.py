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


class GameHandler(tornado.web.RequestHandler):
	def get(self):
		players = create_player_dict(self.get_argument('players'))
		game_id = start_game_session(players)

		actor_name = self.get_argument('actor_entered')
		Actor = get_actor_object_from_imdb(actor_name)
		enter_actor_in_actors_db(Actor)

		movie_available = return_appropriate_movie(actor_or_actress(Actor))
		if not movie_available:
			print "No more movies available from that actor. Exiting the game. Please play again soon, but choose a more prolific actor."
		movie, critics_score, audience_score = movie_available

		enter_movie_in_actors_db(movie, Actor.personID, critics_score, audience_score)
		push_ratings_scores_in_game_db(game_id, critics_score, audience_score)
		movie_list = actor_or_actress(Actor)
		tornado.ioloop.IOLoop.instance().call_later(0, enter_all_movies_in_both_dbases, 
										movie_list, Actor.personID,
										 game_id)

		#enter all movies in both databases in an asynchronous loop

		self.render("game_round.html", title='title', 
					movie=movie, critics_score=critics_score, audience_score=audience_score,
					players=players, game_id=game_id)


	def post(self):
		pass

# class TestHandler(tornado.web.RequestHandler):
# 	def get(self):
# 		print "We are in TestHandler"
# 		try:
# 			actor_name = self.get_argument('actor_entered')
# 			print actor_name
# 			players_entry = self.get_argument('players')
# 			print players_entry
# 			players_list = players_entry.split(',')
# 			# players = {"Philip": 0, "Michael": 0}
# 			players = {}
# 		except:
# 			self.redirect("/")
# 		for player in players_list:
# 			players[player.strip()] = 0
# 		print players


# 		game_id = db.game_input.insert({"Players": players, "Actor": actor_name})
# 		print game_id
# 		self.render("game_test.html", actor_name=actor_name, players=players, game_id=game_id)


# class ScoreHandler(tornado.web.RequestHandler):
# 	def get(self):
# 		print "We are in ScoreHandler"
# 		try:
# 			game_id = self.get_argument("game_id")
# 		except:
# 			self.redirect("/")
# 		print game_id
# 		game_entry = db.game_input.find({"_id": ObjectId(game_id)})
# 		players = game_entry[0]["Players"]
# 		for player in players:
# 			players[player] += int(self.get_argument(player))
# 		print players

# 		print db.game_input.update({"_id": ObjectId(game_id)}, {"Players": players})
# 		self.render("score_update.html", players=players, game_id=game_id)


def get_actor_object_from_imdb(actor_name):
	actor_object = imd.search_person(actor_name)[0]
	imd.update(actor_object)
	
	return actor_object


def start_game_session(players):
	player_guesses = {}
	for player in players:
		player_guesses[player] = 0
	game_id = db.game_sessions.insert({
										"Player scores": players,
										"Player guesses": player_guesses 
										})

	return game_id


def push_ratings_scores_in_game_db(game_id, critics_score, audience_score):

	db.game_sessions.update({"_id": game_id}, { "$set":  {"Critics": critics_score,
												"Audience": audience_score} 
												})


def create_player_dict(players_str):
	players_list = players_str.split(',')
	players = {}
	# players = {"Philip": 0, "Michael": 0}
	for player in players_list:
		players[player.strip()] = 0

	return players


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



def enter_game_session_info_in_game_db(critics_score, audience_score, players):
	player_guesses = {}
	for player in players:
		player_guesses[player] = 0

	game_id = db.game_sessions.insert({"Player scores": players, 
										"Critics": critics_score, 
										"Audience": audience_score, 
										"Player guesses": player_guesses,
										"Movies": []
										})

	return game_id



def actor_or_actress(actor):
	print "We are in actor_or_actress."
	if 'actor' in actor.keys():
		return actor['actor']
	else:
		return actor['actress']


def pick_random_movie_object(movie_list):
	return movie_list.pop(random.randrange(len(movie_list) - 1 ) )


def return_appropriate_movie(movie_list):
	print "We are in return_appropriate_movie"

	useful = False
	while not useful and len(movie_list) > 0:
		movie = pick_random_movie_object(movie_list)

		if not movie_has_relevant_keys(movie):
			continue
		has_reviews = check_for_rt_reviews(movie.movieID)
		if not has_reviews:
			continue
		critics_score, audience_score, rt_id = has_reviews
		if not has_more_than_five_reviews(rt_id):
			continue
		useful = True
	
	if not useful:
		return False
	print "We are returning a movie."
	print movie
	return movie, critics_score, audience_score


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

		return critics_score, audience_score, rt_movie_id
	else:
		return False


def has_more_than_five_reviews(movie_id):
	total_reviews = request_number_of_rt_reviews(movie_id)
	if total_reviews < 6:
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
	return json_data['total']


def enter_actor_in_actors_db(actor):
	
	split_name = actor['canonical name'].split(",")

	db.actors.insert({
					"IMDb PersonID": actor.personID, 
					"Last Name": split_name[0].strip(),
					"First Name": split_name[1].strip(),
					# "Birth year": actor['birth date'],
					# "Biography": actor['bio'],
					"Movies": []

					})

def enter_movie_in_actors_db(movie, actor_id, critics_score, audience_score):

	movie_dict = prepare_movie_dict_entry(movie, critics_score, audience_score)

	db.actors.update({"IMDb PersonID": actor_id}, { "$push": {"Movies": movie_dict}})

	print "Entered one movie of this actor/actress."


def enter_all_movies_in_both_dbases(movie_list, actor_id, game_id):
	print "In enter_all_movies_in_both_dbases"
	if len(movie_list) > 0:
		movie, critics_score, audience_score  = return_appropriate_movie(movie_list)
		enter_movie_in_actors_db(movie, actor_id, critics_score, audience_score)
		enter_movie_into_game_db(movie, game_id, critics_score, audience_score)
		print "Entered one movie in both dbases."
		tornado.ioloop.IOLoop.instance().call_later(0, enter_all_movies_in_both_dbases, 
													movie_list, actor_id,
										 			game_id)
	else:
		print "Finished enter_all_movies_in_both_dbases"



def enter_movie_into_game_db(movie, game_id, 
								critics_score, audience_score):
	movie_dict = prepare_movie_dict_entry(movie, critics_score, audience_score)
	db.game_sessions.update({"_id": game_id}, {"$push": {"Movies": movie_dict}})


def prepare_movie_dict_entry(movie, critics_score, audience_score):
	movie_dict = {'Title': movie['title'], 
					'Year': movie['year'],
		 			'Director': str(movie['director'][0]['name']),
		 			'Plot Outline': movie['plot outline'],
		 			'Plot': movie['plot'],
		 			'Poster': movie['full-size cover url'],
		 			"Critics": critics_score,
		 			"Audience": audience_score  
		 			}

	cast = []
	for i in range(len(movie['cast'])):
		cast.append(movie['cast'][i]['name'])
	movie_dict['Cast'] = cast

	return movie_dict


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
										# (r"/game_test", TestHandler),
										# (r"/score_update", ScoreHandler)
										# (r"/nextround", RoundHandler)
										],
										static_path="static",
										debug=True)

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.ioloop.IOLoop.instance().start()
