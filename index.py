import logging

import tornado.ioloop
import tornado.web
import tornado.autoreload

from rottentomatoes import RT
import imdb

imd = imdb.IMDb()
rt = RT()
ACTOR = None
# PLAYERS = {}
PLAYER = None


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		player_numbers = range(1,9)
		self.render("home.html", title='title', player_numbers=player_numbers)


class SurpriseHandler(tornado.web.RequestHandler):
	def get(self):
		pic = 'http://i.imgur.com/THnYk7c.jpg'
		pic_href = "<img src='" + pic + "'>"
		self.write(pic_href)


class ActorHandler(tornado.web.RequestHandler):
	def post(self):
		global ACTOR
		actor_name = self.get_argument('actorName')
		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)
		ACTOR = actor_object
		print actor_object['name']

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
	def get(self):
		movie_title = self.get_argument()
		movie_search = rt.feeling_lucky(movie_title)
	

application = tornado.web.Application([
										(r"/", MainHandler),
										(r"/surprise", SurpriseHandler),
										(r"/getactor", ActorHandler),
										(r"/game", GameHandler),
										(r"/getplayer", PlayerHandler)
										],
										static_path="static")

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.autoreload.watch('home.html')
	tornado.ioloop.IOLoop.instance().start()
