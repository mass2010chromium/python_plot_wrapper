"""
Example of creating interactive matplotlib plots using a separate process.

This is useful for some quick asynchronous plotting -- usually much faster than
running matplotlib in the parent process.

"""
# Equivalent of:
#   import matplotlib.pyplot as plt
#   plt.ion()
from plot_wrapper import InteractiveMatplotlibWrapper
plt = InteractiveMatplotlibWrapper()
# Accepts keyword arguments:
#   spinrate: Controls the plt.pause() duration to be 1/spinrate.
#             If your plots are not showing up, this should be decreased
#               to give matplotlib more time to draw the canvas.
#
#             Default: 80
plt.start(spinrate=80)

# Interactive terminal
import select, sys, termios, tty
settings = termios.tcgetattr(sys.stdin)
def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        return sys.stdin.read(1)
    return None

# Bind asynchronous methods to be fully nonblocking
# Unfortunately, this tends to fail for some reason, over very slow connections
#    (ex. X forwarding)
import rpyc
clf = rpyc.async_(plt.clf)
plot = rpyc.async_(plt.plot)

try:
    print("Flappy Line")
    print("Press w in the terminal to jump, q to exit")
    plt.figure(0)
    x_history = [0]*20
    plt.plot(x_history)
    plt.show()
    x = 0
    v = 0
    prev_key = None
    i = 0
    while True:
        key = getKey()
        if key == 'q':
            break
        v -= 0.1
        if key == 'w' and prev_key != 'w':
            v = 2
        x += v
        if x < 0:
            x = 0
        x_history.pop(0)
        x_history.append(x)
        i += 1
        clf()
        plot(x_history)

finally:
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    # Optional: clean up
    plt.stop()
