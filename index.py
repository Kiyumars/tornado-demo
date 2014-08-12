import logging

import tornado.ioloop
import tornado.web
import tornado.autoreload

from rottentomatoes import RT
import imdb

imd = imdb.IMDb()
rt = RT()
MOVIE_LIST = None
# PLAYERS = {}
PLAYER = None

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
	movie_choice = filmography.pop(random.randrange(len(filmography)))
	has_reviews = reviews_exist(movie_choice.movieID)
	
	if not has_reviews:
		get_one_movie()
	else:
		update_movie_info(movie_choice)
		start_new_round(movie_choice)


def reviews_exist(movieID):
	"""remove movies that have no reviews or just one positive review on RT.com"""
	critics, audience = request_rt_ratings(movieID)
	if critics < 0 or critics == 100 or not critics:
		return False
	else:
		return True


def start_new_round(movie_choice):
	critics, audience = request_rt_ratings(movie_choice.movieID)
	
	print_movie_info(movie_choice)
	get_and_calc_player_guesses(critics, movie_choice)

	#only start bonus round if critics score and audience score differ, otherwise
	#update player scores and ask to start a new round.
	if critics != audience:	
		start_bonus_round(critics, audience)	
	elif critics == audience:
		for player in player_scores:
			player_scores[player] += player_guesses[player]
			print player_names[player] + " now has a total score of " + str(player_scores[player]) + " points.\n"
			want_another_round()
	else:
		print "Something went wrong with the start_bonus_round function."


class MainHandler(tornado.web.RequestHandler):
	def get(self):

		self.render("home.html", title='title',  movie_info=[])

	def post(self):
		player_name = self.get_argument('player_name')
		print player_name
		global MOVIE_LIST
		movie_info = []
		for movie in MOVIE_LIST:
			movie_info.append(str(movie['title']))
		print movie_info
		# import pdb; pdb.set_trace()
		self.render("home.html", title='title',  movie_info=movie_info )


class SurpriseHandler(tornado.web.RequestHandler):
	def get(self):
		pic = 'http://i.imgur.com/THnYk7c.jpg'
		pic_href = "<img src='" + pic + "'>"
		self.write(pic_href)


class ActorHandler(tornado.web.RequestHandler):
	def post(self):
		global MOVIE_LIST
		actor_name = self.get_argument('actorName')
		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)
		MOVIE_LIST = get_released_movies(actor_object)
		print "Finished movie list"
		# ACTOR = actor_object
		# print actor_object['name']

		# self.write(actor_object['mini biography'][0])



class PlayerHandler(tornado.web.RequestHandler):
	def post(self):
		# global PLAYERS
		# player_dict = self.get_argument('player_names')
		# for i in range(len(player_dict)):
		# 	player_index = 'Player' + str(i + 1 )
		# 	PLAYERS[player_index] = player_dict[player_index]
		global PLAYER
		PLAYER = self.get_argument('player_name')
		print PLAYER


class GameHandler(tornado.web.RequestHandler):
	def get(self):
		player_name = self.get_argument('player1')
		self.render("game_round.html", player=player_name)



class MovieHandler(tornado.web.RequestHandler):
	pass
	

application = tornado.web.Application([
										(r"/", MainHandler),
										(r"/surprise", SurpriseHandler),
										(r"/getactor", ActorHandler),
										(r"/game", GameHandler),
										(r"/getplayer", PlayerHandler),
										(r"/movie", MovieHandler)
										],
										static_path="static")

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.autoreload.watch('home.html')
	tornado.ioloop.IOLoop.instance().start()
