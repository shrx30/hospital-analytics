"""
Hospital Operations Analytics - Database Pipeline Module
This script downloads the Kaggle dataset using kagglehub,
copies the CSV files into the local /data directory, and ingest them into SQLite.
"""

import os
import shutil
import sqlite3
import pandas as pd
import kagglehub

# Define project directories and file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "hospital_operations.db")
DATASET_SLUG = "shalakagangurde/hospital-hmis-dataset-for-healthcare-analytics"

def find_csv_files(search_dir):
    """
    Recursively scans the downloaded cache folder to find all CSV files.
    Returns:
        List of paths to CSV files found.
    """
    csv_files = []
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    return csv_files

def download_and_setup_data():
    """
    Downloads the dataset from Kaggle, Copies CSV files into local 'data/' folder.
    """
    # Ensure local data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created local data directory at: {DATA_DIR}")

    print(f"Downloading dataset '{DATASET_SLUG}' using kagglehub...")
    # This downloads the dataset to the user's kagglehub cache folder
    downloaded_path = kagglehub.dataset_download(DATASET_SLUG)
    print(f"Dataset downloaded successfully to cache: {downloaded_path}")

    # Find and copy all CSV files to the local data/ folder
    csv_files = find_csv_files(downloaded_path)
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the downloaded Kaggle dataset!")

    print(f"Found {len(csv_files)} CSV files. Copying to local data/ folder...")
    copied_count = 0
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        dest_path = os.path.join(DATA_DIR, filename)
        
        # Copy the file
        shutil.copy2(csv_path, dest_path)
        copied_count += 1
        print(f" - Copied {filename} to {dest_path}")
    
    print(f"Data copy operation finished. Total files copied: {copied_count}")

def load_data_to_sqlite():
    """
    Reads all CSV files from local 'data/' directory and stores them as tables in SQLite DB.
    """
    if not os.path.exists(DATA_DIR):
         raise FileNotFoundError("Local data/ directory does not exist! Please run download_and_setup_data() first.")

    print(f"Connecting to SQLite database at: {DB_PATH}")
    # Establish connection; this will create the DB file if it doesn't exist
    conn = sqlite3.connect(DB_PATH)
    
    # Get all CSV files in local data directory
    local_csvs = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    
    if not local_csvs:
        print("No CSV files found in local data directory to ingest.")
        conn.close()
        return

    print(f"Found {len(local_csvs)} CSV files for ingestion. Processing...")
    
    for csv_filename in local_csvs:
        table_name = os.path.splitext(csv_filename)[0]
        csv_file_path = os.path.join(DATA_DIR, csv_filename)
        
        print(f" - Log: Reading {csv_filename} into Pandas DataFrame...")
        # Load CSV using Pandas
        df = pd.read_csv(csv_file_path)
        
        print(f" - Log: Saving to SQLite table '{table_name}' ({len(df)} rows)...")
        # Load DataFrame into SQLite
        df.to_sql(name=table_name, con=conn, if_exists="replace", index=False)
        print(f" - Success: Table '{table_name}' loaded successfully.")

    # Commit changes and close
    conn.commit()
    conn.close()
    print("All CSV tables successfully loaded into SQLite database.")

def main():
    print("Starting Hospital HMIS Dataset Ingestion Pipeline...")
    try:
        download_and_setup_data()
        load_data_to_sqlite()
        print("Database pipeline ran successfully!")
    except Exception as e:
        print(f"Error occurred during ingestion pipeline: {e}")

if __name__ == "__main__":
    main()
