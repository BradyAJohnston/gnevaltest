import bpy
import time

def _bake_print_time(obj: bpy.types.Object):
    obj.select_set(True)
    start = time.time()
    bpy.ops.object.simulation_nodes_cache_bake(selected=True)
    end = time.time()
    print(end - start)

def test_particle(n_frames: int = 100, density: int = 1_000):
    bpy.ops.wm.open_mainfile(filepath="basic_particle_simulation.blend")
    bpy.context.scene.frame_end = n_frames
    obj = bpy.data.objects["Particles"]
    obj.modifiers["GeometryNodes"]["Input_3"] = density
    _bake_print_time(obj)

def test_raycast(cubes: int = 10_000, points: int = 10_000):
    bpy.ops.wm.open_mainfile(filepath="raycasting.blend")
    obj = bpy.data.objects["Cube"]
    tree = obj.modifiers["GeometryNodes"].node_group
    tree.nodes["Points.001"].inputs["Count"].default_value = cubes
    tree.nodes["Points"].inputs["Count"].default_value = points
    
    _bake_print_time(obj)

def main():
    test_particle()
    test_raycast()


if __name__ == "__main__":
    main()
