import os
import sys
import re
import cv2
import numpy as np
from PIL import Image

# =====================================================================
# 1. OPENSLIDE INITIALIZATION (WINDOWS SPECIFIC)
# =====================================================================
OPENSLIDE_PATH = r"c:\openslide-win64\bin"

if os.path.exists(OPENSLIDE_PATH):
    # Add OpenSlide to DLL search path for Python 3.8+
    if hasattr(os, 'add_dll_directory'):
        with os.add_dll_directory(OPENSLIDE_PATH):
            import openslide
    else:
        os.environ['PATH'] = OPENSLIDE_PATH + ';' + os.environ['PATH']
        import openslide
    print("[INFO] OpenSlide library successfully loaded.")
else:
    print(f"[ERROR] OpenSlide not found at {OPENSLIDE_PATH}.")
    sys.exit(1)

# =====================================================================
# 2. MAIN EXTRACTION FUNCTION
# =====================================================================
def extract_all_tissue_patches(svs_path, patch_size=512, white_thresh=225, black_thresh=20, min_tissue_coverage=40.0):
    """
    Reads an SVS file, scans the entire slide, filters out background/artifacts 
    using a pixel-coverage strategy, and saves ALL valid tissue patches 
    in a subfolder next to the original SVS file.
    
    Parameters:
        svs_path (str): Full path to the .svs file.
        patch_size (int): Resolution of the extracted square patch (e.g., 512x512).
        white_thresh (int): Upper bound for pixel intensity (ignore white background).
        black_thresh (int): Lower bound for pixel intensity (ignore black slide edges).
        min_tissue_coverage (float): Minimum percentage of the patch that MUST contain tissue (0 to 100).
    """
    
    # 2.1 Validate File Existence
    if not os.path.exists(svs_path):
        print(f"[ERROR] File does not exist: {svs_path}")
        return False

    # 2.2 Define Output Directory (Next to the SVS file)
    svs_dir = os.path.dirname(svs_path)
    svs_filename = os.path.basename(svs_path)
    base_name = os.path.splitext(svs_filename)[0].split('.', 1)[0] # Filename without .svs extension
    
    output_dir = os.path.join(svs_dir, f"{base_name}SVS_patches")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[START] Processing WSI: {svs_filename}")
    print(f"        Output directory: {output_dir}")
    print(f"        Tissue coverage threshold: >= {min_tissue_coverage}%")

    saved_patches_count = 0

    try:
        # Handle Windows long paths safely
        safe_path = os.path.abspath(svs_path)
        if os.name == 'nt' and not safe_path.startswith('\\\\?\\'): 
            safe_path = f'\\\\?\\{safe_path}'

        # 2.3 Open the Slide
        slide = openslide.OpenSlide(safe_path)
        
        # 2.4 Determine Extraction Level 
        # Using Level 1 (if available) is standard for Deep Learning to save processing time
        # while keeping cellular details. If only Level 0 exists, use Level 0.
        level = 1 if slide.level_count > 1 else 0
        w, h = slide.level_dimensions[level]
        downsample_factor = slide.level_downsamples[level]
        
        print(f"        -> Slide Dimensions (Level {level}): Width={w}, Height={h}")
        print(f"        -> Scanning for valid tissue patches... This may take a while.")

        # 2.5 Grid Iteration over the Slide
        for y in range(0, h, patch_size):
            for x in range(0, w, patch_size):
                
                try:
                    # Calculate coordinates relative to Level 0 (Required by OpenSlide)
                    start_x = int(x * downsample_factor)
                    start_y = int(y * downsample_factor)
                    
                    # Read the region and convert to standard RGB image
                    patch_pil = slide.read_region(
                        (start_x, start_y), 
                        level, 
                        (patch_size, patch_size)
                    ).convert("RGB")
                    
                    patch_np = np.array(patch_pil)
                    
                    # =========================================================
                    # 2.6 ADVANCED Tissue Filtering (Coverage Based)
                    # =========================================================
                    # Convert to grayscale to evaluate pixel intensity
                    gray_patch = cv2.cvtColor(patch_np, cv2.COLOR_RGB2GRAY)
                    
                    # Create a boolean mask of pixels that are "tissue-like" 
                    # (Neither absolute black edges nor absolute white background)
                    valid_tissue_mask = (gray_patch > black_thresh) & (gray_patch < white_thresh)
                    
                    # Calculate the percentage of the patch that is covered by valid tissue
                    tissue_coverage_percentage = np.mean(valid_tissue_mask) * 100
                    
                    # Check if the patch meets the minimum tissue requirement
                    if tissue_coverage_percentage >= min_tissue_coverage:
                        
                        # Format output filename (e.g., patch_x512_y1024.jpg)
                        patch_filename = f"patch_x{x}_y{y}.jpg"
                        out_path = os.path.join(output_dir, patch_filename)
                        
                        # Save image with high quality for medical deep learning
                        patch_pil.save(out_path, format='JPEG', quality=95)
                        saved_patches_count += 1
                        
                        # Print progress periodically to track performance
                        if saved_patches_count % 100 == 0:
                            print(f"        -> Extracted {saved_patches_count} pure tissue patches so far...")

                except Exception as inner_e:
                    # Silently skip corrupted regions
                    continue
                    
        # 2.7 Clean up Memory
        slide.close()
        
        print(f"[SUCCESS] Finished! Total purely tissue patches extracted: {saved_patches_count}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to process {svs_filename}: {str(e)}")
        return False

# =====================================================================
# 3. BATCH PROCESSING FUNCTION (NEW)
# =====================================================================
def process_all_patients_in_directory(parent_dir, patch_size=512, white_thresh=225, black_thresh=20, min_tissue_coverage=40.0):
   
    
    # Check if the parent directory exists
    if not os.path.exists(parent_dir):
        print(f"[ERROR] The specified directory does not exist: {parent_dir}")
        return

    print(f"\n🔍 Scanning directory for .svs files: {parent_dir}")
    
    # List to store all found .svs file paths
    svs_files_list = []
    
    # os.walk automatically enters every subfolder and scans for files
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if file.lower().endswith('.svs'):
                full_path = os.path.join(root, file)
                svs_files_list.append(full_path)
                
    total_files = len(svs_files_list)
    
    if total_files == 0:
        print("[WARNING] No .svs files were found in the specified directory.")
        return
        
    print(f"✅ Found {total_files} .svs file(s). Starting batch processing...")
    
    successful_count = 0
    failed_count = 0
    
    # Loop through each found .svs file and process it
    for index, svs_path in enumerate(svs_files_list, start=1):
        print(f"\n{'='*60}")
        print(f"▶️ Processing File [{index}/{total_files}]")
        print(f"{'='*60}")
        
        # Call the main extraction function
        success = extract_all_tissue_patches(
            svs_path=svs_path,
            patch_size=patch_size,
            white_thresh=white_thresh,
            black_thresh=black_thresh,
            min_tissue_coverage=min_tissue_coverage
        )
        
        if success:
            successful_count += 1
        else:
            failed_count += 1
            
    # Final Summary Report
    print(f"\n🎉 ================= BATCH PROCESS COMPLETE =================")
    print(f"Total files scanned: {total_files}")
    print(f"Successfully processed: {successful_count}")
    print(f"Failed to process: {failed_count}")
    print(f"===========================================================\n")


# =====================================================================
# 4. EXECUTION EXAMPLE
# =====================================================================
if __name__ == "__main__":
    
    # 🌟 مسیر فولدر اصلی (پوشه‌ای که داخلش پوشه بیماران قرار دارد) را اینجا بگذارید
    # Insert the path to the main directory containing all patient folders
    MAIN_DATASET_DIR = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA"
    
    # Run the batch processor
    process_all_patients_in_directory(
        parent_dir=MAIN_DATASET_DIR,
        patch_size=512, 
        white_thresh=225,          # Stricter white background filter
        black_thresh=20,           # Filter out black slide edges
        min_tissue_coverage=40.0   # At least 40% of the patch must be real tissue
    )