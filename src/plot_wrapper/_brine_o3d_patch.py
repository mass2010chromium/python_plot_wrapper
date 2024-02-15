"""load/dump monkeypatch functions for open3d vectors and objects.

Currently supports:
    Vector3iVector
    Vector3dVector
    TriangleMesh
        only vertices and triangles
    PointCloud
        only points and colors
"""
from rpyc.core import brine
try:
    from _brine_patch import register
    from _brine_array_patch import _dump_array
except ImportError:
    from ._brine_patch import register
    from ._brine_array_patch import _dump_array

import numpy as np
import open3d as o3d

@register(brine._custom_dumpable)
def _dumpable_o3d(obj):
    if isinstance(obj, o3d.geometry.TriangleMesh):
        return True
    if isinstance(obj, o3d.geometry.PointCloud):
        return True
    if isinstance(obj, o3d.utility.Vector3iVector):
        return True
    if isinstance(obj, o3d.utility.Vector3dVector):
        return True
    return False

@register(brine._custom_loaders)
def _load_o3d_vec3ivec(stream):
    return o3d.utility.Vector3iVector(np.array(brine._load(stream)))
@brine.register(brine._dump_registry, o3d.utility.Vector3iVector)
def _dump_o3d_vec3ivec(obj, stream):
    stream.append(brine.TAG_CUSTOM)
    brine._dump_int(_load_o3d_vec3ivec.id, stream)
    _dump_array(np.asarray(obj), stream)

@register(brine._custom_loaders)
def _load_o3d_vec3dvec(stream):
    return o3d.utility.Vector3dVector(np.array(brine._load(stream)))
@brine.register(brine._dump_registry, o3d.utility.Vector3dVector)
def _dump_o3d_vec3dvec(obj, stream):
    stream.append(brine.TAG_CUSTOM)
    brine._dump_int(_load_o3d_vec3dvec.id, stream)
    _dump_array(np.asarray(obj), stream)

@register(brine._custom_loaders)
def _load_o3d_trimesh(stream):
    geom = o3d.geometry.TriangleMesh()
    geom.triangles = brine._load(stream)
    geom.vertices = brine._load(stream)
    return geom
@brine.register(brine._dump_registry, o3d.geometry.TriangleMesh)
def _dump_o3d_trimesh(obj, stream):
    stream.append(brine.TAG_CUSTOM)
    brine._dump_int(_load_o3d_trimesh.id, stream)
    _dump_o3d_vec3ivec(obj.triangles, stream)
    _dump_o3d_vec3dvec(obj.vertices, stream)

@register(brine._custom_loaders)
def _load_o3d_pcd(stream):
    geom = o3d.geometry.PointCloud()
    geom.points = brine._load(stream)
    geom.colors= brine._load(stream)
    return geom
@brine.register(brine._dump_registry, o3d.geometry.PointCloud)
def _dump_o3d_pcd(obj, stream):
    stream.append(brine.TAG_CUSTOM)
    brine._dump_int(_load_o3d_pcd.id, stream)
    _dump_o3d_vec3dvec(obj.points, stream)
    _dump_o3d_vec3dvec(obj.colors, stream)
