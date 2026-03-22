import pandas as pd
import os
import glob

def build_separated_raw_datasets(base_dir, rna_output_path, cnv_output_path):
    print(f"[INFO] Scanning directory: {base_dir}")
    
    # پیدا کردن فایل‌های RNA و CNV
    rna_files = glob.glob(os.path.join(base_dir, "**", "*.rna_seq.augmented_star_gene_counts.tsv"), recursive=True)
    cnv_files = glob.glob(os.path.join(base_dir, "**", "*.gene_level_copy_number.*.tsv"), recursive=True)
    
    print(f"[INFO] Found {len(rna_files)} RNA-Seq files and {len(cnv_files)} CNV files.")
    
    # ==========================================
    # 1. PROCESS RNA (RAW)
    # ==========================================
    rna_list = []
    if rna_files:
        print("[INFO] Processing Raw RNA-Seq files...")
        for f in rna_files:
            try:
                patient_id = os.path.basename(os.path.dirname(f))
                df = pd.read_csv(f, sep='\t', comment='#', usecols=['gene_name', 'tpm_unstranded'], low_memory=False)
                df = df.dropna(subset=['gene_name', 'tpm_unstranded'])
                df = df.groupby('gene_name', as_index=False)['tpm_unstranded'].mean()
                
                df_wide = df.set_index('gene_name').T
                df_wide.columns = [f"RNA_{col}" for col in df_wide.columns]
                df_wide['Patient_ID'] = patient_id
                rna_list.append(df_wide)
            except Exception as e:
                print(f"[ERROR] Processing RNA file {f}: {e}")

    # ==========================================
    # 2. PROCESS CNV (RAW)
    # ==========================================
    cnv_list = []
    if cnv_files:
        print("[INFO] Processing Raw CNV files...")
        for f in cnv_files:
            try:
                patient_id = os.path.basename(os.path.dirname(f))
                df = pd.read_csv(f, sep='\t', comment='#', usecols=['gene_name', 'copy_number'], low_memory=False)
                df = df.dropna(subset=['gene_name', 'copy_number'])
                df = df.groupby('gene_name', as_index=False)['copy_number'].mean()
                
                df_wide = df.set_index('gene_name').T
                df_wide.columns = [f"CNV_{col}" for col in df_wide.columns]
                df_wide['Patient_ID'] = patient_id
                cnv_list.append(df_wide)
            except Exception as e:
                print(f"[ERROR] Processing CNV file {f}: {e}")

    # ==========================================
    # 3. SAVE SEPARATE FILES
    # ==========================================
    print("[INFO] Consolidating and Saving DataFrames...")

    # --- ذخیره فایل RNA ---
    if rna_list:
        master_rna = pd.concat(rna_list, ignore_index=True)
        # انتقال Patient_ID به ابتدای ستون‌ها
        cols = master_rna.columns.tolist()
        cols.insert(0, cols.pop(cols.index('Patient_ID')))
        master_rna = master_rna[cols]
        
        print(f"[INFO] Saving RNA Dataset to CSV...")
        master_rna.to_csv(rna_output_path, index=False)
        print(f"  -> RNA Data Saved: {master_rna.shape[0]} Patients, {master_rna.shape[1] - 1} Genes")
    else:
        print("[WARNING] No RNA data processed.")

    # --- ذخیره فایل CNV ---
    if cnv_list:
        master_cnv = pd.concat(cnv_list, ignore_index=True)
        # انتقال Patient_ID به ابتدای ستون‌ها
        cols = master_cnv.columns.tolist()
        cols.insert(0, cols.pop(cols.index('Patient_ID')))
        master_cnv = master_cnv[cols]
        
        print(f"[INFO] Saving CNV Dataset to CSV...")
        master_cnv.to_csv(cnv_output_path, index=False)
        print(f"  -> CNV Data Saved: {master_cnv.shape[0]} Patients, {master_cnv.shape[1] - 1} Genes")
    else:
        print("[WARNING] No CNV data processed.")

    print("=" * 80)
    print(f"[SUCCESS] Datasets successfully separated and saved!")
    print("=" * 80)

if __name__ == "__main__":
    BASE_DIR = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA"
    
    # تعیین دو مسیر مجزا برای خروجی‌ها
    RNA_OUTPUT_CSV = r"D:\TCGA-BRCA\RNA_RAW.csv"
    CNV_OUTPUT_CSV = r"D:\TCGA-BRCA\CNV_RAW.csv"
    
    build_separated_raw_datasets(BASE_DIR, RNA_OUTPUT_CSV, CNV_OUTPUT_CSV)