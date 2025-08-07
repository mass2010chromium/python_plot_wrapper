"""load/dump monkeypatch functions for numpy arrays and numpy numeric data types."""
from functools import reduce
import operator

from rpyc.core import brine
try:
    from _brine_patch import register
except ImportError:
    from ._brine_patch import register

try:
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
        if type(obj) in NP_TYPES:
            return True
        if isinstance(obj, np.ndarray):
            if obj.dtype == object:
                for elem in obj.reshape(-1, copy=False):
                    if not brine.dumpable(elem):
                        return False
            return True
        return False

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

    @register(brine._custom_loaders)
    def _load_array_object(stream):
        # NOTE: is this broken for 0-d arrays? Do I care?
        shape = brine._load(stream)
        elems = []
        n_elems = reduce(operator.mul, shape, 1)
        for i in range(n_elems):
            elems.append(brine._load(stream))
        return np.array(elems, dtype=object).reshape(shape)

    def _dump_array_object(obj, stream):
        stream.append(brine.TAG_CUSTOM)
        brine._dump_int(_load_array_object.id, stream)
        brine._dump_tuple(obj.shape, stream)
        for elem in obj.reshape(-1, copy=False):
            brine._dump(elem, stream)

    @register(brine._custom_dumpers)
    def _dump_numpy(obj, stream):
        ret = True
        if isinstance(obj, np.ndarray):
            if obj.dtype == object:
                _dump_array_object(obj, stream)
            else:
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
except Exception as e:
    print("Could not load array patches... perhaps numpy is not installed?")
