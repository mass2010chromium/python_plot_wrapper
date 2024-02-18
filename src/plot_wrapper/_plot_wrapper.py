import multiprocessing as mp
import time

import numpy as np
import rpyc

class WrapperService(rpyc.Service):
    """RPyC service that simply forwards all calls to an object.
    Useful for "objects" that have APIs, like python modules.
    """

    def __init__(self, wrap_obj):
        """
        Parameters:
        -------------------
        wrap_obj:       Object              Object that will handle all rpyc calls.
        """
        self.wrap_obj = wrap_obj
        self.server = None

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass

    def vis_spin(self):
        """Update visualizer window here."""
        pass
    
    def exposed_stop(self):
        self.server.close()

    def _rpyc_getattr(self, name):
        if name == "stop":
            return self.exposed_stop
        return getattr(self.wrap_obj, name)

    def start_server(self, port_val):
        """Spin up the rpyc server.

        Parameters:
        ------------------------------
        port_val:   Shared memory that we need to report the server port back to.
        """
        # Default port = 0 means pick a port for me.
        server = rpyc.utils.server.OneShotServer(self)
        self.server = server

        # Communicate the assigned port back via shared memory.
        port_val.value = server.port

        # Copied from rpyc server implementation.
        # https://github.com/tomerfiliba-org/rpyc/blob/master/rpyc/utils/server.py#L258
        server._listen()
        server._register()
        try:
            while server.active:
                server.accept()
        except EOFError:
            pass  # server closed by another thread
        except KeyboardInterrupt:
            print("")
            server.logger.warning("keyboard interrupt!")
        finally:
            server.logger.info("server has terminated")
            server.close()


class AsyncWrapperService(WrapperService):
    """Extension of WrapperService that supports spinning in a loop
        while listening for server events.
    Useful for "objects" that should be handled asynchronously, like
        Open3D Visualizer windows or Matplotlib interactive sessions.
    """

    def __init__(self, wrap_obj, spin_func, spinrate=20):
        """
        Parameters:
        -------------------
        wrap_obj:       Object              Object that will handle all rpyc calls.

        spin_func:      callable()          Callback for updating visualizer.

        spinrate:       Float               FPS to spin at
        """
        super().__init__(wrap_obj)
        self.spin_func = spin_func
        self.dt = 1 / spinrate
        self.active = False

    def vis_spin(self):
        """Update visualizer window here."""
        self.spin_func()
    
    def spin(self, conn):
        """Listen for server events and update visualizer window in the same thread."""
        self.active = True
        while self.active:
            self.vis_spin()
            try:
                res = True
                while res:
                    res = conn.poll(timeout=self.dt)
            except EOFError:
                break

    def start_server(self, port_val):
        # Default port = 0 means pick a port for me.
        server = rpyc.utils.server.OneShotServer(self)
        self.server = server

        # Communicate the assigned port back via shared memory.
        port_val.value = server.port

        try:
            spin_server_singlethread(server, self.spin)
        finally:
            self.active = False


class ServiceHost:
    """Class that handles multiprocessing and server setup logic."""

    def create_wrapper_service(self, **kwargs):
        """Return a WrapperService (or AsyncWrapperService) customized to your visualizer.
        
        You should import the library here and do any setup needed.
        """
        return None

    def start(self, sleep_dt=1, **kwargs):
        """
        Spawn the o3d visualizer-running process. Uses rpyc to do communication.
        """
        self.__client = None
        def spawn_vis_wrapper(port_val):
            # Janky way to pass the server object to the service after it's created.
            error, vis_obj = self.create_wrapper_service()
            if error != 0:
                return error

            vis_obj.start_server(port_val)
            return 0

        # Set to nonzero when the child starts correctly. Set it back to zero as a termination signal.
        self.__port_val = mp.Value('i', 0)
        self.__server_proc = mp.Process(target=spawn_vis_wrapper, args=(self.__port_val,))
        self.__server_proc.start()
        while self.__port_val.value == 0:
            #print("Waiting for server to start...")
            time.sleep(sleep_dt)

        if self.__port_val.value == -1:
            # Import error. server did not start correctly
            return self.__server_proc.join()
        self.__client = rpyc.connect('localhost', self.__port_val.value, config={'allow_public_attrs' : True})
        return 0

    def stop(self):
        #print("Stopping server")
        if self.__client is not None:
            try:
                self.__client.root.stop()
            except EOFError:
                pass
        self.__server_proc.join()
        #print("Stopped server.")

    # Forward all calls to rpyc.
    def __getattr__(self, name):
        return getattr(self.__client.root, name)


    # Implement Python contextmanager ( with x as MatplotlibWrapper(): )
    def __enter__(self):
        self.start()
    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


def spin_server_singlethread(server, spin_callback):
    """Set up a socket server but allow a custom callback for the event loop.

    This lets us run server logic and vis logic in the same thread.
    """

    # Copied from rpyc server implementation.
    # https://github.com/tomerfiliba-org/rpyc/blob/master/rpyc/utils/server.py#L258
    import socket
    import errno
    from contextlib import closing
    from rpyc.lib.compat import poll, get_exc_errno
    from rpyc.core import SocketStream, Channel
    server._listen()
    server._register()
    try:
        # IMPLEMENT: server.accept()
        print("waiting for conn")
        while server.active:
            try:
                sock, addrinfo = server.listener.accept()
            except socket.timeout:
                pass
            except socket.error:
                ex = sys.exc_info()[1]
                if get_exc_errno(ex) in (errno.EINTR, errno,EAGAIN):
                    pass
                else:
                    raise EOFError()
            else:
                break
        print("connected!")
        sock.setblocking(True)
        server.logger.info(f"accepted {addrinfo} with fd {sock.fileno()}")
        server.clients.add(sock)
        # IMPLEMENT: server._authenticate_and_serve_client
        try:
            # IMPLEMENT: server._serve_client(sock, None)
            addrinfo = sock.getpeername()
            server.logger.info(f"welcome {addrinfo}")
            config = dict(server.protocol_config, credentials=None,
                            endpoints=(sock.getsockname(), addrinfo), logger=server.logger)
            conn = server.service._connect(Channel(SocketStream(sock)), config)

            ###### SPIN FOREVER HERE
            print("spin forever")
            spin_callback(conn)
            ###### SPIN FOREVER HERE
        except Exception:
            server.logger.exception("client connection terminated abruptly")
            raise
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            closing(sock)
            server.clients.discard(sock)
    except EOFError:
        pass  # server closed by another thread
    except KeyboardInterrupt:
        print("")
        server.logger.warning("keyboard interrupt!")
    finally:
        server.logger.info("server has terminated")
        server.close()

