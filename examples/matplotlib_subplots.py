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

plt.figure(0)

fig, (a1, a2) = plt.subplots(1, 2)
a1.plot([0, 1], [1, 2])
a2.plot([1, 2], [3, 4])

input()

plt.stop()
