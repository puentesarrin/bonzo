# -*- coding: utf-8 -*-
import tornado.ioloop
import email

import sys
sys.path = ['..'] + sys.path

from bonzo.smtpserver import SMTPServer


def receive_message(message):
    print "New received message: "
    print "From: " + message['from']
    print "Subject: " + message['subject']
    for line in email.iterators.body_line_iterator(message):
        print line


if __name__ == '__main__':
    SMTPServer(receive_message).listen(2525)
    tornado.ioloop.IOLoop.instance().start()
