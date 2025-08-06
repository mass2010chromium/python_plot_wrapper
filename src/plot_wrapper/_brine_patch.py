"""Patch brine dump/load core functionality to make it easier to extend."""
from rpyc.core import brine, netref

brine.TAG_CUSTOM = b"\x1c"

def _undumpable(obj, stream):
    raise TypeError(f"cannot dump {obj} of type {type(obj)}")
brine._undumpable = _undumpable

brine._custom_dumpable = []
def dumpable(obj):
    """Indicates whether the given object is *dumpable* by brine

    :returns: ``True`` if the object is dumpable (e.g., :func:`dump` would succeed),
              ``False`` otherwise
    """
    if type(obj) in brine.simple_types:
        return True
    if type(obj) in (tuple, frozenset):
        return all(dumpable(item) for item in obj)
    if type(obj) is slice:
        return dumpable(obj.start) and dumpable(obj.stop) and dumpable(obj.step)
    if type(type(obj)) == netref.NetrefMetaclass:
        return False
    for dumpable_check in brine._custom_dumpable:
        if dumpable_check(obj):
            return True
    return False
brine.dumpable = dumpable

brine._custom_dumpers = []
def _dump(obj, stream):
    """Dump an object to a byte stream (list).

    First try using brine's existing dumpers. to not degrade performance in average case
    Then, go through patches and try them one at a time
    """
    #print("dump", type(obj))
    #print(obj)
    i = len(stream)
    if type(obj) in brine._dump_registry:
        brine._dump_registry.get(type(obj))(obj, stream)
        #print(stream[i:])
        return
    if type(obj) == netref:
        brine._undumpable(obj, stream)
    for dumper in brine._custom_dumpers:
        if dumper(obj, stream):
            #print(stream[i:])
            return
    brine._undumpable(obj, stream)
brine._dump = _dump

old_dump = brine.dump
def dump(obj):
    print("start dump")
    print(obj)
    res = old_dump(obj)
    print("finish dump", res, flush=True)
    return res
#brine.dump = dump

brine._custom_loaders = []
@brine.register(brine._load_registry, brine.TAG_CUSTOM)
def _load_custom(stream):
    type_id = brine._load(stream)
    #print("load custom", type_id, brine._custom_loaders[type_id])
    return brine._custom_loaders[type_id](stream)

def register(target):
    def reg(func):
        func.id = len(target)
        target.append(func)
        return func
    return reg


def _load(stream):
    tag = stream.read(1)
    print(tag)
    if tag in brine.IMM_INTS_LOADER:
        print("imm")
        ret = brine.IMM_INTS_LOADER[tag]
    else:
        print(brine._load_registry.get(tag))
        ret = brine._load_registry.get(tag)(stream)
    print(ret, type(ret))
    return ret
#brine._load = _load

old_load = brine.load
def load(data):
    print("start load", data, flush=True)
    return old_load(data)
#brine.load = load
