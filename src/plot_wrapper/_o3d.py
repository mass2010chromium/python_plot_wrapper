import multiprocessing as mp
import threading
import time

import numpy as np
import rpyc

if __name__ == "__main__":
    from _plot_wrapper import WrapperService
    import _brine_o3d_patch
else:
    from ._plot_wrapper import WrapperService
    from . import _brine_o3d_patch

class O3dVisWrapperService(WrapperService):
    """
    Customized WrapperService for spinning o3d visualization.
    """

    def __init__(self, wrap_obj, server_ptr, spinrate=20):
        """
        @see WrapperService.__init__(self, wrap_obj, server_ptr)

        Parameters:
        -------------------
        wrap_obj:       Object              Object that will handle all rpyc calls.
                                            Must be an instance of o3d.visualization.Visualizer
        server_ptr:     List[rpyc.Server]   Server that runs this service.
        o3d_lib:        Object              Imported open3d
        spinrate:       Number              (Approximate) update rate of visualizer
        """
        super().__init__(wrap_obj, server_ptr)
        self.dt = 1 / spinrate
        self.active = False

    def spin(self, conn):
        """
        Helper function to poll for events from the open3d visualizer window.

        NOTE: wrap_obj is an instance of o3d.visualization.Visualizer
        """
        while self.active:
            self.wrap_obj.poll_events()
            self.wrap_obj.update_renderer()
            try:
                conn.poll(timeout=self.dt)
            except EOFError:
                break

    def _rpyc_getattr(self, name):
        if name == "spin":
            return self.spin
        return super()._rpyc_getattr(name)


class O3dVisWrapper:
    """
    Start an open3d visualization Visualizer object in a separate process
    so opengl doesn't fight with other visualizers.

    Notably open3d is never imported in the parent process.
    """
    
    def start(self, sleep_dt=1, spinrate=20):
        """
        Spawn the o3d visualizer-running process. Uses rpyc to do communication.
        """
        self.__client = None
        def spawn_vis_wrapper(port_val):
            try:
                import open3d as o3d
                vis = o3d.visualization.Visualizer()
                vis.create_window()
            except ImportError:
                print("Error import open3d... maybe it's not installed?")
                port_val.value = -1
                return -1

            # Janky way to pass the server object to the service after it's created.
            server_ptr = []
            vis_obj = O3dVisWrapperService(vis, server_ptr, spinrate=spinrate)
            # Default port = 0 means pick a port for me.
            server = rpyc.utils.server.OneShotServer(vis_obj)
            server_ptr.append(server)

            # Communicate the assigned port back via shared memory.
            port_val.value = server.port

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
                    vis_obj.active = True
                    vis_obj.spin(conn)
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
                vis_obj.active = False
                server.logger.info("server has terminated")
                server.close()

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

if __name__ == "__main__":
    vis = O3dVisWrapper()
    vis.start()

    import open3d as o3d
    mesh = o3d.geometry.TriangleMesh()
    np_vertices = np.array([[2, 2, 0],
                            [5, 2, 0],
                            [5, 5, 0]], dtype=np.float64)
    np_triangles = np.array([[0, 1, 2], [2, 1, 0]]).astype(np.int32)

    mesh.vertices = o3d.utility.Vector3dVector(np_vertices)

    mesh.triangles = o3d.utility.Vector3iVector(np_triangles)

    vis.add_geometry(mesh)

    #vis.spin()
    for i in range(10):
        print(i)
        input()
        np_vertices += [0.0, 0.0, 0.1]
        mesh.vertices = o3d.utility.Vector3dVector(np_vertices)

        vis.clear_geometries()
        vis.add_geometry(mesh, reset_bounding_box=False)
    vis.stop()
