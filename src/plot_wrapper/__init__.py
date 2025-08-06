from . import _brine_array_patch
from . import _brine_torch_patch
from . import _brine_PIL_patch
# Maybe, load modules on demand?

from ._plot_wrapper import WrapperService, AsyncWrapperService, ServiceHost

try:
    from ._matplotlib import MatplotlibWrapper, InteractiveMatplotlibWrapper
except Exception as e:
    print("plot_wrapper: Could not import matplotlib wrapper, maybe it is not installed?")

try:
    from ._o3d import O3dVisWrapper
except Exception as e:
    print("plot_wrapper: Could not import open3d wrapper, maybe it is not installed?")

