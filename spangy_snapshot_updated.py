import slam.io as sio
import slam.texture as stex
import os
import pandas as pd
from utils import plot_mesh_with_legend, mesh_orientation, read_gii_file

# ======================== CONFIGURATION ========================
# Set all paths and parameters here for easy management

# Input/Output directories
MESH_DIRECTORY = "/media/tsanchez/tsanchez_data/data/normative_spangy/mesh"
TEXTURE_DIRECTORY = '/media/tsanchez/tsanchez_data/data/normative_spangy/spangy/textures'
OUTPUT_DIRECTORY = "/media/tsanchez/tsanchez_data/data/normative_spangy/spangy/chuv_snapshots"

# Band definitions
GYRI_BANDS = [4, 5, 6]
SULCI_BANDS = [-6, -5, -4]

# Mesh processing parameters
MESH_PREFIX = "smooth_5_"
MESH_SUFFIX_TO_REMOVE = "reo-SVR-output-brain-mask-brain_bounti-white."
TEXTURE_PREFIX = "spangy_dom_band_"

# Plot parameters
PLOT_TITLE = 'Negative Bands Visualization'
SELECTED_BANDS = SULCI_BANDS  # Change to GYRI_BANDS or None for different visualizations
SHOW_DUAL_VIEW = False


# ======================== MAIN EXECUTION ========================

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    
    print(f"Processing meshes from: {MESH_DIRECTORY}")
    print(f"Loading textures from: {TEXTURE_DIRECTORY}")
    print(f"Saving outputs to: {OUTPUT_DIRECTORY}")
    print(f"Selected bands: {SELECTED_BANDS}")
    print("-" * 60)
    
    # Collect vertex counts from all meshes
    processed_count = 0
    
    for filename in sorted(os.listdir(MESH_DIRECTORY)):
        print(f"Processing mesh: {filename}")
        original_filename = filename
        filename_cleaned = filename.replace(MESH_PREFIX, "").replace(
                MESH_SUFFIX_TO_REMOVE, ""
            ).replace(".surf.gii", "") if filename.startswith(MESH_PREFIX) else filename
        sub_ses = "_".join(filename_cleaned.split('_')[:2])
        hemi = "left" if filename_cleaned.split('_')[-2] == "hemi-L" else "right"
        texture = [file for file in os.listdir(TEXTURE_DIRECTORY) if sub_ses in file and hemi in file]
        if len(texture) == 0:
            print(f"No texture found for {filename_cleaned}")
            continue
        elif len(texture) > 1:
            raise ValueError(f"Multiple textures found for {filename_cleaned}")
        else:
            texture = texture[0]
                
            # Load mesh file
            mesh_file = os.path.join(MESH_DIRECTORY, original_filename)
            mesh = sio.load_mesh(mesh_file)
            hem_det = hemi
            
            # Orient mesh
            mesh, camera_medial, camera_lateral = mesh_orientation(mesh, hem_det)
            vertices = mesh.vertices
            faces = mesh.faces

            # Load generated texture
            tex_file = os.path.join(TEXTURE_DIRECTORY, texture)
            loc_dom_band_texture = read_gii_file(tex_file)

            # Create visualization with dual view
            fig = plot_mesh_with_legend(
                vertices=mesh.vertices,
                faces=mesh.faces,
                scalars=loc_dom_band_texture,
                selected_bands=SELECTED_BANDS,
                camera=camera_lateral, 
                title=PLOT_TITLE,
                show_dual_view=SHOW_DUAL_VIEW
            )
            
            # Save output
            output_path = os.path.join(OUTPUT_DIRECTORY, f"{sub_ses}_{hem_det}.png")
            fig.write_image(output_path)
            
            processed_count += 1
            print(f"Processed: {sub_ses}_{hem_det}")
    
    print("-" * 60)
    print(f"Total images processed: {processed_count}")
    print(f"All outputs saved to: {OUTPUT_DIRECTORY}")
