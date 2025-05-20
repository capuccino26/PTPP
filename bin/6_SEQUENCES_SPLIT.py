#!/usr/bin/env python3

from pathlib import Path
import pandas as pd
from Bio import SeqIO
import re
from datetime import datetime

# Directories
BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR.parent / "outputs"
INPUT_DIR = BASE_DIR.parent / "inputs"
LOG_DIR = BASE_DIR.parent / "logs"
DATA_DIR = BASE_DIR.parent / "data" / "genomes"
for d in [OUTPUT_DIR, LOG_DIR, OUTPUT_DIR / "filtered_fasta"]:
    d.mkdir(parents=True, exist_ok=True)

# File names
protein_fasta = INPUT_DIR / "PROT_DJ-DIR-JRL_unique.fasta"
xlsx_file = INPUT_DIR / "PROT_IDS.xlsx"
log_file = LOG_DIR / "extract_species.log"

# Extract genus name from table
df = pd.read_excel(xlsx_file)
df['Genus'] = df['Tax_Name'].str.extract(r'^(\w+)', expand=False)

# Group IDs by genus
genus_groups = df.groupby('Genus')['ID'].apply(lambda x: set(x.astype(str)))

# Load ALL sequences
all_records = list(SeqIO.parse(protein_fasta, "fasta"))

# Start processing
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] FILTERING genus-specific FASTA files..")
with open(log_file, "w") as log:
    log.write("[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Starting sequence extraction by genus\n")
    
    for genus, ids in genus_groups.items():
        if pd.isna(genus):
            continue
            
        filtered_records = []
        for record in all_records:
            # Verify for multiple match
            record_id = record.id.split('|')[0] if '|' in record.id else record.id
            
            # 1. Exact match
            if any(id == record_id for id in ids):
                filtered_records.append(record)
                continue
                
            # 2. Verify if ID table matches FASTA ID
            if any(id in record_id for id in ids):
                filtered_records.append(record)
                continue
                
            # 3. Verify partial IDs (table ID and FASTA file IDs might diverge)
            for id in ids:
                id_part = re.split(r'[._]', id)[0]
                if id_part and id_part in record_id:
                    filtered_records.append(record)
                    break
        
        # Generate FASTA file by genus
        output_fasta = OUTPUT_DIR / "filtered_fasta" / f"{genus}.fasta"
        SeqIO.write(filtered_records, output_fasta, "fasta")
        log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] {genus} sequences extracted: {len(filtered_records)}\n")
        log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Output FASTA: {output_fasta}\n")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] {len(filtered_records)} {genus} sequences saved to: {output_fasta}!")

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][FINISHED] All genus-specific FASTA files created successfully!")
