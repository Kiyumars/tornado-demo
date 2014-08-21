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

MOVIE_LIST = []
# PLAYERS = {}
PLAYER = ""


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("home.html", title='title',  movie=None, critics_score=None, audience_score=None )

	def post(self):
		global MOVIE_LIST
		actor_name = self.get_argument('actorName')
		print actor_name
		
		# actor_id = actor_in_db(actor_name)
		
		if actor_in_db(actor_name):
			print "Found actor in database. Yay."
			# movie_id_list = search_movieIDs_on_mongo(actor_id)
			# for movieID in movie_id_list:
			# 	global MOVIE_LIST
			# 	movieObject = Movie(MovieID)
			# 	MOVIE_LIST.append(movieObject)
			# movie= MOVIE_LIST.pop(random.randrange(len(MOVIE_LIST)))
			# critics_score = movie.critics_score
			# audience_score = movie.audience_score
			# self.render("game_round.html", title='title',  movie=movie,
			# 		 critics_score=critics_score, audience_score=audience_score)
		else:
			print "Didn't find actor in database. Booh"
			actorObject = search_info_on_imdb(actor_name)
			movie, critics_score, audience_score = get_one_movie()
			self.render("game_round.html", title='title',  movie=movie,
					 critics_score=critics_score, audience_score=audience_score)
			enter_actor_in_db(actorObject)

		# actor_object = imd.search_person(actor_name)[0]
		# imd.update(actor_object)

		# MOVIE_LIST = get_released_movies(actor_object)
		# movie, critics_score, audience_score = get_one_movie()



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


def search_info_on_imdb(actor_name):
	global MOVIE_LIST
	actor_object = imd.search_person(actor_name)[0]
	imd.update(actor_object)
	MOVIE_LIST = get_released_movies(actor_object)
	# movie, critics_score, audience_score = get_one_movie()
	# return movie, critics_score, audience_score
	return actor_object


def enter_actor_in_db(actor):
	global MOVIE_LIST
	print str(len(MOVIE_LIST)) + " movies in total to enter into database."
	split_name = actor['canonical name'].split(",")
	total_movie_dict = []

	for movie in MOVIE_LIST:
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
		total_movie_dict.append( movie_dict)
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


class Movie():
	def __init__(self, MovieID):
		self.MovieID = MovieID
		
		entry_in_mongo = db.movie_info.find({'MovieID': self.movieID})
		for entry in entry_in_mongo:
			self.title = entry['Title']
			self.year = entry['Year']
			self.director = entry['Director']
			self.cast = entry['cast']
			self.plot_outline = entry['plot_outline']
			self.plot = entry['Plot']
			self.critics_score = entry['Critics Rating']
			self.audience_score = entry['Audience Rating']


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
	# refactor this function, no globals
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



def movie_in_db(movieID):
	movie_found = db.movie_id.find_one({ "IMDb id": movieID })
	if movie_found:
		return True
	elif not movie_found:
		return False
	else:
		print "Something went wrong in function movie_in_db."


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
		self.render("game_round.html", title='title', movie=movie, 
					critics_score=critics_score, audience_score= audience_score)


class Actor():
	def __init__(self, PersonID, lname, fname, birth):
		self.PersonID = PersonID
		self.lname = lname
		self.fname = fname
		self.birth = birth
		# self.filmography = filmography
		# self.death = death
		# self.bio = bio




def enter_actor_filmography_in_db(actor_id):
	for movie in MOVIE_LIST:
		db.actor_filmography.insert({'PersonID': actor_id, "MovieID": movie.movieID})


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
										(r"/getactor", ActorHandler),
										(r"/nextround", RoundHandler)
										],
										static_path="static",
										debug=True)

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.ioloop.IOLoop.instance().start()
