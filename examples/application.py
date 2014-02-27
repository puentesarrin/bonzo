# -*- coding: utf-8 -*-
import sys
sys.path = ['..'] + sys.path

import tornado.ioloop
import bonzo.smtp


class Handler(bonzo.smtp.RequestHandler):

    def data(self):
        print(self.request)


if __name__ == '__main__':
    application = bonzo.smtp.Application(Handler)
    application.listen(2525)
    tornado.ioloop.IOLoop.current().start()
