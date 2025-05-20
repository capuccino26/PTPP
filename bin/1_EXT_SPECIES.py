import pandas as pd
from pathlib import Path
from datetime import datetime

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Generating table for species frequencies..")
# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load the input file from
input_file = BASE_DIR.parent / "inputs" / "PROT_IDS.xlsx"
df = pd.read_excel(input_file)

# Standardize species names
df["Species"] = df["Tax_Name"].str.strip().str.replace(r"[^\w]", "_", regex=True)

# Count frequency of each species
freq_table = df["Species"].value_counts().reset_index()
freq_table.columns = ["Species", "Frequency"]

# Ensure the 'outputs' directory exists
output_dir = BASE_DIR.parent / "outputs"
output_dir.mkdir(parents=True, exist_ok=True)

# Save the frequency table
output_path = output_dir / "species_frequency.csv"
freq_table.to_csv(output_path, sep=";", index=False)

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][FINISHED] Table saved to: {output_path}")
