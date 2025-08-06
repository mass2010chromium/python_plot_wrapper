"""load/dump monkeypatch functions for PIL Images. Saves only the raw array data"""
from rpyc.core import brine, netref

try:
    from _brine_patch import register
    from _brine_array_patch import _dump_array
except ImportError:
    from ._brine_patch import register
    from ._brine_array_patch import _dump_array

try:
    from PIL import Image
    import numpy as np

    @register(brine._custom_dumpable)
    def _dumpable_image(obj):
        if type(obj) == netref:
            return False
        return isinstance(obj, Image.Image)

    @register(brine._custom_loaders)
    def _load_image(stream):
        data = brine._load(stream)
        return Image.fromarray(data)

    @register(brine._custom_dumpers)
    def _dump_image(obj, stream):
        if isinstance(obj, Image.Image):
            stream.append(brine.TAG_CUSTOM)
            brine._dump_int(_load_image.id, stream)
            _dump_array(np.array(obj), stream)
            return True
        return False

except Exception as e:
    print("Could not load Image save patches... perhaps PIL or numpy is not installed?")
