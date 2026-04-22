import json
from pathlib import Path
import os

def create_dataset_metadata(source_path, output_file):
    """
    ایجاد فایل متادیتا برای دیتاست
    """
    metadata = {
        "title": "TCGA-AO-A0J9 Medical Imaging Dataset",
        "description": "Processed MRI and SVS patches from TCGA patients",
        "license": "Public",
        "patients_count": 0,
        "folders": []
    }
    
    patients = [f for f in os.listdir(source_path) 
                if os.path.isdir(os.path.join(source_path, f))]
    
    metadata["patients_count"] = len(patients)
    
    for patient in patients:
        patient_path = os.path.join(source_path, patient)
        folders = [f for f in os.listdir(patient_path) 
                   if os.path.isdir(os.path.join(patient_path, f))]
        metadata["folders"].append({
            "patient_id": patient,
            "subfolders": folders
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ متادیتا ایجاد شد: {output_file}")

# استفاده
create_dataset_metadata(
    r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA-processed",
    r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\dataset_info.json"
)