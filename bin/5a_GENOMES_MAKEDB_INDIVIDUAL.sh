#!/bin/bash
# Directories
BASE_DIR="$(dirname "$(realpath "$0")")"
INPUT_DIR="$BASE_DIR/../data/genomes"
OUTPUT_DIR="$BASE_DIR/../data/blast_db"
mkdir -p "$OUTPUT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Parsing fasta files and generating DBs.."

# Generate BLAST DBs
for fasta in "$INPUT_DIR"/*.{fna,fa,fasta}; do
    # File verification
    if [[ -e "$fasta" ]]; then
        # Extract file name without extension
        base_name=$(basename "$fasta")
        
        # Extract genus name (first part before underscore)
        genus_name=$(echo "$base_name" | cut -d'_' -f1)
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')][INFO] Processing file: $base_name -> DB name: $genus_name"
        
        # Check if DB already exists
        if [[ -f "$OUTPUT_DIR/$genus_name.nhr" && -f "$OUTPUT_DIR/$genus_name.nin" && -f "$OUTPUT_DIR/$genus_name.nsq" || \
              -f "$OUTPUT_DIR/$genus_name.00.nhr" && -f "$OUTPUT_DIR/$genus_name.00.nin" && -f "$OUTPUT_DIR/$genus_name.00.nsq" ]]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')][SKIP] BLAST DB for $genus_name already exists, skipping..."
            continue
        fi
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')][START] Creating BLAST DB for: $genus_name.."
        makeblastdb -in "$fasta" -dbtype nucl -out "$OUTPUT_DIR/$genus_name" -parse_seqids
        
        # Check if BLAST DB files were created
        if [[ -f "$OUTPUT_DIR/$genus_name.nhr" && -f "$OUTPUT_DIR/$genus_name.nin" && -f "$OUTPUT_DIR/$genus_name.nsq" || \
              -f "$OUTPUT_DIR/$genus_name.00.nhr" && -f "$OUTPUT_DIR/$genus_name.00.nin" && -f "$OUTPUT_DIR/$genus_name.00.nsq" ]]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')][DONE] DB $genus_name created successfully!"
            # Commented out to avoid automatic deletion - uncomment if needed
            # echo "[$(date '+%Y-%m-%d %H:%M:%S')][INFO] Removing original file: $base_name"
            # rm -f "$fasta"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')][ERROR] BLAST DB for $genus_name was not created properly, continuing.."
        fi
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')][FINISHED] All available DBs were processed!"
