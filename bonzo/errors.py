
class SMTPError(Exception):

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

    def __init__(self):
        super(InternalConfusion, self).__init__(451, 'Internal confusion')


class UnrecognisedCommand(SMTPError):

    def __init__(self):
        super(UnrecognisedCommand, self).__init__(500, 'Error: bad syntax')


class BadArguments(SMTPError):

    def __init__(self, syntax):
        super(BadArguments, self).__init__(501, 'Syntax: %s' % syntax)


class NotImplementedCommand(SMTPError):

    def __init__(self, command):
        message = 'Error: command "%s" not implemented' % command
        super(NotImplementedCommand, self).__init__(502, message)


class BadSequence(SMTPError):

    def __init__(self, message):
        super(BadSequence, self).__init__(503, message)
