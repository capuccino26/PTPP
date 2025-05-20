#!/bin/bash

echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Start moving genome files to genomes folder.."
# Directories
BASE_DIR=$(dirname "$(realpath "$0")")
SOURCE_DIR="$BASE_DIR/../data/genomes"
DEST_DIR="$BASE_DIR/../data/genomes"
mkdir -p "$DEST_DIR"

# Find genomic files and process them
find "$SOURCE_DIR" -type f -name "*_genomic.fna" | while read -r file; do
    # Get the species name from the parent directory
    species=$(basename "$(dirname "$file")")

    # Extract the genome code
    genome_code=$(basename "$file" | sed 's/_genomic\.fna//')

    # Build the new filename with species and genome code
    new_filename="${species}_${genome_code}_genomic.fna"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Moving: $file -> $DEST_DIR/$new_filename.."
    mv "$file" "$DEST_DIR/$new_filename"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][DONE] Moving: $file -> $DEST_DIR/$new_filename!"
done

# Remove empty directories after moving files
find "$SOURCE_DIR" -type d -empty -exec rmdir {} \;

echo "[$(date '+%Y-%m-%d %H:%M:%S')][FINISHED] All files have been moved and renamed successfully. Empty directories removed!"
