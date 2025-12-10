import bpy
import time

FILEPATH = "basic_particle_simulation.blend"
N_FRAMES = 200
DENSITY = 1_000

def main():
    bpy.ops.wm.open_mainfile(filepath=FILEPATH)
    bpy.context.scene.frame_end = N_FRAMES
    obj = bpy.data.objects["Particles"]
    obj.select_set(True)
    obj.modifiers["GeometryNodes"]["Input_3"] = DENSITY
    start = time.time()
    bpy.ops.object.simulation_nodes_cache_bake(selected=True)
    end = time.time()
    print(end - start)


if __name__ == "__main__":
    main()
