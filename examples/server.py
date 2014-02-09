# -*- coding: utf-8 -*-
import sys
sys.path = ['..'] + sys.path

from tornado.ioloop import IOLoop
from bonzo.server import SMTPServer


def receive_message(message):
    print(message)


if __name__ == '__main__':
    SMTPServer(receive_message).listen(2525)
    IOLoop.current().start()
