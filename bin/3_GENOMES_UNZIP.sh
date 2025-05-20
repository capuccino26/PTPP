#!/bin/bash

echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Unziping files downloaded from NCBI datasets.."
# Directories
BASE_DIR=$(dirname "$(realpath "$0")")
GENOMES_DIR="$BASE_DIR/../data/genomes"

# Find all zip files in subdirectories and unzip them in place
find "$GENOMES_DIR" -type f -name "*.zip" | while read -r zip_file; do
    echo "Unzipping: $zip_file"
    unzip -o "$zip_file" -d "$(dirname "$zip_file")"
    
    # Remove the zip file after extracting
    echo "Removing zip file: $zip_file"
    rm -f "$zip_file"
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')][FINISHED] Unzipping completed and zip files removed!"
