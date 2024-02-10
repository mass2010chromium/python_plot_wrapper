import multiprocessing as mp
import time

import rpyc

from _plot_wrapper import WrapperService


class MatplotlibWrapper:
    """
    Start matplotlib in a separate process, so opengl doesn't fight with other visualizers.

    ```
    # instead of importing, you can do this
    plt = MatplotlibWrapper()
    plt.start()

    ...matplotlib commands...

    plt.stop()
    ```

    Notably matplotlib is never imported in the parent process.
    """
    
    def start(self, sleep_dt=1):
        """
        Spawn the matplotlib-running process. Uses rpyc to do communication.
        """
        def spawn_mpl_wrapper(port_val):
            try:
                import matplotlib.pyplot as plt
            except ImportError:
                print("Error import matplotlib... maybe it's not installed?")
                port_val.value = -1
                return -1

            # Janky way to pass the server object to the service after it's created.
            server_ptr = []
            # Default port = 0 means pick a port for me.
            server = rpyc.utils.server.OneShotServer(WrapperService(plt, server_ptr))
            server_ptr.append(server)

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
            return 0

        # Set to nonzero when the child starts correctly. Set it back to zero as a termination signal.
        self.__port_val = mp.Value('i', 0)
        self.__server_proc = mp.Process(target=spawn_mpl_wrapper, args=(self.__port_val,))
        self.__server_proc.start()
        while self.__port_val.value == 0:
            #print("Waiting for server to start...")
            time.sleep(sleep_dt)

        if self.__port_val.value == -1:
            # Import error. server did not start correctly
            return self.__server_proc.join()
        self.__client = rpyc.connect('localhost', self.__port_val.value)
        return 0

    def stop(self):
        #print("Stopping server")
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
    plt = MatplotlibWrapper()
    plt.start()
    plt.figure(0)
    plt.plot([1, 2], [1, 2])
    plt.show()

    plt.stop()
