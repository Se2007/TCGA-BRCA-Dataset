import pandas as pd
import numpy as np
import re

def tcga_vacuum_cleaner(patient_file, drug_file, missing_threshold=0.5):
    print("🧹 Starting the TCGA Vacuum Cleaner...\n")
    
    tcga_nulls = [
        '[Not Available]', '[Not Applicable]', '[Unknown]', 
        '[Not Evaluated]', '[Discrepancy]', 'CDE_ID:'
    ]
    
    # ==========================================
    # ==========================================
    print("💊 Processing Drugs Data...")
    df_drug = pd.read_csv(drug_file, sep='\t', skiprows=[1, 2], na_values=tcga_nulls)
    
    drug_col = [col for col in df_drug.columns if 'drug_name' in col.lower()][0]
    
    df_drug['bcr_patient_barcode'] = df_drug['bcr_patient_barcode'].astype(str).str[0:12]
    
    df_drug = df_drug.dropna(subset=[drug_col])
    
    drugs_grouped = df_drug.groupby('bcr_patient_barcode')[drug_col].apply(
        lambda x: '|'.join(x.dropna().unique())
    ).reset_index()
    
    drugs_encoded = drugs_grouped[drug_col].str.get_dummies(sep='|')
    drugs_encoded = drugs_encoded.add_prefix('Drug_')
    drugs_final = pd.concat([drugs_grouped['bcr_patient_barcode'], drugs_encoded], axis=1)
    
    # ==========================================
    # ==========================================
    print("🧬 Processing Patient Clinical Data...")
    df_patient = pd.read_csv(patient_file, sep='\t', skiprows=[1, 2], na_values=tcga_nulls)
    
    age_cols = [c for c in df_patient.columns if 'birth' in c.lower() and 'days' in c.lower()]
    for col in age_cols:
        df_patient[col] = pd.to_numeric(df_patient[col], errors='coerce')
        df_patient['Age_in_Years'] = (df_patient[col].abs() / 365.25).apply(np.floor)
        df_patient.drop(columns=[col], inplace=True) 
        
    # ==========================================
    # ==========================================
    print("🔗 Merging Datasets...")
    master_df = pd.merge(df_patient, drugs_final, on='bcr_patient_barcode', how='left')
    
    drug_columns = [col for col in master_df.columns if col.startswith('Drug_')]
    master_df[drug_columns] = master_df[drug_columns].fillna(0).astype(int)
    
    trash_keywords = ['uuid', 'form_completion', 'cde_id', 'icd_']
    cols_to_drop = [col for col in master_df.columns if any(k in col.lower() for k in trash_keywords)]
    master_df.drop(columns=cols_to_drop, inplace=True)
    
    print(f"🗑️ Dropping columns with > {missing_threshold*100}% missing values...")
    threshold_count = int((1 - missing_threshold) * len(master_df))
    master_df = master_df.dropna(thresh=threshold_count, axis=1)
    
    master_df.dropna(subset=['bcr_patient_barcode'], inplace=True)
    
    print(f"✅ Vacuuming Complete! Final Dataset Shape: {master_df.shape}")
    return master_df

# ==========================================
# ==========================================
patient_txt = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA\TCGA-AR-A1AN\nationwidechildrens.org_clinical_patient_brca.txt"  # "D:\TCGA-BRCA\TCGA-AO-A0J8\nationwidechildrens.org_clinical_patient_brca.txt"  
drug_txt = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA\TCGA-AR-A1AN\nationwidechildrens.org_clinical_drug_brca.txt"  # "D:\TCGA-BRCA\TCGA-AO-A0J8\nationwidechildrens.org_clinical_drug_brca.txt" 

ml_ready_df = tcga_vacuum_cleaner(patient_txt, drug_txt, missing_threshold=0.5)

ml_ready_df.to_csv('ML_Ready_TCGA_BRCA.csv', index=False)
print("💾 File saved as 'ML_Ready_TCGA_BRCA.csv'")