import os
import slam.io as sio
import slam.texture as stex
import slam.sulcal_depth as ssd
from directories import output_directories

# Declare Paths
output_dirs = output_directories()
dir_meshes = output_dirs['mesh_save_path']  # Smooth fetal SURFACE PATH
dir_curv = output_dirs['mean_tex_dir']  # Mean curvature directory
dir_dpf = output_dirs['dpf_tex_dir']  # Output dpf texture directory

if __name__ == "__main__":
    os.makedirs(dir_dpf, exist_ok=True)
    failed_files = []

    for filename in sorted(os.listdir(dir_meshes)):
        mesh_file = os.path.join(dir_meshes, filename)
        print("Processing file:", filename)

        if filename.startswith("smooth_5_"):
            base_name_mesh = filename.replace("smooth_5_", "")
        else:
            base_name_mesh = filename

        mean_curv_filename = "filt_mean_curv_" + base_name_mesh
        mean_curv_file = os.path.join(dir_curv, mean_curv_filename)
        if not os.path.exists(mean_curv_file):
            error_message = (
                f"{filename} | Expected curvature file not found: "
                f"{mean_curv_filename}"
            )
            failed_files.append(error_message)
            print(f"Failed {error_message}")
            continue

        dpf_filename = "dpf_" + base_name_mesh
        dpf_star_file = os.path.join(dir_dpf, dpf_filename)
        if os.path.exists(dpf_star_file):
            print(f"Skipping {filename}: output already exists at {dpf_star_file}")
            continue

        try:
            mesh = sio.load_mesh(mesh_file)
            mean_curv = sio.load_texture(mean_curv_file)
            dpf_star = ssd.dpf_star(
                mesh,
                curvature=mean_curv.darray[0],
                alphas=[500],
                adaptation='volume_hull',
            )
            dpf_tex = stex.TextureND(darray=dpf_star[0])
            sio.write_texture(dpf_tex, dpf_star_file)
        except Exception as e:
            error_message = f"{filename} | {str(e)}"
            failed_files.append(error_message)
            print(f"Error processing {error_message}")

    if failed_files:
        print("\nFailed files:")
        for failed in failed_files:
            print(f"- {failed}")
    else:
        print("\nAll files processed successfully.")