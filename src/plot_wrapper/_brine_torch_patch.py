"""load/dump monkeypatch functions for pytorch tensors. Converts them to numpy arrays"""
import itertools

from rpyc.core import brine
try:
    from _brine_patch import register
    from _brine_array_patch import _dump_array
except ImportError:
    from ._brine_patch import register
    from ._brine_array_patch import _dump_array

try:
    import torch

    # Annoyed that numpy removed a nice way of enumerating this
    TORCH_INTEGER = [
        torch.bool,
        torch.uint8,
        torch.uint16,
        torch.uint32,
        torch.uint64,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
        torch.quint8,
        torch.qint8,
        torch.qint32,
        torch.quint4x2,
    ]
    TORCH_FLOAT = [
        torch.float16,
        torch.bfloat16,
        torch.float32,
        torch.float64,
    ]
    TORCH_COMPLEX = [
        torch.complex32,
        torch.complex64,
        torch.complex128,
    ]
    TORCH_TYPES = TORCH_INTEGER + TORCH_FLOAT + TORCH_COMPLEX

    @register(brine._custom_dumpable)
    def _dumpable_torch(obj):
        return type(obj) in TORCH_TYPES or torch.is_tensor(obj)

    @register(brine._custom_dumpers)
    def _dump_torch(obj, stream):
        ret = True
        if torch.is_tensor(obj):
            _dump_array(obj.detach().cpu().numpy(), stream)
        elif type(obj) in TORCH_INTEGER:
            brine._dump_int(obj, stream)
        elif type(obj) in TORCH_FLOAT:
            brine._dump_float(obj, stream)
        elif type(obj) in TORCH_COMPLEX:
            brine._dump_complex(obj, stream)
        else:
            ret = False
        return ret
except Exception as e:
    print("Could not load tensor patches... perhaps pytorch is not installed?")
