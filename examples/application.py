# -*- coding: utf-8 -*-
import sys
sys.path = ['..'] + sys.path

import tornado.ioloop
import bonzo.mail


class Handler(bonzo.mail.RequestHandler):

    def data(self):
        print(self.request)


if __name__ == '__main__':
    application = bonzo.mail.Application(Handler)
    application.listen(2525)
    tornado.ioloop.IOLoop.current().start()
