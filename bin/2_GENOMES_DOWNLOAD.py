from pathlib import Path
import pandas as pd
import subprocess
import os
from datetime import datetime

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Input file directory
input_file = BASE_DIR.parent / "inputs" / "species_frequency.csv"
df = pd.read_csv(input_file, sep=";")

# Genomes files directory
genomes_base_dir = BASE_DIR.parent / "data" / "genomes"
genomes_base_dir.mkdir(parents=True, exist_ok=True)

# Loop for downloading species files
for species in df["Species"]:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Downloading genome files for: {species}")
    safe_species = species.replace("_", " ")
    
    output_dir = genomes_base_dir / species
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / f"{species}.zip"
    cmd = [
        "datasets", "download", "genome", "taxon", f"{safe_species}",
        "--reference", "--include", "genome",
        "--filename", str(zip_path)
    ]
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Downloading genome files for: {species}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] {species}: File not downloaded")
print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][FINISHED]")
