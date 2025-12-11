import os
import slam.io as sio
import slam.texture as stex
import slam.sulcal_depth as ssd
from directories import output_directories

# Declare Paths
output_dirs = output_directories()
dir_meshes = output_dirs['mesh_save_path'] # Smooth fetal SURFACE PATH
dir_curv = output_dirs['mean_tex_dir'] # Mean curvature directory
dir_dpf = output_dirs['dpf_tex_dir'] # Output dpf texture directory

if __name__ == "__main__":
    for filename in os.listdir(dir_meshes):
        mesh_file = os.path.join(dir_meshes, filename)
        mesh = sio.load_mesh(mesh_file)
        
        # Extract base name from mesh file by removing prefix
        if filename.startswith("smooth_5_"):
            base_name_mesh = filename.replace("smooth_5_", "")
        else:
            base_name_mesh = filename
        
        for file in os.listdir(dir_curv):
            # Extract base name from curvature file by removing prefix
            if file.startswith("filt_mean_curv_"):
                base_name_curv = file.replace("filt_mean_curv_", "")
            else:
                base_name_curv = file
            
            # Check if base names match
            if base_name_mesh == base_name_curv:
                mean_curv_file = os.path.join(dir_curv, file)
                mean_curv = sio.load_texture(mean_curv_file)
                
                dpf_star = ssd.dpf_star(mesh, curvature=mean_curv.darray[0], alphas=[500], adaptation='volume_hull')
                dpf_tex = stex.TextureND(darray=dpf_star[0])
                dpf_filename = "dpf_" + base_name_curv
                dpf_star_file = os.path.join(dir_dpf, dpf_filename)
                sio.write_texture(dpf_tex, dpf_star_file)
                break  # Found matching file, move to next mesh