import os
import csv
from tqdm import tqdm

import multiomics_downloader as gdc

def check_missing_files(patient_dir):
    missing_files = []
    
    if not os.path.exists(patient_dir):
        return ["Directory not found"]
        
    downloaded_files = [f.lower() for f in os.listdir(patient_dir) if os.path.isfile(os.path.join(patient_dir, f))]
    
    if not any(f.endswith('.json') for f in downloaded_files):
        missing_files.append("Clinical JSON")
        
    if not any('masked' in f for f in downloaded_files):
        missing_files.append("Masked MAF")
        
    if not any('rna_seq.augmented_star_gene_counts.tsv' in f for f in downloaded_files):
        missing_files.append("RNA Seq TSV")
    if not any('gene_level_copy_number.v36.tsv' in f for f in downloaded_files):
        missing_files.append("Copy Number TSV")
        
    if not any('clinical_drug' in f for f in downloaded_files):
        missing_files.append("BCR Clinical Drug")
    if not any('clinical_patient' in f for f in downloaded_files):
        missing_files.append("BCR Clinical Patient")
        
    if not any(f.endswith('.svs') for f in downloaded_files):
        missing_files.append("Diagnostic Slide (SVS)")
        
    return missing_files

def main():
    base_folder = "./manifest-25vRPwyh8987165612391086998/TCGA-BRCA" 
    csv_report_path = "missing_files_report.csv"
    
    if not os.path.exists(base_folder):
        print(f"[-] Base directory '{base_folder}' not found!")
        return

    try:
        patient_ids = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
    except Exception as e:
        print(f"[-] Error reading base folder: {e}")
        return

    if not patient_ids:
        print("[-] No patient folders found in the base directory.")
        return

    print(f"[*] Found {len(patient_ids)} patient folders. Starting/Resuming downloads...")
    
    report_data = []

    for patient_id in tqdm(patient_ids, desc="Processing Patients", unit="patient"):
        patient_dir = os.path.join(base_folder, patient_id)
        
        missing_before = check_missing_files(patient_dir)
        
        if not missing_before:
            report_data.append([patient_id, "None (All complete)"])
            continue 
            
        tqdm.write(f"\n{'='*50}\n[*] Processing Patient: {patient_id}")
        tqdm.write(f"[*] Missing items to download: {', '.join(missing_before)}")
      
        
        # 1. Clinical JSON
        if "Clinical JSON" in missing_before:
            url = gdc.open_gdc_case_page(patient_id)
            if url:
                try:
                    gdc.download_clinical_via_scraping(url, save_dir=patient_dir)
                except Exception as e:
                    tqdm.write(f"[-] Scraping error for {patient_id}: {e}")
                
        # 2. MAF
        if "Masked MAF" in missing_before:
            gdc.download_maf_file_via_api(patient_id, save_dir=patient_dir)
        
        # 3. TSV
        if "RNA Seq TSV" in missing_before or "Copy Number TSV" in missing_before:
            gdc.download_specific_tsv_files_via_api(patient_id, save_dir=patient_dir)
        
        # 4. BCR Biotab
        if "BCR Clinical Drug" in missing_before or "BCR Clinical Patient" in missing_before:
            gdc.download_clinical_bcr_biotab_via_api(patient_id, save_dir=patient_dir)
        
        # 5. SVS
        if "Diagnostic Slide (SVS)" in missing_before:
            gdc.download_diagnostic_slide_via_api(patient_id, save_dir=patient_dir)
        
       
        missing_after = check_missing_files(patient_dir)
        
        if missing_after:
            report_data.append([patient_id, ", ".join(missing_after)])
            tqdm.write(f"[-] Still missing files for {patient_id}: {', '.join(missing_after)}")
        else:
            report_data.append([patient_id, "None (All complete)"])
            tqdm.write(f"[+] All files successfully downloaded for {patient_id}")


    print(f"\n[*] Generating CSV report: {csv_report_path}")
    with open(csv_report_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["submitter_id", "Missing Files"]) 
        writer.writerows(report_data)
        
    print(f"[+] Process complete! Report saved to '{csv_report_path}'.")

if __name__ == "__main__":
    main()