import numpy as np
import rpyc

if __name__ == "__main__":
    from _plot_wrapper import AsyncWrapperService, ServiceHost
    import _brine_o3d_patch
else:
    from ._plot_wrapper import AsyncWrapperService, ServiceHost
    from . import _brine_o3d_patch


class O3dVisWrapper(ServiceHost):
    """
    Start an open3d visualization Visualizer object in a separate process
    so opengl doesn't fight with other visualizers.

    Notably open3d is never imported in the parent process.
    """

    def create_wrapper_service(self, **kwargs):
        try:
            import open3d as o3d
            vis = o3d.visualization.Visualizer()
            vis.create_window()
        except ImportError:
            print("Error import open3d... maybe it's not installed?")
            port_val.value = -1
            return (-1, None)

        def spin_o3d():
            """Helper function to poll for events from the open3d visualizer window."""
            vis.poll_events()
            vis.update_renderer()

        spinrate = kwargs.get("spinrate", 20)
        return (0, AsyncWrapperService(vis, spin_o3d, spinrate=spinrate))

if __name__ == "__main__":
    vis = O3dVisWrapper()
    vis.start()

    import open3d as o3d
    mesh = o3d.geometry.TriangleMesh()
    np_vertices = np.array([[2, 2, 0],
                            [5, 2, 0],
                            [5, 5, 0]], dtype=np.float64)
    np_triangles = np.array([[0, 1, 2], [2, 1, 0]]).astype(np.int32)

    mesh.vertices = o3d.utility.Vector3dVector(np_vertices)

    mesh.triangles = o3d.utility.Vector3iVector(np_triangles)

    vis.add_geometry(mesh)

    #vis.spin()
    for i in range(10):
        print(i)
        input()
        np_vertices += [0.0, 0.0, 0.1]
        mesh.vertices = o3d.utility.Vector3dVector(np_vertices)

        vis.clear_geometries()
        vis.add_geometry(mesh, reset_bounding_box=False)
    vis.stop()
