import slam.curvature as scurv
import slam.io as sio
import slam.texture as stex
from directories import output_directories, input_directories
from utils import ensure_dir_exists
from slam.differential_geometry import (
    laplacian_mesh_smoothing,
)
import os

# Initialize paths
input_dirs = input_directories()
output_dirs = output_directories()
ensure_dir_exists(output_dirs['output_folder'])
log_path = os.path.join(output_dirs['output_folder'], 'log.txt')

surface_path = input_dirs['surface_path']
for sub in sorted(os.listdir(surface_path)):
    for ses in os.listdir(os.path.join(surface_path, sub)):
        for file in os.listdir(os.path.join(surface_path, sub, ses, 'anat')):
            if file.endswith('.surf.gii'):
                filename = file
                subject_id = f"{sub}/{ses}/{filename}"
                subject_output_dirs = output_directories(filename=filename)
                if (
                    subject_output_dirs['mean_tex_path']
                    and os.path.exists(subject_output_dirs['mean_tex_path'])
                ):
                    print(
                        f"Skipping {subject_id}: output already exists at "
                        f"{subject_output_dirs['mean_tex_path']}"
                    )
                    continue
                try:
                    mesh_file = os.path.join(
                        surface_path, sub, ses, 'anat', file
                    )

                    filename = os.path.basename(mesh_file)
                    print("Processing file: ", filename)
                    mesh = sio.load_mesh(mesh_file)
                    mesh_smooth_5 = laplacian_mesh_smoothing(
                        mesh, nb_iter=5, dt=0.1
                    )
                    mesh = mesh_smooth_5

                    # Use path from directories module
                    ensure_dir_exists(output_dirs['mesh_save_path'])
                    new_mesh_path = os.path.join(
                        output_dirs['mesh_save_path'],
                        'smooth_5_{}'.format(filename),
                    )
                    sio.write_mesh(mesh, new_mesh_path)

                    # CURVATURE
                    print("compute the mean curvature")
                    PrincipalCurvatures, _, _ = \
                        scurv.curvatures_and_derivatives(mesh)
                    tex_PrincipalCurvatures = stex.TextureND(PrincipalCurvatures)

                    # Use path from directories module
                    subject_output_dirs = output_directories(filename=filename)
                    ensure_dir_exists(subject_output_dirs['principal_tex_dir'])
                    sio.write_texture(
                        tex_PrincipalCurvatures,
                        subject_output_dirs['principal_tex_path'],
                    )

                    mean_curv = 0.5 * (
                        PrincipalCurvatures[0, :] + PrincipalCurvatures[1, :]
                    )
                    tex_mean_curv = stex.TextureND(mean_curv)
                    tex_mean_curv.z_score_filtering(z_thresh=3)

                    # Use path from directories module
                    ensure_dir_exists(subject_output_dirs['mean_tex_dir'])
                    sio.write_texture(
                        tex_mean_curv, subject_output_dirs['mean_tex_path']
                    )
                    filt_mean_curv = tex_mean_curv.darray.squeeze()
                except Exception as e:
                    error_message = f"{subject_id} | {str(e)}"
                    print(f"Error processing {error_message}")
                    with open(log_path, 'a', encoding='utf-8') as log_file:
                        log_file.write(error_message + "\n")
                    continue