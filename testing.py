import tornado.ioloop
import tornado.web
import tornado.autoreload

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		player_numbers = range(1,9)
		self.render("template.html", title='title', player_numbers=player_numbers)
			


application = tornado.web.Application([(r"/", MainHandler),])

if __name__ == "__main__":
	application.listen(8888)
	tornado.autoreload.start()
	tornado.autoreload.watch('template.html')
	tornado.ioloop.IOLoop.instance().start()
