import bpy
import time

FILEPATH = "basic_particle_simulation.blend"
N_FRAMES = 100
DENSITY = 1_000

def _bake_print_time(obj: bpy.types.Object):
    obj.select_set(True)
    start = time.time()
    bpy.ops.object.simulation_nodes_cache_bake(selected=True)
    end = time.time()
    print(end - start)


def main():
    bpy.ops.wm.open_mainfile(filepath=FILEPATH)
    bpy.context.scene.frame_end = N_FRAMES
    obj = bpy.data.objects["Particles"]
    obj.modifiers["GeometryNodes"]["Input_3"] = DENSITY
    _bake_print_time(obj)
    
    bpy.ops.wm.open_mainfile(filepath="raycasting.blend")
    obj = bpy.data.objects["Cube"]
    _bake_print_time(obj)


if __name__ == "__main__":
    main()
