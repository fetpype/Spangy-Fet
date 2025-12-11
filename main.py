import os
import pandas as pd
import numpy as np
import sys
from utils import ensure_dir_exists
from spangy_analysis import process_single_file
from directories import output_directories, input_directories


def main():
    try:
        # Get all paths from directories module
        input_dirs = input_directories()
        output_dirs = output_directories()
        
        surface_path = output_dirs['mesh_save_path']
        mesh_info_path = input_dirs['mesh_info_path']
        
        # Ensure all output directories exist
        ensure_dir_exists(output_dirs['principal_tex_dir'])
        ensure_dir_exists(output_dirs['mean_tex_dir'])
        ensure_dir_exists(output_dirs['plots_dir'])
        ensure_dir_exists(os.path.dirname(output_dirs['spangy_tex_path'])) if output_dirs['spangy_tex_path'] else None
        ensure_dir_exists(output_dirs['output_folder'])
        
        print("Reading data from {}".format(mesh_info_path))
        
        # Read dataframe
        df = pd.read_csv(mesh_info_path, sep='\t')
        df['participant_session'] = df['subject_id'] + '_' + df['session_id']
        
        print("Scanning directory: {}".format(surface_path))
        
        # Get list of files
        all_files = [f for f in os.listdir(surface_path) if f.endswith('left.surf.gii') or f.endswith('right.surf.gii')]
        print("Found {} files to process".format(len(all_files)))
        
        # Process directly if not in SLURM environment
        if 'SLURM_ARRAY_TASK_ID' not in os.environ:
            print("Running in local mode - processing all files")
            results = []
            
            for filename in all_files:
                result = process_single_file(filename, surface_path, df)
                if result:
                    results.append(result)
            
            if results:
                results_df = pd.DataFrame(results)
                results_df.to_csv(output_dirs['output_csv_file'], index=False)
                print(f"All results saved to {output_dirs['output_csv_file']}")
            else:
                print("Warning: No results generated")
            
            return
        
        # Calculate chunk for this array task
        task_id = int(os.environ['SLURM_ARRAY_TASK_ID'])
        n_tasks = int(os.environ['SLURM_ARRAY_TASK_COUNT'])
        
        chunk_size = len(all_files) // n_tasks + (1 if len(all_files) % n_tasks > 0 else 0)
        start_idx = task_id * chunk_size
        end_idx = min((task_id + 1) * chunk_size, len(all_files))
        
        print("Processing chunk {}/{} (files {} to {})".format(task_id + 1, n_tasks, start_idx, end_idx))
        
        # Process files in this chunk
        results = []
        for filename in all_files[start_idx:end_idx]:
            result = process_single_file(filename, surface_path, df)
            if result:
                results.append(result)
        
        # Save results for this chunk
        if results:
            results_df = pd.DataFrame(results)
            chunk_file = os.path.join(output_dirs['output_folder'], 'chunk_{}_results.csv'.format(task_id))
            results_df.to_csv(chunk_file, index=False)
            print("Results for chunk {} saved to {}".format(task_id, chunk_file))
        else:
            print("Warning: No results generated for chunk {}".format(task_id))
    
    except Exception as e:
        print("Critical error in main: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()