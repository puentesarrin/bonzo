# -*- coding: utf-8 -*-
"""SMTP exceptions for response to the client."""


class SMTPError(Exception):
    """An exception that will turn into an SMTP error response.

    :arg int status_code: SMTP status code. For a status codes list, see:
        http://www.greenend.org.uk/rjk/tech/smtpreplies.html.
    :arg string message: Message to be written to the stream in order to
        response to the client.
    :arg string log_message: Message to be written to the log for this error.
        May contain ``%s``-style placeholders, which will be filled in with
        remaining positional parameters.
    """

    def __init__(self, status_code, message, log_message=None, *args):
        self.status_code = status_code
        self.message = message
        self.log_message = log_message
        self.args = args

    def __str__(self):
        message = 'SMTP %d: %s' % (self.status_code, self.message)
        if not self.log_message:
            return message
        return message + ' (' + (self.log_message % self.args) + ')'


class InternalConfusion(SMTPError):
    """Used to return a ``451`` status code.
    """

    def __init__(self):
        super(InternalConfusion, self).__init__(451, 'Internal confusion')


class UnrecognisedCommand(SMTPError):
    """Used to return a ``500`` status code.
    """

    def __init__(self):
        super(UnrecognisedCommand, self).__init__(500, 'Error: bad syntax')


class BadArguments(SMTPError):
    """Used to return a ``501`` status code.

    :arg string syntax: Syntax returned to the client.
    """

    def __init__(self, syntax):
        super(BadArguments, self).__init__(501, 'Syntax: %s' % syntax)


class NotImplementedCommand(SMTPError):
    """Used to return a ``502`` status code.

    :arg string command: Command not implemented for the server.
    """

    def __init__(self, command):
        message = 'Error: command "%s" not implemented' % command
        super(NotImplementedCommand, self).__init__(502, message)


class BadSequence(SMTPError):
    """Used to return a ``503`` status code.

    :arg string message: Message to be written to the stream and to response to
        the client.
    """

    def __init__(self, message):
        super(BadSequence, self).__init__(503, message)
