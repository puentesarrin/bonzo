# -*- coding: utf-8 -*-
import sys
sys.path = ['..'] + sys.path

import tornado.ioloop
import bonzo.server


def handle_request(request):
    print(request)
    request.finish()

if __name__ == '__main__':
    smtp_server = bonzo.server.SMTPServer(handle_request)
    smtp_server.listen(2525)
    tornado.ioloop.IOLoop.current().start()
