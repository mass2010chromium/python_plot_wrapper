"""load/dump monkeypatch functions dumping lists and dictionaries as immutable. Performance optimizations for RPC purposes"""
from functools import reduce
import operator

from rpyc.core import brine
try:
    from _brine_patch import register
except ImportError:
    from ._brine_patch import register

try:
    @register(brine._custom_dumpable)
    def _dumpable_pytype(obj):
        return type(obj) == list or type(obj) == dict

    @register(brine._custom_loaders)
    def _load_dict(stream):
        keys = brine._load(stream)
        values = brine._load(stream)
        return dict(zip(keys, values))

    def _dump_dict(obj, stream):
        """Dumps keys, then values.
        Can crash if the entire dict is not serializable.
        """
        stream.append(brine.TAG_CUSTOM)
        brine._dump_int(_load_dict.id, stream)
        keys = []
        values = []
        for k, v in obj.items():
            keys.append(k)
            values.append(v)
        brine._dump_tuple(keys, stream)
        brine._dump_tuple(values, stream)

    @register(brine._custom_dumpers)
    def _dump_pytypes(obj, stream):
        if type(obj) == list:
            brine._dump_tuple(obj, stream)

        # TODO: dict subclasses?
        elif type(obj) == dict:
            _dump_dict(obj, stream)
        else:
            return False
        return True
except Exception as e:
    print("Could not load array patches... perhaps numpy is not installed?")
