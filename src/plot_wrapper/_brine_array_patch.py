"""load/dump monkeypatch functions for numpy arrays and numpy numeric data types."""
from rpyc.core import brine
try:
    from _brine_patch import register
except ImportError:
    from ._brine_patch import register
import numpy as np

@register(brine._custom_dumpable)
def _dumpable_numpy(obj):
    return isinstance(obj, np.number) or isinstance(obj, np.ndarray)

@register(brine._custom_loaders)
def _load_array(stream):
    shape = brine._load(stream)
    dtype = brine._load(stream)
    data = brine._load(stream)
    array = np.frombuffer(data, dtype=dtype).reshape(shape)
    return array

def _dump_array(obj, stream):
    """Dump four things.
    
    array tag, tuple for shape, string for dtype, tuple (flat) for data.
    """
    stream.append(brine.TAG_CUSTOM)
    brine._dump_int(_load_array.id, stream)
    brine._dump_tuple(obj.shape, stream)
    brine._dump_str(str(obj.dtype), stream)
    brine._dump_bytes(obj.tobytes(), stream)

@register(brine._custom_dumpers)
def _dump_numpy(obj, stream):
    ret = True
    if isinstance(obj, np.ndarray):
        _dump_array(obj, stream)
    elif isinstance(obj, np.integer):
        brine._dump_int(obj, stream)
    elif isinstance(obj, np.floating):
        brine._dump_float(obj, stream)
    elif isinstance(obj, np.complexfloating):
        brine._dump_complex(obj, stream)
    else:
        ret = False
    return ret
