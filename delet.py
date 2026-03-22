import os
import glob
import pandas as pd

def remove_recovered_files(base_dataset_dir, log_csv_name="1Deleted_Files_Log.csv"):
    print(f"[*] Scanning for recovered JSON files in: {base_dataset_dir}")
    
    # استفاده از الگو برای پیدا کردن تمام فایل های ریکاور شده در تمام زیرپوشه ها
    # اگر فقط دقیقا همون یک اسم خاص رو میخواستی، به جای ستاره بنویس TCGA-AO-A0JI
    search_pattern = os.path.join(base_dataset_dir, "**", "*2026-03-06.json")
    files_to_delete = glob.glob(search_pattern, recursive=True)
    
    if not files_to_delete:
        print("[-] No recovered JSON files found to delete.")
        return

    print(f"[!] Found {len(files_to_delete)} files. Starting deletion process...\n")
    
    deleted_records = []
    
    for file_path in files_to_delete:
        file_name = os.path.basename(file_path)
        folder_path = os.path.dirname(file_path)
        patient_id = os.path.basename(folder_path)
        
        try:
            os.remove(file_path) # دستور حذف فایل
            status = "Success"
            print(f"  -> Deleted: {file_name}")
            
            # ذخیره اطلاعات برای فایل گزارش
            deleted_records.append({
                "Patient_ID": patient_id,
                "Deleted_File_Name": file_name,
                "Folder_Path": folder_path,
                "Status": status
            })
            
        except Exception as e:
            print(f"  -> Error deleting {file_name}: {str(e)}")
            deleted_records.append({
                "Patient_ID": patient_id,
                "Deleted_File_Name": file_name,
                "Folder_Path": folder_path,
                "Status": f"Failed: {str(e)}"
            })

    # ساخت فایل CSV از لاگ ها
    if deleted_records:
        df_log = pd.DataFrame(deleted_records)
        df_log.to_csv(log_csv_name, index=False, encoding='utf-8')
        
        print("\n" + "="*50)
        print(f"✅ Cleanup Completed!")
        print(f"🗑️ Successfully deleted {len(deleted_records)} files.")
        print(f"📝 Deletion log saved to: {os.path.abspath(log_csv_name)}")
        print("="*50)

if __name__ == "__main__":
    # آدرس پوشه اصلی که تمام بیماران (TCGA-...) در آن هستند را اینجا بگذار
    MASTER_DATASET_FOLDER = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA"
    
    # اسم فایل اکسلی که لاگ حذفیات رو توش مینویسه
    LOG_FILE_NAME = "Deleted_Recovered_Files.csv"
    
    remove_recovered_files(MASTER_DATASET_FOLDER, LOG_FILE_NAME)