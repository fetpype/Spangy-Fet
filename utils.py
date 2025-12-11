import os
import numpy as np
import trimesh
import slam.io as sio
import slam.texture as stex
import plotly.graph_objs as go
import plotly.colors as pc
import nibabel as nib

# Function to get hull area
def get_hull_area(mesh):
    convex_hull = trimesh.convex.convex_hull(mesh)
    return float(convex_hull.area)  # Convert to float to ensure it's a numeric value

def get_gyrification_index(mesh):
    """
    Gyrification index as surface ratio between a mesh and its convex hull
    
    Parameters
    ----------
    mesh : Trimesh
        Triangular watertight mesh
    
    Returns
    -------
    gyrification_index : Float
        surface ratio between a mesh and its convex hull
    hull_area : Float
        area of the convex hull
    """
    hull_area = get_hull_area(mesh)
    gyrification_index = float(mesh.area) / hull_area  # Convert both to float
    return gyrification_index, hull_area

def calculate_band_wavelength(eigVal, group_indices):
    """
    Calculate the wavelength for each band based on eigenvalues
    
    Parameters
    ----------
    eigVal : ndarray
        Eigenvalues from the spectrum analysis
    group_indices : list of arrays
        Indices of eigenvalues in each band
    
    Returns
    -------
    band_wavelengths : list
        Average wavelength for each band in mm
    """
    band_wavelengths = []
    
    for indices in group_indices:
        if len(indices) == 0:  # Check if array is empty
            band_wavelengths.append(0)
            continue
            
        # Calculate frequency from eigenvalues using equation in Appendix A.1
        band_frequencies = np.sqrt(eigVal[indices] / (2 * np.pi))
        
        # Wavelength = 1/frequency (in mm)
        if np.mean(band_frequencies) > 0:
            avg_wavelength = 1 / np.mean(band_frequencies)
        else:
            avg_wavelength = 0
            
        band_wavelengths.append(avg_wavelength)
    
    return band_wavelengths

def calculate_parcels_per_band(loc_dom_band, levels):
    """
    Calculate the number of parcels (connected components) for each band
    
    Parameters
    ----------
    loc_dom_band : ndarray
        Local dominant band map
    levels : int
        Number of frequency bands
    
    Returns
    -------
    parcels_per_band : list
        Number of parcels for each band
    """
    from scipy import ndimage
    
    parcels_per_band = []
    
    for i in range(levels):
        # Create binary mask for this band
        band_mask = (loc_dom_band == i).astype(int)
        
        # Check if the band exists at all
        if np.sum(band_mask) == 0:
            parcels_per_band.append(0)
            continue
            
        # Label connected components
        labeled_array, num_parcels = ndimage.label(band_mask)
        
        parcels_per_band.append(num_parcels)
    
    return parcels_per_band

def calculate_band_coverage(mesh, loc_dom_band, band_idx):
    """
    Calculate the coverage metrics for a specific frequency band using local dominance map.
    
    Parameters:
    mesh: Mesh object containing vertices and faces
    loc_dom_band: Array of local dominant bands for each vertex
    band_idx: Index of the band to analyze (e.g., 4 for B4)
    
    Returns:
    float: Number of vertices where this band is dominant
    float: Percentage of total vertices
    float: Surface area covered by the band in mm²
    float: Percentage of total surface area
    """
    # Count vertices where this band is dominant
    band_vertices = loc_dom_band == band_idx
    num_vertices = np.sum(band_vertices)
    vertex_percentage = (num_vertices / len(loc_dom_band)) * 100
    
    # Calculate surface area coverage
    total_area = 0
    faces = mesh.faces
    vertices = mesh.vertices
    
    for face in faces:
        # If any vertex in the face has this dominant band, include face area
        if any(band_vertices[face]):
            v1, v2, v3 = vertices[face]
            # Calculate face area using cross product
            area = 0.5 * np.linalg.norm(np.cross(v2 - v1, v3 - v1))
            total_area += area
    
    area_percentage = (total_area / mesh.area) * 100
    return num_vertices, vertex_percentage, total_area, area_percentage

def ensure_dir_exists(directory):
    """
    Make sure a directory exists, creating it if necessary
    Handle the case where the directory might be created between check and creation
    """
    try:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)
    except FileExistsError:
        # Directory already exists (race condition handled)
        print(f"Directory already exists: {directory}")
        pass

def calculate_distance_to_center(mesh):
    """
    Calculate Euclidean distance from each vertex to the mesh center of mass.
    
    Parameters
    ----------
    vertices : np.ndarray
        Vertex coordinates (N, 3)
    faces : np.ndarray
        Face indices (M, 3)
    
    Returns
    -------
    distances : np.ndarray
        Distance values for each vertex (N,)
    center_mass : np.ndarray
        Center of mass coordinates (3,)
    """
    
    # Get center of mass
    center_mass = mesh.center_mass
    
    # Calculate Euclidean distance from each vertex to center of mass
    distances = np.linalg.norm(mesh.vertices - center_mass, axis=1)
    
    return distances, center_mass



def process_dist_tex(input_mesh, output_texture):
    """
    Main function to create distance texture from mesh.
    
    Parameters
    ----------
    input_mesh : str
        Path to input GIFTI mesh file (.surf.gii)
    output_texture : str
        Path to output GIFTI texture file (.gii)
    """
    print(f"Loading mesh from: {input_mesh}")
    mesh= sio.load_mesh(input_mesh)
    print(f"  Loaded {len(mesh.vertices)} vertices and {len(mesh.faces)} faces")
    
    print("Calculating distances to center of mass...")
    distances, center_mass = calculate_distance_to_center(mesh)
    print(f"  Center of mass: [{center_mass[0]:.2f}, {center_mass[1]:.2f}, {center_mass[2]:.2f}]")
    print(f"  Distance range: [{distances.min():.2f}, {distances.max():.2f}]")
    print(f"  Mean distance: {distances.mean():.2f}")
    
    print("Creating GIFTI texture...")
    gii_texture = stex.TextureND(distances)
    
    print(f"Saving texture to: {output_texture}")
    sio.write_texture(gii_texture, output_texture)
    print("Done!")

def read_gii_file(file_path):
    """
    Read scalar data from a GIFTI file
    
    :param file_path: str, path to the GIFTI scalar file
    :return: numpy array of scalar values or None if error
    """
    try:
        gifti_img = nib.load(file_path)
        scalars = gifti_img.darrays[0].data
        return scalars
    except Exception as e:
        print(f"Error loading texture: {e}")
        return None


def flip_translate_mesh(vertices):
    """
    Flip and translate mesh vertices for dual view display
    
    :param vertices: numpy array of vertex coordinates
    :return: transformed vertex coordinates
    """
    # rotation
    # Rx(90)
    # rot = np.array([[1, 0, 0, 0],[0, 0, -1, 0],[0, 1, 0, 0]])
    # Rz(180)
    rot = np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    vertices_trans = np.dot(rot, vertices.T).T
    # translation
    vertices_trans = vertices_trans - np.mean(vertices_trans, axis=0)
    trl_y = max(vertices[:, 1]) - min(vertices[:, 1]) + 10
    vertices_trans[:, 1] = vertices_trans[:, 1] + trl_y
    return vertices_trans


def create_custom_colormap():
    """
    Create a custom colormap for values from -6 to 6
    Returns both the colormap and the discrete colors for the legend
    """
    # Define colors for negative values (cool colors)
    negative_colors = [
        '#FF0000',  # red
        '#00FF00',  # green
        '#0000FF',  # blue
        '#92c5de',  # very light blue
        '#d1e5f0',  # pale blue
        '#f7f7f7',  # very pale blue for B-1
    ]
    
    # Define colors for positive values (warm colors)
    positive_colors = [
        '#fddbc7',  # pale red
        '#f4a582',  # light red
        '#d6604d',  # medium red
        '#d6604d',  # medium red
        '#b2182b',  # dark red
        '#67001f',  # very dark red
    ]
    
    # Create color mapping for legend
    value_color_map = {}
    for i, color in enumerate(reversed(negative_colors)):
        value_color_map[-(i + 1)] = color
    for i, color in enumerate(positive_colors):
        value_color_map[i + 1] = color
        
    # Create continuous colorscale
    colorscale = []
    
    # Add negative colors
    for i, color in enumerate(negative_colors):
        pos = i / (len(negative_colors) - 1) * 0.5
        colorscale.append([pos, color])
    
    # Add positive colors
    for i, color in enumerate(positive_colors):
        pos = 0.5 + (i / (len(positive_colors) - 1) * 0.5)
        colorscale.append([pos, color])
    
    return colorscale, value_color_map


def plot_mesh_with_legend(vertices, faces, scalars, view_type='both', selected_bands=None, 
                          camera=None, title=None, show_dual_view=True):
    """
    Plot mesh with custom legend instead of colorbar for SPANGY
    
    Parameters:
    - vertices: mesh vertices
    - faces: mesh faces
    - scalars: texture values
    - view_type: 'both', 'positive', or 'negative'
    - selected_bands: list of bands to display (None for all)
    - camera: camera position dictionary
    - title: plot title
    - show_dual_view: if True, shows both original and flipped mesh
    """
    # Create custom colormap and value-color mapping
    colorscale, value_color_map = create_custom_colormap()
    
    # Create a copy of scalars to modify
    display_scalars = scalars.copy()
    
    # Apply band selection if specified
    if selected_bands is not None:
        # Convert all values not in selected_bands to NaN
        mask = np.zeros_like(display_scalars, dtype=bool)
        for band in selected_bands:
            mask |= (np.round(display_scalars) == band)
        display_scalars[~mask] = np.nan
    
    # Apply view filtering after band selection
    if view_type == 'positive':
        display_scalars[display_scalars < 0] = np.nan
    elif view_type == 'negative':
        display_scalars[display_scalars > 0] = np.nan
    
    # Clip values to our range of interest (-6 to 6)
    display_scalars = np.clip(display_scalars, -6, 6)
    
    # Create the original mesh
    mesh = go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        intensity=display_scalars,
        intensitymode='vertex',
        colorscale=colorscale,
        cmin=-6,
        cmax=6,
        showscale=False,
        flatshading=False,
        hoverinfo='text',
        hovertext=[f'Value: {s:.2f}' for s in display_scalars]  # Match plot.py format
    )
    
    # Create data list starting with original mesh
    mesh_data = [mesh]
    
    # Add flipped mesh if dual view is enabled
    if show_dual_view:
        vertices_flipped = flip_translate_mesh(vertices)
        mesh_flipped = go.Mesh3d(
            x=vertices_flipped[:, 0],
            y=vertices_flipped[:, 1],
            z=vertices_flipped[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            intensity=display_scalars,
            intensitymode='vertex',
            colorscale=colorscale,
            cmin=-6,
            cmax=6,
            showscale=False,
            flatshading=False,
            hoverinfo='text',
            hovertext=[f'Value: {s:.2f}' for s in display_scalars]
        )
        mesh_data.append(mesh_flipped)
    
    # Create legend items
    legend_traces = []
    
    def add_legend_items(values):
        for val in values:
            color = value_color_map[val]
            legend_traces.append(
                go.Scatter3d(
                    x=[None],
                    y=[None],
                    z=[None],
                    mode='markers',
                    marker=dict(size=10, color=color),
                    name=f'B{val}',
                    showlegend=True
                )
            )
    
    if selected_bands is not None:
        sorted_bands = sorted(selected_bands)
        add_legend_items([b for b in sorted_bands if 
                         (b < 0 and view_type in ['both', 'negative']) or
                         (b > 0 and view_type in ['both', 'positive'])])
    else:
        if view_type in ['both', 'negative']:
            add_legend_items(range(-6, 0))
        if view_type in ['both', 'positive']:
            add_legend_items(range(1, 7))
    
    # Create the figure
    fig = go.Figure(data=mesh_data + legend_traces)
    
    # Update layout - MATCH plot.py exactly
    layout_dict = dict(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=camera  # NO aspectmode!
        ),
        height=900,
        width=1200,  # Always 1200 for dual view, like plot.py
        margin=dict(l=10, r=10, b=10, t=50 if title else 10),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)'
        )
    )
    
    if title:
        layout_dict['title'] = dict(
            text=title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20)
        )
    
    fig.update_layout(**layout_dict)
    
    return fig

def plot_distance_texture(vertices, faces, distances, distance_range=None,
                          camera=None, title=None, show_dual_view=True,
                          colorscale='viridis', show_colorbar=True):
    """
    Plot mesh with distance-based texture using consistent coloring
    
    Parameters:
    - vertices: mesh vertices (N, 3)
    - faces: mesh faces (M, 3)
    - distances: distance values per vertex (N,)
    - distance_range: tuple (min, max) for consistent color scaling across meshes
                      If None, uses (0, max_distance_in_data)
    - camera: camera position dictionary
    - title: plot title
    - show_dual_view: if True, shows both original and flipped mesh
    - colorscale: plotly colorscale name ('viridis', 'plasma', 'turbo', 'jet', etc.)
    - show_colorbar: whether to show the colorbar
    
    Returns:
    - fig: plotly figure object
    """
    # Determine color range
    if distance_range is None:
        cmin = 0
        cmax = np.nanmax(distances)
    else:
        cmin, cmax = distance_range
    
    # Create the original mesh
    mesh = go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        intensity=distances,
        intensitymode='vertex',
        colorscale=colorscale,
        cmin=cmin,
        cmax=cmax,
        showscale=show_colorbar,
        colorbar=dict(
            title=dict(text='Distance', side='right'),
            x=1.0,
            len=0.75,
            thickness=20
        ) if show_colorbar else None,
        flatshading=False,
        hoverinfo='text',
        hovertext=[f'Distance: {d:.2f}' for d in distances]
    )
    
    # Create data list starting with original mesh
    mesh_data = [mesh]
    
    # Add flipped mesh if dual view is enabled
    if show_dual_view:
        vertices_flipped = flip_translate_mesh(vertices)
        mesh_flipped = go.Mesh3d(
            x=vertices_flipped[:, 0],
            y=vertices_flipped[:, 1],
            z=vertices_flipped[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            intensity=distances,
            intensitymode='vertex',
            colorscale=colorscale,
            cmin=cmin,
            cmax=cmax,
            showscale=False,  # Only show colorbar once
            flatshading=False,
            hoverinfo='text',
            hovertext=[f'Distance: {d:.2f}' for d in distances]
        )
        mesh_data.append(mesh_flipped)
    
    # Create the figure
    fig = go.Figure(data=mesh_data)
    
    # Update layout - match original function style
    layout_dict = dict(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=camera
        ),
        height=900,
        width=1200,
        margin=dict(l=10, r=10, b=10, t=50 if title else 10),
        showlegend=False
    )
    
    if title:
        layout_dict['title'] = dict(
            text=title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20)
        )
    
    fig.update_layout(**layout_dict)
    
    return fig

def mesh_orientation(mesh, hemisphere):
    """
    Function to orient mesh for proper visualisation
    
    Parameters:
    - mesh: loaded mesh file to be visualized
    - hemisphere: hemisphere of mesh being visualized
    
    Returns:
    - Oriented mesh and medial and lateral camera configuration
    """
    # Define hemisphere
    hemisphere = str(hemisphere).lower()

    # Set configuration and transformation according to hemisphere
    if hemisphere == 'right':
        transfo_180 = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        # mesh.apply_transform(transfo_180)
        
        camera_lateral = dict(
            eye=dict(x=2, y=0, z=0),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=-1)
        )

        camera_medial = dict(
            eye=dict(x=-2, y=0, z=0),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=-1)
        )
        
    elif hemisphere == 'left':
        transfo_180 = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        # mesh.apply_transform(transfo_180)
        
        camera_medial = dict(
            eye=dict(x=2, y=0, z=0),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=-1)
        )

        camera_lateral = dict(
            eye=dict(x=-2, y=0, z=0),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=-1)
        )
    
    else:
        raise ValueError(f'Invalid hemisphere parameter: {hemisphere}. Expected "left" or "right".')

    return mesh, camera_medial, camera_lateral

def create_colormap_with_black_stripes(base_colormap, num_intervals=10, black_line_width=0.01):
    temp_c = pc.get_colorscale(base_colormap)
    temp_c_2 = [ii[1] for ii in temp_c]
    old_colormap = convert_rgb_to_hex_if_needed(temp_c_2)
    custom_colormap = []
    base_intervals = np.linspace(0, 1, len(old_colormap))

    for i in range(len(old_colormap) - 1):
        custom_colormap.append([base_intervals[i], old_colormap[i]])
        if i % (len(old_colormap) // num_intervals) == 0:
            black_start = base_intervals[i]
            black_end = min(black_start + black_line_width, 1)
            custom_colormap.append([black_start, 'rgb(0, 0, 0)'])
            custom_colormap.append([black_end, old_colormap[i]])
    custom_colormap.append([1, old_colormap[-1]])
    return custom_colormap

def plot_mesh_with_colorbar(vertices, faces, scalars=None, color_min=None, color_max=None, camera=None, show_contours=False, colormap='jet', use_black_intervals=False, center_colormap_on_zero=False, title=None):
    fig_data = dict(
        x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
        i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
        flatshading=False, hoverinfo='text', showscale=False
    )

    vertices_flipped = flip_translate_mesh(vertices)
    fig_data_flipped = dict(
        x=vertices_flipped[:, 0], y=vertices_flipped[:, 1], z=vertices_flipped[:, 2],
        i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
        flatshading=False, hoverinfo='text', showscale=False
    )

    if scalars is not None:
        color_min = color_min if color_min is not None else np.min(scalars)
        color_max = color_max if color_max is not None else np.max(scalars)

        if center_colormap_on_zero:
            max_abs_value = max(abs(color_min), abs(color_max))
            color_min, color_max = -max_abs_value, max_abs_value

        if use_black_intervals:
            colorscale = create_colormap_with_black_stripes(colormap)
        else:
            colorscale = colormap

        fig_data.update(
            intensity=scalars,
            intensitymode='vertex',
            cmin=color_min,
            cmax=color_max,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title="Scalars",
                tickformat=".2f",
                thickness=30,
                len=0.9
            ),
            hovertext=[f'Scalar value: {s:.2f}' for s in scalars]
        )
        fig_data_flipped.update(
            intensity=scalars,
            intensitymode='vertex',
            cmin=color_min,
            cmax=color_max,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title="Scalars",
                tickformat=".2f",
                thickness=30,
                len=0.9
            ),
            hovertext=[f'Scalar value: {s:.2f}' for s in scalars]
        )
    fig = go.Figure(data=[go.Mesh3d(**fig_data), go.Mesh3d(**fig_data_flipped)])
    if show_contours:
        fig.data[0].update(contour=dict(show=True, color='black', width=2))

    # Update layout
    layout_dict = dict(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            camera=camera
        ),
        height=900,
        width=1200,
        margin=dict(l=10, r=10, b=10, t=50 if title else 10),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)'
        )
    )

    if title:
        layout_dict['title'] = dict(
            text=title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20)
        )

    fig.update_layout(**layout_dict)
    return fig

def convert_rgb_to_hex_if_needed(colormap):
    hex_colormap = []
    for color in colormap:
        if color.startswith('rgb'):
            rgb_values = [int(c) for c in color[4:-1].split(',')]
            hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb_values)
            hex_colormap.append(hex_color)
        else:
            hex_colormap.append(color)
    return hex_colormap