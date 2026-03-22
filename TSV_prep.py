import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def get_uncorrelated_features(df, features, max_features=300, corr_threshold=0.80):
    """
    دریافت ویژگی‌های برتر و حذف ویژگی‌هایی که همبستگی (Correlation) بالایی با هم دارند.
    """
    print(f"      [Pruning] Reducing redundancy (Correlation > {corr_threshold})...")
    selected = []
    
    # محاسبه ماتریس همبستگی فقط برای ژن‌های فیلتر شده (برای جلوگیری از پر شدن رم)
    corr_matrix = df[features].corr().abs()
    
    for col in features:
        if len(selected) >= max_features:
            break
        
        is_correlated = False
        for sel_col in selected:
            if corr_matrix.loc[col, sel_col] > corr_threshold:
                is_correlated = True
                break
                
        if not is_correlated:
            selected.append(col)
            
    print(f"      [Pruning] Kept {len(selected)} independent features out of {len(features)}.")
    return selected

def create_model_ready_dataset(rna_path, cnv_path, output_path, rna_max_features=300, cnv_max_features=200, variance_pool=2000):
    print("[INFO] Loading RAW datasets...")
    # خواندن داده‌های خام
    rna_df = pd.read_csv(rna_path)
    cnv_df = pd.read_csv(cnv_path)
    
    print(f"[INFO] Initial shapes -> RNA: {rna_df.shape}, CNV: {cnv_df.shape}")
    
    # ==========================================
    # 0. REMOVE DUPLICATES (CRITICAL STEP)
    # ==========================================
    print("\n[INFO] --- Removing Duplicates (Data Leakage Prevention) ---")
    initial_rna_patients = len(rna_df)
    initial_cnv_patients = len(cnv_df)
    
    rna_df = rna_df.drop_duplicates(subset=['Patient_ID'], keep='first').reset_index(drop=True)
    cnv_df = cnv_df.drop_duplicates(subset=['Patient_ID'], keep='first').reset_index(drop=True)
    
    print(f"      [Drop] RNA: Removed {initial_rna_patients - len(rna_df)} duplicate patients.")
    print(f"      [Drop] CNV: Removed {initial_cnv_patients - len(cnv_df)} duplicate patients.")

    # ==========================================
    # 1. ALIGN PATIENTS (اشتراک بیماران)
    # ==========================================
    common_patients = list(set(rna_df['Patient_ID']) & set(cnv_df['Patient_ID']))
    print(f"\n[INFO] Found {len(common_patients)} common patients. Aligning datasets...")
    
    # فیلتر کردن و مرتب‌سازی دقیق بیماران برای جلوگیری از اشتباه در ادغام
    rna_df = rna_df[rna_df['Patient_ID'].isin(common_patients)].sort_values('Patient_ID').reset_index(drop=True)
    cnv_df = cnv_df[cnv_df['Patient_ID'].isin(common_patients)].sort_values('Patient_ID').reset_index(drop=True)
    
    scaler = StandardScaler()
    
    # ==========================================
    # 2. PROCESS RNA
    # ==========================================
    print("\n[INFO] --- Processing RNA Data ---")
    rna_features = [c for c in rna_df.columns if c != 'Patient_ID']
    
    print("      [Filter] Removing sparse genes (<20% expression)...")
    non_zero_ratio = (rna_df[rna_features] > 0).mean()
    valid_rna = non_zero_ratio[non_zero_ratio >= 0.2].index.tolist()
    
    print("      [Transform] Applying Log2(x+1)...")
    rna_data = np.log2(rna_df[valid_rna] + 1)
    
    print(f"      [Filter] Selecting top {variance_pool} genes by variance...")
    top_var_rna = rna_data.var().nlargest(variance_pool).index.tolist()
    
    final_rna_cols = get_uncorrelated_features(rna_data, top_var_rna, max_features=rna_max_features)
    
    print("      [Scale] Applying Z-Score Standardization...")
    final_rna_data = pd.DataFrame(scaler.fit_transform(rna_data[final_rna_cols]), columns=final_rna_cols)
    final_rna_data.insert(0, 'Patient_ID', rna_df['Patient_ID'])
    
    # ==========================================
    # 3. PROCESS CNV
    # ==========================================
    print("\n[INFO] --- Processing CNV Data ---")
    cnv_features = [c for c in cnv_df.columns if c != 'Patient_ID']
    
    print("      [Impute] Filling missing CNV with normal diploid (2.0)...")
    cnv_df[cnv_features] = cnv_df[cnv_features].fillna(2.0)
    
    print("      [Transform] Applying Log2(x+1)...")
    cnv_data = np.log2(cnv_df[cnv_features] + 1)
    
    print(f"      [Filter] Selecting top {variance_pool} genes by variance...")
    top_var_cnv = cnv_data.var().nlargest(variance_pool).index.tolist()
    
  
    final_cnv_cols = get_uncorrelated_features(cnv_data, top_var_cnv, max_features=cnv_max_features)
    
    print("      [Scale] Applying Z-Score Standardization...")
    final_cnv_data = pd.DataFrame(scaler.fit_transform(cnv_data[final_cnv_cols]), columns=final_cnv_cols)
    final_cnv_data.insert(0, 'Patient_ID', cnv_df['Patient_ID'])
    
    # ==========================================
    # 4. MERGE & SAVE
    # ==========================================
    print("\n[INFO] --- Finalizing AI-Ready Dataset ---")
  
    final_df = pd.merge(final_rna_data, final_cnv_data, on='Patient_ID')
    
    final_df = final_df.round(4)
    
    print(f"[INFO] Saving dataset to {output_path}...")
    final_df.to_csv(output_path, index=False)
    
    print("=" * 80)
    print(f"[SUCCESS] Balanced & Leak-Free Dataset Created Successfully!")
    print(f"Total Patients: {final_df.shape[0]}")
    print(f"Total Features: {final_df.shape[1] - 1} ({len(final_rna_cols)} RNA + {len(final_cnv_cols)} CNV)")
    print(f"Saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    RNA_RAW_PATH = r"D:\TCGA-BRCA\RNA_RAW.csv"
    CNV_RAW_PATH = r"D:\TCGA-BRCA\CNV_RAW.csv"
    OUTPUT_CSV_PATH = r"D:\TCGA-BRCA\Kaggle_TCGA_BRCA_ModelReady_V3.csv"
    
    create_model_ready_dataset(
        rna_path=RNA_RAW_PATH, 
        cnv_path=CNV_RAW_PATH, 
        output_path=OUTPUT_CSV_PATH, 
        rna_max_features=300,       # <-- سقف ویژگی‌های RNA
        cnv_max_features=200,       # <-- سقف ویژگی‌های CNV
        variance_pool=2000
    )