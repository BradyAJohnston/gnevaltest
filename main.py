import argparse
import csv
import itertools
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import bpy

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_cpu_info() -> Dict[str, str]:
    """Get detailed CPU information."""
    cpu_info = {}

    if PSUTIL_AVAILABLE:
        # Physical and logical core counts
        cpu_info["cpu_physical_cores"] = str(psutil.cpu_count(logical=False))
        cpu_info["cpu_logical_cores"] = str(psutil.cpu_count(logical=True))

        # CPU frequency
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_info["cpu_freq_current_mhz"] = f"{freq.current:.2f}"
                cpu_info["cpu_freq_min_mhz"] = f"{freq.min:.2f}"
                cpu_info["cpu_freq_max_mhz"] = f"{freq.max:.2f}"
        except Exception:
            pass

        # Memory info
        try:
            mem = psutil.virtual_memory()
            cpu_info["total_ram_gb"] = f"{mem.total / (1024**3):.2f}"
        except Exception:
            pass

    # Try to get CPU model name from /proc/cpuinfo on Linux
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_info["cpu_model"] = line.split(":")[1].strip()
                        break
        except Exception:
            pass

    return cpu_info


def get_platform_metadata() -> Dict[str, str]:
    """Collect platform and system metadata."""
    # Get Blender version as a formatted string
    bpy_version = ".".join(map(str, bpy.app.version))

    metadata = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "blender_version": bpy_version,
    }

    # Add detailed CPU and hardware info
    metadata.update(get_cpu_info())

    return metadata


def _bake_and_time(obj: bpy.types.Object) -> float:
    """Bake simulation and return elapsed time."""
    obj.select_set(True)
    start = time.time()
    bpy.ops.object.simulation_nodes_cache_bake(selected=True)
    end = time.time()
    elapsed = end - start
    print(f"Bake completed in {elapsed:.2f}s")
    return elapsed


def test_particle(n_frames: int = 100, density: int = 1_000) -> Dict[str, Any]:
    """Run particle simulation test and return results."""
    test_file = "basic_particle_simulation.blend"
    bpy.ops.wm.open_mainfile(filepath=test_file)
    bpy.context.scene.frame_end = n_frames
    obj = bpy.data.objects["Particles"]
    obj.modifiers["GeometryNodes"]["Input_3"] = density

    elapsed_time = _bake_and_time(obj)

    return {
        "test_name": "particle",
        "test_file": test_file,
        "n_frames": n_frames,
        "density": density,
        "elapsed_time": elapsed_time,
    }


def test_raycast(cubes: int = 10_000, points: int = 10_000) -> Dict[str, Any]:
    """Run raycast test and return results."""
    test_file = "raycasting.blend"
    bpy.ops.wm.open_mainfile(filepath=test_file)
    obj = bpy.data.objects["Cube"]
    tree = obj.modifiers["GeometryNodes"].node_group
    tree.nodes["Points.001"].inputs["Count"].default_value = cubes
    tree.nodes["Points"].inputs["Count"].default_value = points

    elapsed_time = _bake_and_time(obj)

    return {
        "test_name": "raycast",
        "test_file": test_file,
        "cubes": cubes,
        "points": points,
        "elapsed_time": elapsed_time,
    }


def write_results_to_csv(
    results: List[Dict[str, Any]],
    output_file: str,
    custom_metadata: Dict[str, str] = None,
    append: bool = True,
):
    """Write test results to CSV file with metadata."""
    if custom_metadata is None:
        custom_metadata = {}

    output_path = Path(output_file)
    file_exists = output_path.exists()

    # Get platform metadata once
    platform_metadata = get_platform_metadata()
    timestamp = datetime.now().isoformat()

    # Combine all metadata
    base_metadata = {
        "timestamp": timestamp,
        **platform_metadata,
        **custom_metadata,
    }

    # Determine all possible columns from results
    all_result_keys = set()
    for result in results:
        all_result_keys.update(result.keys())

    # Create fieldnames: metadata first, then result fields
    fieldnames = list(base_metadata.keys()) + sorted(all_result_keys)

    mode = "a" if append and file_exists else "w"

    with open(output_path, mode, newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file is new or we're overwriting
        if not file_exists or not append:
            writer.writeheader()

        # Write each result row with metadata
        for result in results:
            row = {**base_metadata, **result}
            writer.writerow(row)

    print(f"Results written to {output_file} ({mode} mode)")


def main():
    parser = argparse.ArgumentParser(
        description="Run Blender simulation tests and record results to CSV"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="test_results.csv",
        help="Output CSV file path (default: test_results.csv)",
    )
    parser.add_argument(
        "--no-append",
        action="store_true",
        help="Overwrite output file instead of appending",
    )
    parser.add_argument(
        "--metadata",
        "-m",
        action="append",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Add custom metadata (can be used multiple times)",
    )

    args = parser.parse_args()

    # Parse custom metadata
    custom_metadata = {}
    if args.metadata:
        for key, value in args.metadata:
            custom_metadata[key] = value

    # # Define parameter ranges (small to large)
    # particle_n_frames = [50, 100, 200]
    # particle_density = [500, 1_000, 2_500, 5_000]

    # raycast_cubes = [1_000, 5_000, 10_000, 20_000]
    # raycast_points = [1_000, 5_000, 10_000, 20_000]
    #
    particle_n_frames = [50, 100]
    particle_density = [500, 1_000]

    raycast_cubes = [1_000, 5_000]
    raycast_points = [1_000, 5_000]

    # Generate all test configurations using itertools
    test_configs = []

    # Generate particle test configurations
    for n_frames, density in itertools.product(particle_n_frames, particle_density):
        test_configs.append(
            {
                "test": test_particle,
                "params": {"n_frames": n_frames, "density": density},
            }
        )

    # Generate raycast test configurations
    for cubes, points in itertools.product(raycast_cubes, raycast_points):
        test_configs.append(
            {"test": test_raycast, "params": {"cubes": cubes, "points": points}}
        )

    # Run all tests and collect results
    results = []
    for i, config in enumerate(test_configs, 1):
        test_func = config["test"]
        params = config["params"]
        print(f"\n[{i}/{len(test_configs)}] Running {test_func.__name__} with {params}")

        result = test_func(**params)
        results.append(result)

    # Write results to CSV
    write_results_to_csv(
        results, args.output, custom_metadata, append=not args.no_append
    )

    print(f"\nCompleted {len(results)} tests")


if __name__ == "__main__":
    main()
