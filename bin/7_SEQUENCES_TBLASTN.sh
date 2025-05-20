#!/bin/bash

# Directories
BASE_DIR=$(dirname "$(realpath "$0")")
PROTEIN_DIR="$BASE_DIR/../outputs/filtered_fasta"
DATABASE_DIR="$BASE_DIR/../data/blast_db"
OUTPUT_DIR="$BASE_DIR/../outputs/blast_results"
mkdir -p "$OUTPUT_DIR"

# Count total protein FASTA files
total_files=$(find "$PROTEIN_DIR" -name "*.fasta" | wc -l)
count=0

# Run tblastn for each protein FASTA file
for protein_file in "$PROTEIN_DIR"/*.fasta; do
    # Skip if no files found
    [ -e "$protein_file" ] || continue

    # Increment counter
    count=$((count + 1))

    # Print progress every 10 proteins or for the first one
    if (( count % 10 == 0 || count == 1 )); then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking $count/$total_files proteins"
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Running tblastn for $protein_file.."

    # Get base name without extension
    genus=$(basename "${protein_file%.fasta}")

    # Check if database exists
    if ! ls "$DATABASE_DIR/$genus"*.nsq >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')][WARNING] Database for $genus not found, skipping..."
        continue
    fi

    # Run tblastn with dynamic database name
    tblastn -query "$protein_file" \
            -db "$DATABASE_DIR/$genus" \
            -out "$OUTPUT_DIR/${genus}_tblastn.txt" \
            -evalue 1e-5 \
            -outfmt 6 \
            -max_target_seqs 1 \
            -num_threads $(nproc --ignore=2)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][SUCCESS] tblastn for $protein_file, continuing.."

    # Filter best hits (lowest e-value per query)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Filtering best hits for $protein_file..."
    sort -k1,1 -k12,12gr "$OUTPUT_DIR/${genus}_tblastn.txt" \
        | awk '!seen[$1]++' \
        > "$OUTPUT_DIR/${genus}_BH.txt"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')][SUCCESS] Filtered best hits for $protein_file, continuing.."
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')][FINISHED] tblastn process completed with best hits extracted!"
