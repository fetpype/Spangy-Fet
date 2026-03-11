import os

def output_directories(filename=None, participant_session=None):
    """
    Returns a dictionary of output directory paths.
    
    Args:
        filename: Optional filename for constructing specific paths
        participant_session: Optional participant session identifier
    
    Returns:
        dict: Dictionary containing all output directory paths
    """
    mesh_save_path = "/media/tsanchez/tsanchez_data/data/normative_spangy/mesh/"
    principal_tex_dir = '/media/tsanchez/tsanchez_data/data/normative_spangy/principal_curv_tex/'
    mean_tex_dir = '/media/tsanchez/tsanchez_data/data/normative_spangy/mean_curv_tex/'
    dpf_tex_dir =  '/media/tsanchez/tsanchez_data/data/normative_spangy/dpf_tex/'
    dpf_snapshots_dir = '/media/tsanchez/tsanchez_data/data/normative_spangy/dpf_tex/snapshots/'
    plots_dir = '/media/tsanchez/tsanchez_data/data/normative_spangy/spangy/plots/'
    frecomposed_dir = "/media/tsanchez/tsanchez_data/data/normative_spangy/frecomposed/"
    output_folder = '/media/tsanchez/tsanchez_data/data/normative_spangy/info/'
    output_csv_file = os.path.join('/media/tsanchez/tsanchez_data/data/normative_spangy/info/', 'all_results.csv')
    
    # Paths that depend on variables
    principal_tex_path = os.path.join(principal_tex_dir, 'principal_curv_{}'.format(filename)) if filename else None
    mean_tex_path = os.path.join(mean_tex_dir, 'filt_mean_curv_{}'.format(filename)) if filename else None
    spangy_tex_path = f"/media/tsanchez/tsanchez_data/data/normative_spangy/spangy/textures/spangy_dom_band_{participant_session}" if participant_session else None
    
    return {
        'mesh_save_path': mesh_save_path,
        'principal_tex_dir': principal_tex_dir,
        'principal_tex_path': principal_tex_path,
        'mean_tex_dir': mean_tex_dir,
        'mean_tex_path': mean_tex_path,
        'dpf_tex_dir' : dpf_tex_dir,
        'dpf_snapshots_dir' : dpf_snapshots_dir,
        'plots_dir': plots_dir,
        'spangy_tex_path': spangy_tex_path,
        'frecomposed_dir': frecomposed_dir,
        'output_folder': output_folder,
        'output_csv_file': output_csv_file
    }

def input_directories():
    """
    Returns a dictionary of input directory paths.
    
    Returns:
        dict: Dictionary containing all input directory paths
    """
    surface_path = "/media/tsanchez/tsanchez_data/data/data/derivatives/nesvor_bounti_surfpype/"
    mesh_info_path = "/media/tsanchez/tsanchez_data/data/data/derivatives/nesvor_bounti_surfpype/participants.csv"
    
    return {
        'surface_path': surface_path,
        'mesh_info_path': mesh_info_path
    }
