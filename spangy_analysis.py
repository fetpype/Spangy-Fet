import slam.io as sio
import slam.texture as stex
import slam.curvature as scurv
import os
import time
import slam.spangy as spgy
from slam.differential_geometry import laplacian_mesh_smoothing
import numpy as np
import matplotlib.pyplot as plt
from utils import ensure_dir_exists, calculate_band_coverage, calculate_band_wavelength, calculate_parcels_per_band, get_gyrification_index
from directories import output_directories, input_directories


def process_single_file(filename, surface_path, df):
    """
    Process a single surface file and compute various metrics.
    """
    try:
        start_time = time.time()
        print("Starting processing of {}".format(filename))

        filename = filename.replace('smooth_5_', '') # Remove the prefix from the previous smoothing

        hemisphere = 'left' if filename.endswith('left.surf.gii') else 'right'
        participant_session = filename.split('_')[0] + '_' + filename.split('_')[1] + f'_{hemisphere}'
        base_participant_session = filename.split('_')[0] + '_' + filename.split('_')[1]
        
        # Get directory paths from directories module
        output_dirs = output_directories(filename=filename, participant_session=participant_session)
        
        # Get corresponding gestational age
        try:
            gestational_age = df[df['participant_session'] == base_participant_session]['scan_age'].values[0]
        except:
            print(f"Warning: No matching gestational age found for {base_participant_session}")
            return None

        mesh_file = os.path.join(surface_path, filename)
        if not os.path.exists(mesh_file):
            print("Error: Mesh file not found: {}".format(mesh_file))
            return None

        # load mesh file    
        mesh = sio.load_mesh(mesh_file)

        # Define N
        N = 5000
        
        # Compute eigenpairs and mass matrix
        print("compute the eigen vectors and eigen values")
        eigVal, eigVects, lap_b = spgy.eigenpairs(mesh, N)

        tex_mean_curv = sio.load_texture(output_dirs['mean_tex_path'])
        filt_mean_curv = tex_mean_curv.darray.squeeze()
        total_mean_curv = sum(filt_mean_curv)
        # gyral_mask = np.where(filt_mean_curv > 0, 0, filt_mean_curv) # To mask gyri and only focus on sulci

        # WHOLE BRAIN MEAN-CURVATURE SPECTRUM
        grouped_spectrum, group_indices, coefficients, nlevels \
            = spgy.spectrum(filt_mean_curv, lap_b, eigVects, eigVal)
        levels = len(group_indices)

        # Calculate additional measures
        # 1. Power distribution across bands (normalized to percentage)
        total_power = np.sum(grouped_spectrum)
        power_distribution = (grouped_spectrum / total_power) * 100 if total_power > 0 else np.zeros_like(grouped_spectrum)
        
        # 2. Band wavelength for each band
        band_wavelengths = calculate_band_wavelength(eigVal, group_indices)
        
        # Plot coefficients and bands for all mean curvature signal
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        frequency = np.sqrt(eigVal/2*np.pi) # from equations in Appendix A.1
        ax1.scatter(frequency,
        coefficients, marker='o', s=20, linewidths=0.5)
        ax1.set_xlabel('Frequency (m⁻¹)')
        ax1.set_ylabel('Coefficients')

        ax2.scatter(frequency[1:],
        coefficients[1:], marker='o', s=20, linewidths=0.5) # remove B0 coefficients
        ax2.set_xlabel('Frequency (m⁻¹)')
        ax2.set_ylabel('Coefficients')

        ax3.bar(np.arange(0, levels), grouped_spectrum)
        ax3.set_xlabel('Spangy Frequency Bands')
        ax3.set_ylabel('Power Spectrum')
        plt.tight_layout()  # Adjust the spacing between subplots
        
        # Use path from directories module
        ensure_dir_exists(output_dirs['plots_dir'])
        
        # Save first plot
        fig.savefig(f"{output_dirs['plots_dir']}/{filename}.png", bbox_inches='tight', dpi=300)
        plt.close(fig)
        
        # Add a second plot for power distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        band_names = [f'B{i}' for i in range(levels)]
        ax.bar(band_names, power_distribution)
        ax.set_xlabel('Frequency Bands')
        ax.set_ylabel('Power Distribution (%)')
        ax.set_title(f'SPANGY Power Distribution - {participant_session}')
        for i, v in enumerate(power_distribution):
            ax.text(i, v + 0.5, f'{v:.1f}%', ha='center')
        plt.tight_layout()
        fig.savefig(f"{output_dirs['plots_dir']}/power_distribution_{filename}.png", bbox_inches='tight', dpi=300)
        plt.close(fig)
        
        # a. Whole brain parameters
        mL_in_MM3 = 1000
        CM2_in_MM2 = 100
        volume = mesh.volume
        surface_area = mesh.area
        afp = np.sum(grouped_spectrum[1:])
        print('** a. Whole brain parameters **')
        print('Volume = %d mL, Area = %d cm², Analyze Folding Power = %f,' %
            (np.floor(volume / mL_in_MM3), np.floor(surface_area / CM2_in_MM2), afp))

        # LOCAL SPECTRAL BANDS
        loc_dom_band, frecomposed = spgy.local_dominance_map(coefficients, filt_mean_curv,
                                                            levels, group_indices,
                                                            eigVects)
        
        # 3. Calculate number of parcels per band
        parcels_per_band = calculate_parcels_per_band(loc_dom_band, levels)
        
        # Print band number of parcels
        print('** b. Band number of parcels **')
        for i in range(levels):
            print(f'B{i} = {parcels_per_band[i]}', end=', ')
        print()
        
        # Print band wavelengths
        print('** Band wavelengths (mm) **')
        for i in range(levels):
            print(f'B{i} = {band_wavelengths[i]:.2f}', end=', ')
        print()

        # c. Band power
        print('** c. Band power **')
        for i in range(levels):
            print(f'B{i} = {grouped_spectrum[i]:.6f}', end=', ')
        print()

        # d. Band relative power
        print('** d. Band relative power **')
        for i in range(levels):
            print(f'B{i} = {power_distribution[i]:.2f}%', end=', ')
        print()

        # Use path from directories module
        tmp_tex = stex.TextureND(loc_dom_band)
        # tmp_tex.z_score_filtering(z_thresh=3)

        # Ensure output directories exist before saving files
        ensure_dir_exists(os.path.dirname(output_dirs['spangy_tex_path']))
        sio.write_texture(tmp_tex, output_dirs['spangy_tex_path'])
        
        # Save frecomposed data
        # Use path from directories module
        bands_dir = os.path.join(output_dirs['frecomposed_dir'], "bands")
        full_dir = os.path.join(output_dirs['frecomposed_dir'], "full")
        
        # Create all directories, ensuring they exist
        os.makedirs(output_dirs['frecomposed_dir'], exist_ok=True)
        os.makedirs(bands_dir, exist_ok=True)
        os.makedirs(full_dir, exist_ok=True)
        
        # Convert each band of frecomposed to a texture and save it
        # for i in range(frecomposed.shape[1]):
        #     band_data = frecomposed[:, i]
        #     band_tex = stex.TextureND(band_data)
        #     band_path = os.path.join(bands_dir, f'frecomposed_band{i+1}_{filename}.gii')
        #     sio.write_texture(band_tex, band_path)
            
        # Also save the full frecomposed array as a numpy file for future analysis
        np_path = os.path.join(full_dir, f'frecomposed_full_{filename}.npy')
        np.save(np_path, frecomposed)
        
        # Get hull area and gyrification index
        gyrification_index, hull_area = get_gyrification_index(mesh)

        # Calculate coverage for bands 4, 5, 6 and 7
        band_vertices = []
        band_vertex_percentages = []
        band_areas = []
        band_area_percentages = []
        
        max_band = np.max(loc_dom_band)  # Get the highest available band
        
        for band_idx in [4, 5, 6]:
            if band_idx <= max_band:
                num_verts, vert_pct, area, area_pct = calculate_band_coverage(mesh, loc_dom_band, band_idx)
            else:
                # Set zeros for unavailable bands
                num_verts, vert_pct, area, area_pct = 0, 0, 0, 0
            
            band_vertices.append(num_verts)
            band_vertex_percentages.append(vert_pct)
            band_areas.append(area)
            band_area_percentages.append(area_pct)
        
        band_powers = []
        band_rel_powers = []        
        for band_idx in [4, 5, 6]:
            if band_idx < len(grouped_spectrum):
                band_powers.append(grouped_spectrum[band_idx])
                band_rel_powers.append(grouped_spectrum[band_idx]/afp)
            else:
                band_powers.append(0)
                band_rel_powers.append(0)

        # Calculate and print execution time for this iteration
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"\nExecution time for {filename}: {execution_time:.2f} seconds")
        print("----------------------------------------\n")
        
        # Create result dictionary with all the requested measures
        result = {
            'participant_session': participant_session,
            'gestational_age': gestational_age,
            'total_mean_curvature': total_mean_curv,
            'gyrification_index': gyrification_index,
            'hull_area': hull_area,
            'volume_ml': np.floor(volume / mL_in_MM3),
            'surface_area_cm2': np.floor(surface_area / CM2_in_MM2),
            'analyze_folding_power': afp,
            'processing_time': execution_time,
            "B4_band_relative_power" : band_rel_powers[0],
            "B5_band_relative_power": band_rel_powers[1], 
            "B6_band_relative_power": band_rel_powers[2],
            "B4_number_of_vertices" : band_vertices[0],
            "B5_number_of_vertices": band_vertices[1], 
            "B5_number_of_vertices" : band_vertices[2], 
            # f.write(f"B7: {band_vertices[3]} vertices ({band_vertex_percentages[3]:.2f}%)\n")
            "B4_vertex_percentage" : band_vertex_percentages[0],
            "B5_vertex_percentage" : band_vertex_percentages[1],
            "B6_vertex_percentage" : band_vertex_percentages[2], 
            "B4_surface_area": band_areas[0],
            "B5_surface_area": band_areas[1], 
            "B6_surface_area": band_areas[2], 
            "B4_surface_area_percentage": band_area_percentages[0],
            "B5_surface_area_percentage": band_area_percentages[1],
            "B6_surface_area_percentage": band_area_percentages[2]
        }
        
        # Add band power data
        for i in range(levels):
            result[f'band_power_B{i}'] = grouped_spectrum[i]
            result[f'band_power_pct_B{i}'] = power_distribution[i]
            result[f'band_wavelength_B{i}'] = band_wavelengths[i]
            result[f'band_parcels_B{i}'] = parcels_per_band[i]
        
        return result
        
    except Exception as e:
        print("Error processing {}: {}".format(filename, str(e)))
        import traceback
        traceback.print_exc()
        return None