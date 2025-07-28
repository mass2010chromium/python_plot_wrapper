"""
Example of creating matplotlib plots using a separate process.

This isn't usually necessary, but can help in some cases,
  mostly if you are encountering opengl conflicts between matplotlib
  and other visualization packages.
"""
# Equivalent of:
#   import matplotlib.pyplot as plt
from plot_wrapper import MatplotlibWrapper
plt = MatplotlibWrapper()
plt.start()

print("Starting plot")
plt.figure(0)
plt.plot([1, 2], [3, 4])
plt.show()  # blocking
print("Done!")

# Optional: clean up
plt.stop()
