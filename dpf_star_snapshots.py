import os
import glob
import numpy as np
import slam.io as sio
from utils import plot_mesh_with_colorbar
from directories import output_directories

# Initialize output directories
output_dirs = output_directories()
dir_meshes = output_dirs['mesh_save_path']  # Smooth fetal SURFACE PATH (with "smooth_5_" prefix)
dir_dpf = output_dirs['dpf_tex_dir']  # DPF texture directory (with "dpf_" prefix)
dir_dpf_snapshots = output_dirs['dpf_snapshots_dir']  # Snapshot save directory

if __name__ == "__main__":
    # Define camera positions for visualization
    camera_medial = dict(
        eye=dict(x=2, y=0, z=0),  # Camera position from medial side
        center=dict(x=0, y=0, z=0),  # Looking at center
        up=dict(x=0, y=0, z=1)  # Up vector points in positive z direction
    )
    
    camera_lateral = dict(
        eye=dict(x=-2, y=0, z=0),  # Camera position from lateral side
        center=dict(x=0, y=0, z=0),  # Looking at center
        up=dict(x=0, y=0, z=1)  # Up vector points in positive z direction
    )
    
    # Track processing status
    processed_subjects = []
    unprocessed_subjects = []
    
    # Iterate through each mesh file
    for mesh_filename in os.listdir(dir_meshes):
        mesh_file = os.path.join(dir_meshes, mesh_filename)
        
        # Remove "smooth_5_" prefix from mesh filename to get base name
        if mesh_filename.startswith("smooth_5_"):
            base_name_mesh = mesh_filename.replace("smooth_5_", "")
        else:
            base_name_mesh = mesh_filename
        
        # Iterate through DPF texture files to find matching one
        for dpf_filename in os.listdir(dir_dpf):
            # Remove "dpf_" prefix from DPF texture filename to get base name
            if dpf_filename.startswith("dpf_"):
                base_name_dpf = dpf_filename.replace("dpf_", "")
            else:
                base_name_dpf = dpf_filename
            
            # Check if base names match
            if base_name_mesh == base_name_dpf:
                print(f"Processing: {base_name_mesh}")
                
                # Define output snapshot filename
                snapshot_file = os.path.join(
                    dir_dpf_snapshots, 
                    f"snapshot_{base_name_mesh.replace('.surf.gii', '')}.png"
                )
                
                # Check if already processed
                if os.path.exists(snapshot_file):
                    print(f"  Already processed: {snapshot_file}")
                    processed_subjects.append(base_name_mesh)
                    break
                
                try:
                    # Load mesh file
                    mesh = sio.load_mesh(mesh_file)
                    
                    # Load matching DPF texture
                    dpf_star_file = os.path.join(dir_dpf, dpf_filename)
                    tex = sio.load_texture(dpf_star_file)
                    tex_visu = tex.darray[0]
                    
                    # Center the texture values around zero (subtract mean)
                    tex_visu = tex_visu - np.mean(tex_visu)
                    
                    # Create visualization with colorbar
                    fig = plot_mesh_with_colorbar(
                        vertices=mesh.vertices,
                        faces=mesh.faces,
                        scalars=tex_visu,
                        camera=camera_medial,  # Use medial view
                        color_min=-0.01,
                        color_max=0.01,
                        colormap='ylgnbu_r',
                        title=f'dpf_star {base_name_mesh}'
                    )
                    
                    # Save snapshot to directory
                    fig.write_image(snapshot_file)
                    print(f"  Saved snapshot: {snapshot_file}")
                    
                    processed_subjects.append(base_name_mesh)
                    
                except Exception as e:
                    print(f"  Error processing {base_name_mesh}: {e}")
                    unprocessed_subjects.append(base_name_mesh)
                
                break  # Found matching file, move to next mesh
    
    # Print summary
    print("\n" + "="*50)
    print(f"Processing complete!")
    print(f"Successfully processed: {len(processed_subjects)} subjects")
    print(f"Failed to process: {len(unprocessed_subjects)} subjects")
    
    if unprocessed_subjects:
        print("\nUnprocessed subjects:")
        for sub in unprocessed_subjects:
            print(f"  - {sub}")