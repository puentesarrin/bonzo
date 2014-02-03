
from tornado.testing import AsyncTestCase, bind_unused_port
from bonzo.smtpserver import SMTPServer


class AsyncSMTPTestCase(AsyncTestCase):
    """A test case that starts up an SMTP server.

    Subclasses must override ``get_request_callback()`, which returns a
    `.SMTPServer` callback to be tested.
    """

    def setUp(self):
        super(AsyncSMTPTestCase, self).setUp()
        sock, port = bind_unused_port()
        self.__port = port

        self._request_callback = self.get_request_callback()
        self.smtp_server = self.get_smtp_server()
        self.smtp_server.add_sockets([sock])

    def get_smtp_server(self):
        return SMTPServer(self._request_callback, io_loop=self.io_loop,
                          **self.get_smtpserver_options())

    def get_request_callback(self):
        """Should be overrridden by subclasses to return a `.SMTPServer`
        callback.
        """
        raise NotImplementedError()

    def get_smtpserver_options(self):
        """May be overridden by subclasses to return additional keyword
        arguments for the server.
        """
        return {}

    def get_smtp_port(self):
        """Returns the port used by the server.

        A new port is chosen for each test.
        """
        return self.__port

    def tearDown(self):
        self.smtp_server.stop()
        super(AsyncSMTPTestCase, self).tearDown()
