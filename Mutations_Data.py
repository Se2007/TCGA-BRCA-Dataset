import pandas as pd
import os
import glob

def build_master_mutation_dataset(base_dir, output_csv_path):
    print(f"[INFO] Scanning '{base_dir}' for MAF files...")
    
    maf_files = glob.glob(os.path.join(base_dir, "**", "*.maf*"), recursive=True)
    
    if not maf_files:
        print("[WARNING] No MAF files found in the specified directory.")
        return
        
    print(f"[INFO] Found {len(maf_files)} MAF files. Processing...")
    
    all_patients_data = []
    
    for file_path in maf_files:
        try:
            df = pd.read_csv(file_path, sep='\t', comment='#', low_memory=False)
            
            df['Patient_ID'] = df['Tumor_Sample_Barcode'].str[:12]
            
            aggregated_df = df.groupby('Patient_ID').agg(
                Total_Mutations=('Hugo_Symbol', 'count'),
                Mutated_Genes=('Hugo_Symbol', lambda x: '|'.join(x.dropna().unique()))
            ).reset_index()
            
            all_patients_data.append(aggregated_df)
            print(f"[OK] Processed: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"[ERROR] Failed on {os.path.basename(file_path)}: {e}")
    
    if all_patients_data:
        master_df = pd.concat(all_patients_data, ignore_index=True)
        
        master_df = master_df.groupby('Patient_ID').agg({
            'Total_Mutations': 'sum',
            'Mutated_Genes': lambda x: '|'.join(set('|'.join(x).split('|'))) 
        }).reset_index()

        master_df.to_csv(output_csv_path, index=False)
        print("\n" + "="*60)
        print(f"[SUCCESS] Master dataset created with {master_df.shape[0]} unique patients!")
        print(f"[SUCCESS] Saved to: {output_csv_path}")
        print("="*60)

if __name__ == "__main__":
    BASE_DIR = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA"
    
    MASTER_OUTPUT = r"D:\TCGA-BRCA\Master_Mutations_Dataset.csv"
    
    build_master_mutation_dataset(BASE_DIR, MASTER_OUTPUT)