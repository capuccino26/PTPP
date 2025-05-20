import subprocess
from pathlib import Path
import sys
import glob
import re
import os
from datetime import datetime

# Exonerate params
min_percent = 20
min_intron = 20
max_intron = 50000
bestn = 1
verbose = 3

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent
FILTERED_FASTA_DIR = BASE_DIR/"outputs/filtered_fasta"
GENOMES_DIR = BASE_DIR/"data/genomes"
OUTPUT_DIR = BASE_DIR/"outputs/exonerate_results"

# Logging function
def log(message):
    print(message, flush=True)

# Function to find first match of genome
def find_genome_file(genus):
    pattern = re.compile(rf'{genus}.*\.(fa|fna|fasta)$', re.IGNORECASE)
    matching_files = []
    
    for file in GENOMES_DIR.glob('*'):
        if pattern.search(file.name):
            matching_files.append(file)
    
    if matching_files:
        return matching_files[0]
    return None

# Find exonerate executable
def get_exonerate_path():
    try:
        exonerate_path = subprocess.check_output(['which', 'exonerate']).decode('utf-8').strip()
        return exonerate_path
    except subprocess.CalledProcessError:
        log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Exonerate not found in PATH!")
        return "exonerate"

# Process each genus with Exonerate
def process_genus(genus, fasta_file):
    log(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Processing {genus} with Exonerate..")
    
    # Find genome file
    genome_file = find_genome_file(genus)
    if not genome_file:
        log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Genome file not found for {genus}, continuing..")
        return False
        
    log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Genome found: {genome_file.name}..")
    
    # Define output file
    output_file = OUTPUT_DIR/f"{genus}_exonerate.gff"
    
    # Get exonerate path
    exonerate_path = get_exonerate_path()
    
    # Execute exonerate
    cmd = [
        exonerate_path,
        "--model", "protein2genome",
        str(fasta_file),
        str(genome_file),
        "--showtargetgff", "yes",
        "--showalignment", "yes", 
        "--showvulgar", "yes",
        "--verbose", str(verbose),
        "--percent", str(min_percent),
        "--minintron", str(min_intron),
        "--maxintron", str(max_intron),
        "--bestn", str(bestn)
    ]
    
    log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Running Exonerate..")
    log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][CMD] {' '.join(cmd)}")
    
    try:
        with open(output_file, "w") as out:
            subprocess.run(cmd, check=True, stdout=out)
        log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Exonerate finished for {genus}, results in {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] Exonerate failed for {genus}: {e}")
        return False

# Main
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Find all FASTA files
    fasta_files = list(FILTERED_FASTA_DIR.glob('*.fasta'))
    
    if not fasta_files:
        log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] No FASTA files found in {FILTERED_FASTA_DIR}, exiting!")
        sys.exit(1)
    
    log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Found {len(fasta_files)} FASTA files to process")
    
    # Process each FASTA file
    success_count = 0
    for fasta_file in fasta_files:
        genus = fasta_file.stem
        try:
            if process_genus(genus, fasta_file):
                success_count += 1
        except Exception as e:
            log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Error processing {genus}: {str(e)}")
            continue
    
    log(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][FINISHED] Processed {success_count}/{len(fasta_files)} genera successfully")

if __name__ == "__main__":
    main()
