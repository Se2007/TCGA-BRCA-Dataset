import requests
import json
from playwright.sync_api import sync_playwright
import os

def open_gdc_case_page(submitter_id):
    api_endpoint = "https://api.gdc.cancer.gov/cases"
    filters = {"op": "in", "content": {"field": "submitter_id", "value": [submitter_id]}}
    params = {"filters": json.dumps(filters), "fields": "case_id,submitter_id", "format": "JSON"}
    
    try:
        response = requests.get(api_endpoint, params=params)
        response.raise_for_status() 
        data = response.json()
        hits = data.get("data", {}).get("hits", [])
        
        if hits:
            case_id = hits[0].get("case_id")
            return f"https://portal.gdc.cancer.gov/cases/{case_id}"
        else:
            print(f"[-] not found'{submitter_id}'")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[-] error {e}")
        return None


def download_clinical_via_scraping(url, save_dir="."):
    print(f"[*] Opening browser to scrape: {url}")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        page.goto(url, wait_until="networkidle")
        
        print("[*] Handling disclaimers and popups...")
        try:
            page.locator('button:has-text("Accept")').click(timeout=3000)
            print("[+] Disclaimer accepted.")
        except:
            pass
        
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500) 
        except:
            pass
        # ---------------------------------------------------
        
        try:
            page.get_by_role("heading", name="Clinical").scroll_into_view_if_needed()
            
            download_btn = page.locator('button:has-text("Download")').first
            
            download_btn.click(force=True)
            
            with page.expect_download(timeout=10000) as download_info:
                page.locator('text=JSON').first.click(force=True)
            
            download = download_info.value
            
            file_path = os.path.join(save_dir, download.suggested_filename)
            download.save_as(file_path)
            
            print(f"[+] Download complete via Scraping! Saved as: {file_path}")
            
        except Exception as e:
            print(f"[-] Scraping failed. Error: {e}")
            
        finally:
            browser.close()

def download_maf_file_via_api(submitter_id, save_dir="."):
    print(f"[*] Searching for Open Masked MAF file for {submitter_id} via API...")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    files_endpoint = "https://api.gdc.cancer.gov/files"
    
    filters = {
        "op": "and",
        "content": [
            {"op": "in", "content": {"field": "cases.submitter_id", "value": [submitter_id]}},
            {"op": "=", "content": {"field": "data_format", "value": "MAF"}},
            {"op": "=", "content": {"field": "access", "value": "open"}}
        ]
    }
    
    params = {
        "filters": json.dumps(filters),
        "fields": "file_id,file_name",
        "format": "JSON",
        "size": "100"
    }
    
    try:
        response = requests.get(files_endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        files = data.get("data", {}).get("hits", [])
        
        target_file = None
        for f in files:
            if "masked" in f.get("file_name", "").lower():
                target_file = f
                break
                
        if target_file:
            file_id = target_file["file_id"]
            file_name = target_file["file_name"]
            print(f"[+] Found Target File: {file_name}")
            print(f"[*] Starting download (this might take a few seconds)...")
            
            download_endpoint = f"https://api.gdc.cancer.gov/data/{file_id}"
            file_path = os.path.join(save_dir, file_name)
            
            with requests.get(download_endpoint, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
                        
            print(f"[+] MAF file downloaded successfully: {file_path}")
        else:
            print("[-] No 'Open Masked MAF' file found for this patient in the database.")
            
    except Exception as e:
        print(f"[-] MAF API error: {e}")


            
def download_specific_tsv_files_via_api(submitter_id, save_dir="."):
    print(f"[*] Searching for EXACTLY 2 target TSV files for {submitter_id} via API...")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    files_endpoint = "https://api.gdc.cancer.gov/files"
    
    filters = {
        "op": "and",
        "content": [
            {"op": "in", "content": {"field": "cases.submitter_id", "value": [submitter_id]}},
            {"op": "=", "content": {"field": "data_format", "value": "TSV"}},
            {"op": "=", "content": {"field": "access", "value": "open"}}
        ]
    }
    
    params = {
        "filters": json.dumps(filters),
        "fields": "file_id,file_name",
        "format": "JSON",
        "size": "100"
    }
    
    try:
        response = requests.get(files_endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        files = data.get("data", {}).get("hits", [])
        
        files_to_download = []
        
        for f in files:
            file_name = f.get("file_name", "").lower()
            
            if "rna_seq.augmented_star_gene_counts.tsv" in file_name:
                files_to_download.append(f)
                
            elif "gene_level_copy_number.v36.tsv" in file_name:
                if "ascat" not in file_name and "absolute" not in file_name:
                    files_to_download.append(f)
                    
        if files_to_download:
            print(f"[+] Found {len(files_to_download)} exact matching TSV file(s).")
            
            for target_file in files_to_download:
                file_id = target_file["file_id"]
                file_name = target_file["file_name"]
                
                print(f"[*] Downloading TSV: {file_name} ...")
                download_endpoint = f"https://api.gdc.cancer.gov/data/{file_id}"
                file_path = os.path.join(save_dir, file_name)
                
                with requests.get(download_endpoint, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f_out:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f_out.write(chunk)
                            
                print(f"[+] Saved: {file_path}")
        else:
            print("[-] No target TSV files found for this patient.")
            
    except Exception as e:
        print(f"[-] TSV API error: {e}")


def download_clinical_bcr_biotab_via_api(submitter_id, save_dir="."):
    print(f"[*] Searching for Clinical BCR Biotab files (Drug & Patient) for {submitter_id} via API...")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    files_endpoint = "https://api.gdc.cancer.gov/files"
    
    filters = {
        "op": "and",
        "content": [
            {"op": "in", "content": {"field": "cases.submitter_id", "value": [submitter_id]}},
            {"op": "=", "content": {"field": "data_format", "value": "BCR Biotab"}}, 
            {"op": "=", "content": {"field": "access", "value": "open"}}
        ]
    }
    
    params = {
        "filters": json.dumps(filters),
        "fields": "file_id,file_name",
        "format": "JSON",
        "size": "100"
    }
    
    try:
        response = requests.get(files_endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        files = data.get("data", {}).get("hits", [])
        
        files_to_download = []
        
        for f in files:
            file_name = f.get("file_name", "").lower()
            
            if "clinical_drug" in file_name:
                files_to_download.append(f)
                
            elif "clinical_patient" in file_name:
                files_to_download.append(f)
                    
        if files_to_download:
            print(f"[+] Found {len(files_to_download)} exact matching BCR Biotab file(s).")
            
            for target_file in files_to_download:
                file_id = target_file["file_id"]
                file_name = target_file["file_name"]
                
                print(f"[*] Downloading: {file_name} ...")
                download_endpoint = f"https://api.gdc.cancer.gov/data/{file_id}"
                file_path = os.path.join(save_dir, file_name)
                
                with requests.get(download_endpoint, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f_out:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f_out.write(chunk)
                            
                print(f"[+] Saved: {file_path}")
        else:
            print("[-] No target Clinical BCR Biotab files (Drug/Patient) found for this patient.")
            
    except Exception as e:
        print(f"[-] API error: {e}")


def download_diagnostic_slide_via_api(submitter_id, save_dir="."):
    print(f"[*] Searching for Diagnostic Slide (SVS) for {submitter_id} via API...")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    files_endpoint = "https://api.gdc.cancer.gov/files"
    
    filters = {
        "op": "and",
        "content": [
            {"op": "in", "content": {"field": "cases.submitter_id", "value": [submitter_id]}},
            {"op": "=", "content": {"field": "data_format", "value": "SVS"}},
            {"op": "=", "content": {"field": "experimental_strategy", "value": "Diagnostic Slide"}},
            {"op": "=", "content": {"field": "access", "value": "open"}}
        ]
    }
    
    params = {
        "filters": json.dumps(filters),
        "fields": "file_id,file_name,file_size",
        "format": "JSON",
        "size": "100"
    }
    
    try:
        response = requests.get(files_endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        files = data.get("data", {}).get("hits", [])
        
        if files:
            print(f"[+] Found {len(files)} Diagnostic Slide(s).")
            
            for target_file in files:
                file_id = target_file["file_id"]
                file_name = target_file["file_name"]
                
                file_size_bytes = target_file.get("file_size", 0)
                file_size_mb = file_size_bytes / (1024 * 1024)
                
                print(f"[*] Downloading SVS: {file_name} ({file_size_mb:.2f} MB) ...")
                print("    (This is a large file, please wait...)")
                
                download_endpoint = f"https://api.gdc.cancer.gov/data/{file_id}"
                file_path = os.path.join(save_dir, file_name)
                
                with requests.get(download_endpoint, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f_out:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f_out.write(chunk)
                            
            print(f"[+] Saved: {file_path}")
        else:
            print("[-] No Diagnostic Slide (SVS) found for this patient.")
            
    except Exception as e:
        print(f"[-] SVS API error: {e}")


if __name__ == "__main__":
    target_id = 'TCGA-AO-A0JB'#'TCGA-AR-A1AN'
    
    url = open_gdc_case_page(target_id)
    print(f"URL Found: {url}")
    
    # if url:
        # download_clinical_via_scraping(url)

    # download_maf_file_via_api(target_id)
    # download_specific_tsv_files_via_api(target_id)

    # download_clinical_bcr_biotab_via_api(target_id)

    download_diagnostic_slide_via_api(target_id)