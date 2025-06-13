"""load/dump monkeypatch functions for numpy arrays and numpy numeric data types."""
import itertools

from rpyc.core import brine
try:
    from _brine_patch import register
except ImportError:
    from ._brine_patch import register
import numpy as np

# Annoyed that numpy removed a nice way of enumerating this
NP_INTEGER = [
    np.bool_,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64
]
NP_FLOAT = [
    np.float16,
    np.float32,
    np.float64,
]
NP_COMPLEX = [
    np.complex64,
    np.complex128,
]
NP_TYPES = NP_INTEGER + NP_FLOAT + NP_COMPLEX

@register(brine._custom_dumpable)
def _dumpable_numpy(obj):
    return type(obj) in NP_TYPES or type(obj) == np.ndarray

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
    if type(obj) == np.ndarray:
        _dump_array(obj, stream)
    elif type(obj) in NP_INTEGER:
        brine._dump_int(obj, stream)
    elif type(obj) in NP_FLOAT:
        brine._dump_float(obj, stream)
    elif type(obj) in NP_COMPLEX:
        brine._dump_complex(obj, stream)
    else:
        ret = False
    return ret
