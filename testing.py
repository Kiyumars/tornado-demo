import tornado.ioloop
import tornado.web
import tornado.autoreload

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		player_numbers = range(1,9)
		self.render("template.html", title='title', player_numbers=player_numbers)

class SurpriseHandler(tornado.web.RequestHandler):
	def get(self):
		pic = 'http://i.imgur.com/THnYk7c.jpg'
		pic_href = "<img src='" + pic + "'>"
		self.write(pic_href)			


application = tornado.web.Application([(r"/", MainHandler),
										(r"/surprise", SurpriseHandler)])

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.autoreload.watch('template.html')
	tornado.ioloop.IOLoop.instance().start()
