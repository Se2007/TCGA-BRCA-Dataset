import os
import re
import cv2
import numpy as np
import pydicom

# =====================================================================
# 1. MAIN MRI EXTRACTION FUNCTION (FIXED FOR MULTIPLE SCANS)
# =====================================================================
def process_patient_mri(patient_dir, output_folder_name, image_size=512, min_contrast=15):
    if not os.path.exists(patient_dir):
        print(f"[ERROR] Directory not found: {patient_dir}")
        return False

    match = re.search(r'(TCGA-[A-Z0-9]{2}-[A-Z0-9]{4})', patient_dir)
    patient_id = match.group(1) if match else "Unknown_Patient"

    output_dir = os.path.join(patient_dir, output_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    scans_dict = {}
    
    for root, dirs, files in os.walk(patient_dir):
        if output_dir in root:
            continue
            
        dcm_files = [f for f in files if f.lower().endswith('.dcm')]
        if dcm_files:
            scans_dict[root] = dcm_files

    if not scans_dict:
        print(f"[WARNING] No .dcm files found in {patient_dir}")
        return False

    print(f"\n[START] Processing Patient: {patient_id}")
    print(f"        -> Found {len(scans_dict)} distinct scan folder(s).")

    total_processed = 0
    total_skipped = 0

    for scan_path, dcm_list in scans_dict.items():
        scan_folder_name = os.path.basename(scan_path)
        print(f"        -> Processing Scan: {scan_folder_name} ({len(dcm_list)} files)")
        
        specific_scan_output_dir = os.path.join(output_dir, scan_folder_name)
        os.makedirs(specific_scan_output_dir, exist_ok=True)
        
        scan_processed_count = 0
        
        for f in dcm_list:
            try:
                dcm_path = os.path.join(scan_path, f)
                ds = pydicom.dcmread(dcm_path)
                img = ds.pixel_array.astype(float)

                if np.std(img) < min_contrast:
                    total_skipped += 1
                    continue

                if hasattr(ds, 'PhotometricInterpretation') and ds.PhotometricInterpretation == "MONOCHROME1":
                    img = np.max(img) - img

                img_max = img.max()
                if img_max > 0:
                    img = (np.maximum(img, 0) / img_max) * 255.0
                else:
                    total_skipped += 1
                    continue

                img_resized = cv2.resize(img.astype(np.uint8), (image_size, image_size))

                filename = f"{patient_id}_img_{scan_processed_count:04d}.jpg"
                out_path = os.path.join(specific_scan_output_dir, filename)
                
                cv2.imwrite(out_path, img_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                
                scan_processed_count += 1
                total_processed += 1

            except Exception as e:
                total_skipped += 1
                continue

    print(f"[SUCCESS] Finished Patient {patient_id}!")
    print(f"          Saved {total_processed} valid images.")
    print(f"          Skipped {total_skipped} dark/error images.")
    return True


# =====================================================================
# 2. BATCH PROCESSING FUNCTION (WITH RESUME & SAFE NAMING)
# =====================================================================
def process_all_patients_mri_in_directory(parent_dir, base_suffix="mri_processed", image_size=512, min_contrast=15):
    """
    پیمایش کل بیماران + قابلیت Skip کردن بیمارانی که قبلاً پردازش شده‌اند.
    """
    if not os.path.exists(parent_dir):
        print(f"[ERROR] The specified directory does not exist: {parent_dir}")
        return

    print(f"\n🔍 Scanning directory for patient folders: {parent_dir}")
    
    patient_folders = []
    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path) and re.search(r'(TCGA-[A-Z0-9]{2}-[A-Z0-9]{4})', item):
            patient_folders.append(item_path)
                
    total_patients = len(patient_folders)
    
    if total_patients == 0:
        print("[WARNING] No patient folders found.")
        return
        
    print(f"✅ Found {total_patients} patient folder(s). Starting batch processing...")
    
    successful_count = 0
    failed_count = 0
    skipped_count = 0
    
    for index, patient_dir in enumerate(patient_folders, start=1):
        patient_id = os.path.basename(patient_dir)
        
        current_output_folder_name = f"{patient_id}_{base_suffix}"
        expected_output_path = os.path.join(patient_dir, current_output_folder_name)
        
        if os.path.exists(expected_output_path) and len(os.listdir(expected_output_path)) > 0:
            print(f"\n{'='*60}")
            print(f"⏭️ SKIPPING [{index}/{total_patients}]: {patient_id} (Already Processed)")
            print(f"{'='*60}")
            skipped_count += 1
            continue

        print(f"\n{'='*60}")
        print(f"▶️ PROCESSING [{index}/{total_patients}]: {patient_id}")
        print(f"{'='*60}")

        success = process_patient_mri(
            patient_dir=patient_dir,
            output_folder_name=current_output_folder_name,
            image_size=image_size,
            min_contrast=min_contrast
        )
        
        if success:
            successful_count += 1
        else:
            failed_count += 1
            
    print(f"\n🎉 ================= BATCH PROCESS COMPLETE =================")
    print(f"Total scanned: {total_patients}")
    print(f"Successfully processed: {successful_count}")
    print(f"Skipped (Already done): {skipped_count}")
    print(f"Failed / No DICOMs: {failed_count}")
    print(f"===========================================================\n")


# =====================================================================
# 3. EXECUTION EXAMPLE
# =====================================================================
if __name__ == "__main__":
    
    MAIN_DATASET_DIR = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA"
    
    process_all_patients_mri_in_directory(
        parent_dir=MAIN_DATASET_DIR,
        base_suffix="mri_processed", 
        image_size=512,                     
        min_contrast=15                     
    )