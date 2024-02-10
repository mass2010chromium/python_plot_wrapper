import rpyc

class WrapperService(rpyc.Service):
    """
    RPyC service that simply forwards all calls to an object.
    Useful for "objects" that have APIs, like python modules.
    """

    def __init__(self, wrap_obj, server_ptr):
        """
        Parameters:
        -------------------
        wrap_obj:       Object              Object that will handle all rpyc calls.

        server_ptr:     List[rpyc.Server]   Server that runs this service.
                                            Janky implementation detail is that it's a singleton
                                            list instead, because the server is not initialized
                                            when the service is constructed, and the object
                                            is passed back in later.
        """
        self.wrap_obj = wrap_obj
        self.server_ptr = server_ptr

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass

    def exposed_stop(self):
        self.server_ptr[0].close()

    def _rpyc_getattr(self, name):
        if name == "stop":
            return self.exposed_stop
        return getattr(self.wrap_obj, name)

