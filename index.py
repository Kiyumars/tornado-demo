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



class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("home.html", title='title',  movie=None, critics_score=None, audience_score=None )


class TestHandler(tornado.web.RequestHandler):
	def post(self):
		print "We are in TestHandler"
		actor_name = self.get_argument('actor_entered')
		print actor_name
		players_entry = self.get_argument('players')
		print players_entry
		players_list = players_entry.split(',')
		# players = {"Philip": 0, "Michael": 0}
		players = {}
		for player in players_list:
			players[player.strip()] = 0
		print players

		game_id = db.game_input.insert({"Players": players, "Actor": actor_name})
		print game_id
		self.render("game_test.html", actor_name="actor_name", players=players, game_id=game_id)




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
		actor_name = self.get_argument('actor_entered')
		# actor_name = "Nicolas Cage"
		# players_entry = self.get_argument('players')
		# players_list = players_entry.split(',')
		players = {"Philip": 0, "Michael": 0}
		# for player in players_list:
		# 	players[player.strip()] = 0

		# print players
	
		game = Game(players)
		# actor_id = actor_in_db(actor_name)
		print game.players

		actorObject, game.movie_list = search_info_on_imdb(actor_name)
		print len(game.movie_list)
		movie = pop_movie(game)
		print len(game.movie_list)
		update_movie_info(movie)


		self.render("game_round.html", title='title', 
					movie=movie, critics_score=77, audience_score=42)
	# # critics_score, audience_score = self.get_one_movie()
	# # 		self.render("game_round.html", title='title',  movie=movie,
	# # 				 critics_score=critics_score, audience_score=audience_score)
	# # 		enter_actor_in_db(actorObject)

	def post(self):
		print len(game.movie_list)
		movie = pop_movie(game)
		print len(game.movie_list)
		self.render("game_round.html", title='title', movie=movie, 
					critics_score=None, audience_score=None)


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


def reviews_exist(movieID):
	"""remove movies that have no reviews or just one positive review on RT.com"""
	critics, audience = request_rt_ratings(movieID)
	if critics < 0 or critics == 100 or not critics:
		return False, False, False
	else:
		return True, critics, audience


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
										(r"/game_test", TestHandler)
										# (r"/nextround", RoundHandler)
										],
										static_path="static",
										debug=True)

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.ioloop.IOLoop.instance().start()
