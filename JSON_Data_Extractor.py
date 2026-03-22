import os
import json
import glob
import pandas as pd


def flatten_and_filter(data, prefix=''):
    result = {}
    if isinstance(data, dict):
        for key, value in data.items():
            if key.endswith('_id') or key == 'id': continue
            if key.endswith('_datetime') or key.endswith('_date'): continue
            if key == 'state' or key == 'project': continue

            new_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                result.update(flatten_and_filter(value, new_key + '_'))
            elif isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    agg_dict = {}
                    for item in value:
                        flat_item = flatten_and_filter(item, '') 
                        for k, v in flat_item.items():
                            if k not in agg_dict: agg_dict[k] = []
                            if str(v) not in agg_dict[k] and str(v) not in ['None', '', 'not reported', 'unknown']:
                                agg_dict[k].append(str(v))
                                
                    for k, v_list in agg_dict.items():
                        result[f"{new_key}_{k}"] = " | ".join(v_list)
                else:
                    result[new_key] = " | ".join([str(x) for x in value if x is not None and str(x) not in ['None', '']])
            else:
                if str(value) not in ['None', '', 'not reported', 'unknown']:
                    result[new_key] = value
    return result

def process_patient_json(patient_dir):
    json_files = [f for f in glob.glob(os.path.join(patient_dir, "*.json")) if "clinical" in os.path.basename(f).lower()]
    
    if not json_files: 
        return None
        
    try:
        with open(json_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list): data = data[0]
            
        main_patient_id = data.get('submitter_id', 'Unknown')
        clean_data = flatten_and_filter(data)
        
        final_data = {'Patient_ID': main_patient_id}
        final_data.update(clean_data)
        return final_data
    except Exception as e:
        return None

def build_master_clinical_dataset(base_dataset_dir, output_file_name="Master_Clinical_Dataset.csv"):
    print(f"[*] Scanning Master Directory: {base_dataset_dir} ...\n")
    
    all_patients_data = []
    
    patient_dirs = [os.path.join(base_dataset_dir, d) for d in os.listdir(base_dataset_dir) 
                    if os.path.isdir(os.path.join(base_dataset_dir, d)) and d.startswith("TCGA-")]
                    
    total_patients = len(patient_dirs)
    print(f"[+] Found {total_patients} patient folders. Starting Mass Extraction...")
    
    for i, p_dir in enumerate(patient_dirs, 1):
        print(f"\r  -> Processing Patient {i}/{total_patients} : {os.path.basename(p_dir)}", end="", flush=True)
        
        patient_data = process_patient_json(p_dir)
        if patient_data:
            all_patients_data.append(patient_data)
            
    print("\n\n[*] All JSON files processed! Compiling the Master DataFrame...")
    
    df = pd.DataFrame(all_patients_data)
    
    df.to_csv(output_file_name, index=False)
    
    print("="*50)
    print(f"✅ SUCCESS! Master dataset created.")
    print(f"📂 Saved to: {os.path.abspath(output_file_name)}")
    print(f"📊 Dataset Shape: {df.shape[0]} Patients × {df.shape[1]} Clinical Features")
    print("="*50)

if __name__ == "__main__":
    MASTER_DATASET_FOLDER = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA" 
    
    build_master_clinical_dataset(MASTER_DATASET_FOLDER)