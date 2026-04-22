import os
import shutil


source_dir = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA"

destination_dir = r"D:\TCGA-BRCA\manifest-25vRPwyh8987165612391086998\TCGA-BRCA-processed"

#
keywords = ["mri_processed", "SVS_patches"]

def move_patient_folders():
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        print(f"The destination folder was created: {destination_dir}")

    for patient_name in os.listdir(source_dir):
        patient_path = os.path.join(source_dir, patient_name)

        # is it folder or not?
        if os.path.isdir(patient_path):
            
            # پیدا کردن فولدرهای مورد نظر داخل فولدر این بیمار
            folders_to_move = []
            for item in os.listdir(patient_path):
                item_path = os.path.join(patient_path, item)
                
                # اگر آیتم یک فولدر بود و اسمش شامل یکی از کلمات کلیدی بود
                if os.path.isdir(item_path) and any(keyword in item for keyword in keywords):
                    folders_to_move.append(item)

            # اگر فولدری برای انتقال پیدا شد
            if folders_to_move:
                # ایجاد فولدر به اسم همین بیمار در مسیر جدید
                new_patient_path = os.path.join(destination_dir, patient_name)
                if not os.path.exists(new_patient_path):
                    os.makedirs(new_patient_path)

                # کات کردن (منتقل کردن) فولدرها به مسیر جدید
                for folder in folders_to_move:
                    src_folder_path = os.path.join(patient_path, folder)
                    dest_folder_path = os.path.join(new_patient_path, folder)
                    
                    try:
                        shutil.move(src_folder_path, dest_folder_path)
                        print(f"Migration successful: '{folder}' from patient '{patient_name}'")
                    except Exception as e:
                        print(f"Error occurred while moving '{folder}' from patient '{patient_name}': {e}")

if __name__ == "__main__":
    move_patient_folders()
    print("Operation completed.")