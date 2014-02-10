# -*- coding: utf-8 -*-
import sys
sys.path = ['..'] + sys.path

from tornado.ioloop import IOLoop
from bonzo.server import SMTPServer


def handle_request(request):
    print(request)
    request.finish() 

if __name__ == '__main__':
    SMTPServer(handle_request).listen(2525)
    IOLoop.current().start()
