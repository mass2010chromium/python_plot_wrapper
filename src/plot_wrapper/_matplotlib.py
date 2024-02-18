if __name__ == "__main__":
    from _plot_wrapper import WrapperService, AsyncWrapperService, ServiceHost
    import _brine_array_patch
else:
    from ._plot_wrapper import WrapperService, AsyncWrapperService, ServiceHost
    from . import _brine_array_patch


class MatplotlibWrapper(ServiceHost):
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

    def create_wrapper_service(self, **kwargs):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Error import matplotlib... maybe it's not installed?")
            port_val.value = -1
            return (-1, None)

        return (0, WrapperService(plt))

class InteractiveMatplotlibWrapper(ServiceHost):
    """
    Start matplotlib in a separate process, so opengl doesn't fight with other visualizers.
    Starts interactive matplotlib (plt.ion()).

    ```
    # instead of importing, you can do this
    plt = MatplotlibWrapper()
    plt.start()

    ...matplotlib commands...

    plt.stop()
    ```

    Notably matplotlib is never imported in the parent process.
    """

    def create_wrapper_service(self, **kwargs):
        try:
            import matplotlib
            import matplotlib.pyplot as plt
        except ImportError:
            print("Error import matplotlib... maybe it's not installed?")
            port_val.value = -1
            return (-1, None)

        plt.ion()

        # Real spinrate is half this lol
        # half spent on plot, half on polling the server
        spinrate = kwargs.get("spinrate", 80)

        def spin_mpl():
            """Helper function to poll for events from the open3d visualizer window."""
            figManager = matplotlib._pylab_helpers.Gcf.get_active()
            if figManager is not None:
                canvas = figManager.canvas
                if canvas.figure.stale:
                    canvas.draw()
                canvas.start_event_loop(1/spinrate)
        return (0, AsyncWrapperService(plt, spin_mpl, spinrate=spinrate))


if __name__ == "__main__":
    import numpy as np
    plt = MatplotlibWrapper()
    plt.start()
    plt.figure(0)
    plt.plot(np.array([1, 2]), [1, 2])
    plt.show()

    plt.stop()

    plt = InteractiveMatplotlibWrapper()
    plt.start()
    plt.figure(0)

    x = np.array([1.0, 2.0])
    import time
    import rpyc
    clf = rpyc.async_(plt.clf)
    plot = rpyc.async_(plt.plot)
    for i in range(40):
        x += 0.05
        plt.clf()
        plt.plot(x, [1, 2])
        time.sleep(0.05)

    plt.stop()

