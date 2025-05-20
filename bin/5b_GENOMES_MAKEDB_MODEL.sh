#!/bin/bash

echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Manual genome selection for DB generation.."
# Base directory
BASE_DIR=$(dirname "$(realpath "$0")")
cd "$BASE_DIR"/../data/genomes_manual

# Manual list of genome files
genomes=(
    "AP85-441.genome.fa"
    "LA-Purple.genome.fa"
    "Np-X.genome.fa"
    "R570.v2023.genome.fasta"
    "XTT22.genome.fa"
    "YN2009-3.genome.fa"
    "YN83-224.genome.fa"
    "ZZ1.v20231221.genome.fasta"
)

# Output file
output="$BASE_DIR"/../data/genomes/Saccharum_combined.fa
> "$output"  # Clear the previous file

# Process each genome (This step will add the prefix name before the sequence, granting no duplicates)
for file in "${genomes[@]}"; do
    prefix=$(basename "$file" | cut -d. -f1)
    awk -v prefix="$prefix" '
        /^>/ { sub(/^>/, ">" prefix "_"); print }
        !/^>/ { print }
    ' "$file" >> "$output"
done

# Create the BLAST DB
makeblastdb -in "$output" -dbtype nucl -out "$BASE_DIR"/../data/blast_db/Saccharum

echo "[$(date '+%Y-%m-%d %H:%M:%S')][FINISHED] BLAST DB for Saccharum created successfully!"
