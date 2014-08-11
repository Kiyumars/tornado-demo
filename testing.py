import tornado.ioloop
import tornado.web
import tornado.autoreload

from rottentomatoes import RT
import imdb

imd = imdb.IMDb()
rt = RT()


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		player_numbers = range(1,9)
		self.render("template.html", title='title', player_numbers=player_numbers)


class SurpriseHandler(tornado.web.RequestHandler):
	def get(self):
		pic = 'http://i.imgur.com/THnYk7c.jpg'
		pic_href = "<img src='" + pic + "'>"
		self.write(pic_href)


class ActorHandler(tornado.web.RequestHandler):
	def get(self):
		actor_name = self.get_argument('actorName')
		actor_object = imd.search_person(actor_name)[0]
		imd.update(actor_object)
		self.write(actor_object['mini biography'][0])


class MovieHandler(tornado.web.RequestHandler):
	def get(self):
		movie_title = self.get_argument()
		movie_search = rt.feeling_lucky(movie_title)

application = tornado.web.Application([(r"/", MainHandler),
										(r"/surprise", SurpriseHandler),
										(r"/getactor", ActorHandler)])

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.autoreload.watch('template.html')
	tornado.ioloop.IOLoop.instance().start()
