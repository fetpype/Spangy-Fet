# Quick Reference Guide - Using Directories Module

## File Overview

### Installation and set-up
First create a virtual env

```bash
conda create --name devfet python=3.8.2

pip install brain-slam

pip install numpy==1.19

pip install matplotlib==3.4.3

pip install pandas==1.4.4

pip install seaborn==0.11.2

pip install plotly==5.5.0

pip install -U kaleido

pip install dash
```

### 1. directories.py
**Purpose**: Central configuration for all directory paths  
**Functions**:
- `input_directories()` - Returns input paths (surface data, mesh info)
- `output_directories(filename, participant_session)` - Returns output paths

### 2. mean_curvature.py
**Purpose**: Generate and save mean curvature for all meshes  
**How it uses directories**:
```python
from directories import output_directories, input_directories

# Get paths
input_dirs = input_directories()
output_dirs = output_directories(filename=filename, participant_session=participant_session)

# Use them
surface_path = input_dirs['surface_path']
mean_curv_output = output_dirs['mean_tex_path']
```

### 3. dpf_star.py
**Purpose**: Generate and save DPF textures using mean curvature  
**How it uses directories**:
```python
from directories import output_directories

# Get paths
output_dirs = output_directories(filename=filename, participant_session=participant_session)

# Use them
mean_curv_input = output_dirs['mean_tex_path']
dpf_output = output_dirs['dpf_tex_dir']
```

### 4. dpf_star_snapshots.py
**Purpose**: Generate and save snapshots of DPF textures on the mesh  
**How it uses directories**:
```python
from directories import output_directories

# Get paths
output_dirs = output_directories(filename=filename, participant_session=participant_session)

# Use them
mesh_path = output_dirs['mesh_save_path']
dpf_tex = output_dirs['dpf_tex_dir']
snapshot_output = output_dirs['dpf_snapshots_path']
```

### 5. main.py
**Purpose**: Main SPANGY processing script  
**How it uses directories**:
```python
from directories import output_directories, input_directories

# Get paths
input_dirs = input_directories()
output_dirs = output_directories()

# Use them
surface_path = input_dirs['surface_path']
mesh_info_path = input_dirs['mesh_info_path']
output_file = output_dirs['output_csv_file']
```

### 6. spangy_analysis.py (process_single_file)
**Purpose**: Process individual surface files for SPANGY analysis  
**How it uses directories**:
```python
from directories import output_directories

# Get paths with file-specific info
output_dirs = output_directories(filename=filename, participant_session=participant_session)

# Use them
mesh_save_path = output_dirs['mesh_save_path']
principal_tex_path = output_dirs['principal_tex_path']
spangy_tex_path = output_dirs['spangy_tex_path']
```

### 7. spangy_snapshot_updated.py
**Purpose**: Generate and save screenshots of SPANGY textures on the mesh  
**How it uses directories**:
```python
from directories import output_directories

# Get paths
output_dirs = output_directories(filename=filename, participant_session=participant_session)

# Use them
mesh_path = output_dirs['mesh_save_path']
spangy_tex = output_dirs['spangy_tex_path']
```

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                      directories.py                          │
│  • Defines all input/output paths                           │
│  • input_directories() → surface_path, mesh_info_path       │
│  • output_directories() → all output directories            │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼───────────┐                               │
│  STEP 1:          │                               │
│  mean_curvature.py│                               │
│  • Gets input     │                               │
│  • Calculates     │                               │
│  • Saves mean_tex │                               │
└───────┬───────────┘                               │
        │                                           │
        ▼                                           │
┌───────────────────┐                               │
│  STEP 2:          │                               │
│  dpf_star.py      │                               │
│  • Reads mean_tex │                               │
│  • Generates DPF  │                               │
│  • Saves dpf_tex  │                               │
└───────┬───────────┘                               │
        │                                           │
        ▼                                           │
┌──────────────────────┐                            │
│  STEP 3:             │                            │
│  dpf_star_snapshots  │                            │
│  • Reads mesh & DPF  │                            │
│  • Generates images  │                            │
│  • Saves snapshots   │                            │
└──────────────────────┘                            │
                                                    │
┌───────────────────┐                  ┌────────────▼────────┐
│  STEP 4:          │                  │  spangy_analysis.py │
│  main.py          │                  │  • Gets output paths│
│  • Gets input     │                  │  • SPANGY processing│
│  • Loads mesh data│──────────────────▶  • Spectral analysis│
│  • Calls processor│                  │  • Saves textures   │
│  • Saves final CSV│                  │                     │
└───────────────────┘                  └─────────────────────┘
                                                    │
                                                    ▼
                                       ┌───────────────────────┐
                                       │  STEP 5:              │
                                       │  spangy_snapshot      │
                                       │  _updated.py          │
                                       │  • Reads mesh & SPANGY│
                                       │  • Generates images   │
                                       │  • Saves snapshots    │
                                       └───────────────────────┘
```

## Directory Structure Created

```
/scratch/hdienye/dhcp_full_info/
├── mesh/                          # Smoothed meshes
├── principal_curv_tex/            # Principal curvature textures
├── mean_curv_tex/                 # Mean curvature textures
├── dpf/
│   ├── textures/                  # DPF texture files
│   └── snapshots/                 # DPF visualization snapshots
├── spangy/
│   ├── plots/                     # Visualization plots
│   ├── textures/                  # Spangy texture files
│   └── snapshots/                 # SPANGY visualization snapshots
├── frecomposed/
│   ├── bands/                     # Band-specific data
│   └── full/                      # Full frecomposed arrays
└── info/
    ├── all_results.csv            # Combined results (local mode)
    └── chunk_*_results.csv        # Chunk results (SLURM mode)
```

## Quick Start

1. **Ensure all files are in the same directory:**
   ```
   your_project/
   ├── directories.py
   ├── mean_curvature.py
   ├── dpf_star.py
   ├── dpf_star_snapshots.py
   ├── main.py
   ├── spangy_analysis.py
   ├── spangy_snapshot_updated.py
   └── utils.py
   ```

2. **Run the processing pipeline in order:**
   ```bash
   # Step 1: Generate mean curvature
   python mean_curvature.py
   
   # Step 2: Generate DPF textures
   python dpf_star.py
   
   # Step 3: Generate DPF snapshots
   python dpf_star_snapshots.py
   
   # Step 4: Run main SPANGY analysis
   # Local mode (process all files)
   python main.py
   
   # OR SLURM mode (parallel processing)
   sbatch --array=0-9 your_job.sh
   
   # Step 5: Generate SPANGY snapshots
   python spangy_snapshot_updated.py
   ```

3. **To change a directory path:**
   - Open `directories.py`
   - Update the path in the appropriate function
   - Save - all scripts automatically use the new path!

## Available Paths

### From `input_directories()`:
- `surface_path` - Location of surface files
- `mesh_info_path` - Path to participants.tsv

### From `output_directories()`:
- `mesh_save_path` - Smoothed mesh output
- `principal_tex_dir` - Principal curvature textures folder
- `principal_tex_path` - Specific principal curvature file
- `mean_tex_dir` - Mean curvature textures folder
- `mean_tex_path` - Specific mean curvature file
- `dpf_tex_dir` - DPF textures folder
- `plots_dir` - Plots output folder
- `spangy_tex_path` - Specific spangy texture file
- `frecomposed_dir` - Frecomposed data folder
- `output_folder` - General output folder
- `output_csv_file` - Final CSV results file

## Processing Pipeline Details

### Phase 1: Curvature & DPF (Pre-SPANGY)
1. **mean_curvature.py** - Calculates baseline curvature measures
2. **dpf_star.py** - Generates DPF features from curvature
3. **dpf_star_snapshots.py** - Creates visual verification of DPF

### Phase 2: SPANGY Analysis (Main Processing)
4. **main.py + spangy_analysis.py** - Spectral decomposition and analysis

### Phase 3: Visualization (Post-SPANGY)
5. **spangy_snapshot_updated.py** - Creates visual verification of SPANGY results

## Example: Adding a New Output Directory

1. **Edit directories.py:**
   ```python
   def output_directories(filename=None, participant_session=None):
       # ... existing code ...
       
       # Add your new directory
       my_new_dir = "/scratch/hdienye/dhcp_full_info/my_new_output/"
       
       return {
           # ... existing paths ...
           'my_new_dir': my_new_dir
       }
   ```

2. **Use it in your code:**
   ```python
   from directories import output_directories
   
   output_dirs = output_directories()
   ensure_dir_exists(output_dirs['my_new_dir'])
   ```

## Batch Processing Tips

- **For sequential processing**: Run scripts in order as shown in Quick Start
- **For parallel processing**: Use SLURM array jobs for steps 1-3 and step 5
- **Monitoring progress**: Check output directories for generated files
- **Error handling**: Each script should create its output directory if it doesn't exist