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
    
    # فایل CSV را همین ابتدا باز میکنیم تا در حین کار در آن بنویسیم
    with open(csv_report_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["submitter_id", "Missing Files"]) # نوشتن هدر ستون ها
        
        for patient_id in tqdm(patient_ids, desc="Processing Patients", unit="patient"):
            patient_dir = os.path.join(base_folder, patient_id)
            
            missing_before = check_missing_files(patient_dir)
            
            if not missing_before:
                # نوشتن وضعیتِ بیمار کامل، در لحظه درون فایل CSV
                writer.writerow([patient_id, "None (All complete)"])
                csv_file.flush() # اجبار به ذخیره آنی روی هارد دیسک
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
            
            # بررسی مجدد فایل ها پس از تلاش برای دانلود
            missing_after = check_missing_files(patient_dir)
            
            # ثبت وضعیت نهایی بیمار در فایل CSV
            if missing_after:
                writer.writerow([patient_id, ", ".join(missing_after)])
                tqdm.write(f"[-] Still missing files for {patient_id}: {', '.join(missing_after)}")
            else:
                writer.writerow([patient_id, "None (All complete)"])
                tqdm.write(f"[+] All files successfully downloaded for {patient_id}")
            
            # بسیار مهم: پس از پردازش هر بیمار، اطلاعات را فورا در دیسک ذخیره میکنیم
            csv_file.flush()
            os.fsync(csv_file.fileno()) # اطمینان 100 درصدی از نوشته شدن روی هارد

    print(f"\n[+] Process complete! Real-time report finished at '{csv_report_path}'.")

if __name__ == "__main__":
    main()