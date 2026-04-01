# TCGA-BRCA: Multi-Modal Fusion Dataset & Preprocessing Pipeline

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/) [![Kaggle](https://img.shields.io/badge/Kaggle-Dataset-20BEFF)](https://www.kaggle.com/datasets/sepehreslamimoghadam/breast-cancer-vision-and-genomic-fusion-ml-ready)

This repository contains the source code and documentation for creating a curated, machine-learning-ready version of the **TCGA-BRCA** dataset. The goal of this project is to integrate three distinct modalities—**Radiology (MRI)**, **Pathology (SVS Patches)**, and **Multi-Omics (RNA/CNV)**—into a single, patient-aligned framework for multi-modal fusion research.

## 📌 Project Overview
Working with raw data from the GDC Data Portal and TCIA is notoriously difficult due to mismatched IDs, massive file sizes, and inconsistent clinical records. This project solves these issues by:
- **Aligning 122 patients** across all modalities.
- **Preprocessing WSIs** into high-resolution, ML-ready patches.
- **Engineering Clinical Data** (One-hot encoding complex drug regimens).
- **Normalizing Omics Data** (Merging RNA-seq and CNV into fusion-ready formats).

## 🗂️ Dataset Structure
If you are using the processed dataset from Kaggle, the structure is organized as follows:

```text
├── DOWNLOADER.py              # Main script to fetch raw data from GDC/TCIA portals
├── multiomics_downloader.py   # Specialized downloader for RNA-Seq and CNV data
├── JSON_Data_Extractor.py     # Parses manifests and clinical metadata for patient alignment
├── MRI_cleaning.py            # Preprocessing, normalization, and resizing of MRI scans
├── SVS_cleaning.py            # WSI processing: Tiling, background removal, and patching
├── Mutations_Data.py          # Aggregates and filters somatic mutation records
├── TSV_cleaning.py            # Cleaning and formatting raw clinical/omics TSV files
├── TSV_prep.py                # Final preparation of TSVs for machine learning models
├── Text_Data_Preprocessor.py  # Processing clinical notes and unstructured text data
├── Chacking.py                # Data integrity scripts to ensure modal alignment
└── delet.py                   # Utility script for temporary file and workspace cleanup
