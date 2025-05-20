from pyfaidx import Fasta
import subprocess
from pathlib import Path
import sys
import glob
import re
import os
from datetime import datetime 

# Base configuration
padding = 1000 # For sequence sizes (+-)
species = "wheat"  # Check with 'augustus --species=help'

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent
BLAST_RESULTS_DIR = BASE_DIR/"outputs/blast_results"
GENOMES_DIR = BASE_DIR/"data/genomes"
OUTPUT_DIR = BASE_DIR/"outputs"

# Function to find extrinsic file:
def find_extrinsic_cfg():
    # 1. Find in Augustus Path
    if 'AUGUSTUS_CONFIG_PATH' in os.environ:
        cfg_path = Path(os.environ['AUGUSTUS_CONFIG_PATH']) / "extrinsic" / "extrinsic.M.RM.E.W.cfg"
        if cfg_path.exists():
            return cfg_path
    
    # 2. Find in absolute Path
    try:
        which_output = subprocess.check_output(['which', 'augustus']).decode('utf-8').strip()
        augustus_dir = Path(which_output).parent.parent
        cfg_path = augustus_dir / "config" / "extrinsic" / "extrinsic.M.RM.E.W.cfg"
        if cfg_path.exists():
            return cfg_path
    except subprocess.CalledProcessError:
        pass
    
    for path in common_paths:
        if Path(path).exists():
            return Path(path)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Extrinsic configuration file not found, check your Augustus installation!")
    return None

# Check extrinsic valid types
def list_valid_hint_types(cfg_file):
    valid_types = []
    try:
        with open(cfg_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split()
                if len(parts) >= 2:
                    valid_types.append(parts[0])
        return list(set(valid_types))
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Invalid hint type: {e}, using 'exonpart' as failback..")
        return ["CDS", "start", "stop", "dss", "ass", "tss", "tts", "exonpart"]

# Find match genome with inserted genus
def find_genome_file(genus):
    pattern = re.compile(rf'{genus}.*\.(fa|fna|fasta)$', re.IGNORECASE)
    for file in GENOMES_DIR.glob('*'):
        if pattern.search(file.name):
            return file
    return None

# Generate hints file formated for Augustus
def generate_hints_file(blast_results, hints_gff, cfg_file):
    valid_types = list_valid_hint_types(cfg_file)
    hint_type = "ep" if "ep" in valid_types else "exonpart"
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Using hint type: {hint_type}..")
    
    with open(blast_results) as fin, open(hints_gff, 'w') as fout:
        for line in fin:
            if line.strip():
                fields = line.strip().split('\t')
                contig = fields[1]
                start = int(fields[8])
                end = int(fields[9])
                
                # Check start < end
                if start > end:
                    start, end = end, start
                
                strand = '+' if int(fields[8]) < int(fields[9]) else '-'
                evalue = fields[10]
                
                # Formatting for Augustus
                fout.write(f"{contig}\tblastX\t{hint_type}\t{start}\t{end}\t{evalue}\t{strand}\t.\tgrp={fields[0]};pri=4;src=M\n")

# Processing each genus
def process_genus(genus):
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Processing {genus} with {species}..")
    
    # Find genome files
    genome_file = find_genome_file(genus)
    if not genome_file:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Genome file not found for {genus}, continuing..")
        return
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Genome found: {genome_file.name}..")
    
    # Find extrinsic configuration
    extrinsic_cfg = find_extrinsic_cfg()
    if not extrinsic_cfg:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Processing without extrinsic configuration..")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][INFO] Using configuration: {extrinsic_cfg}")
    
    # Dynamic IO
    blast_results = BLAST_RESULTS_DIR/f"{genus}_BH.txt"
    output_fasta = OUTPUT_DIR/f"{genus}_regions.fasta"
    augustus_gff = OUTPUT_DIR/f"{genus}_{species}_augustus.gff"
    augustus_gtf = OUTPUT_DIR/f"{genus}_{species}_augustus.gtf"
    augustus_gtf_clean = OUTPUT_DIR/f"{genus}_{species}_augustus_clean.gtf"
    augustus_transcripts = OUTPUT_DIR/f"{genus}_transcripts.fasta"
    hints_gff = OUTPUT_DIR/f"{genus}_hints.gff"

    # Extract regions
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Extracting regions..")
    genome = Fasta(genome_file)
    regions = set()
    
    with open(blast_results) as f, open(output_fasta, "w") as out:
        for line in f:
            if line.strip():
                fields = line.split('\t')
                contig = fields[1]
                start = int(fields[8])
                end = int(fields[9])
                
                # Find valid coordinates
                region_start = max(1, min(start, end) - padding)
                region_end = min(len(genome[contig]), max(start, end) + padding)
                
                region_id = f"{contig}:{region_start}-{region_end}"
                if region_id not in regions:
                    regions.add(region_id)
                    try:
                        seq = genome[contig][region_start-1:region_end].seq
                        out.write(f">{region_id}\n{seq}\n")
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Ignoring region {region_id}: {str(e)}, continuing..")

    # Generate hint file
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Generating hint files..")
    generate_hints_file(blast_results, hints_gff, extrinsic_cfg)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Finished generating hint files..")

    # Running Augustus
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Running Augustus..")
    cmd = [
        "augustus",
        f"--species={species}",
        "--protein=on",
        "--gff3=on"
    ]
    
    # Include extrinsic file
    if extrinsic_cfg:
        cmd.append(f"--extrinsicCfgFile={extrinsic_cfg}")
        cmd.append(f"--hintsfile={hints_gff}")
    
    cmd.append(str(output_fasta))
    
    with open(augustus_gff, "w") as out:
        try:
            subprocess.run(cmd, check=True, stdout=out)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar Augustus: {e}")
            return
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Finished Augustus!")

    # Converting to GTF files
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Converting to GTF..")
    cmd_gffread = [
        "gffread",
        augustus_gff,
        "-T",
        "-o",
        augustus_gtf
    ]
    subprocess.run(cmd_gffread, check=True)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Finished conversion, results in {augustus_gtf}!")

    # Cleaning GTF file (for IGV)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Cleaning GTF headers..")
    cmd_clean = [
        "sed",
        r"s/^\([^[:space:]]\+\):[0-9]\+-[0-9]\+/\1/",
        augustus_gtf
    ]
    with open(augustus_gtf_clean, "w") as outfile:
        subprocess.run(cmd_clean, stdout=outfile, check=True)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Cleaned GTF saved to {augustus_gtf_clean}")
    
    # Generating transcript FASTA using gffread
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Generating transcript FASTA using gffread..")
    cmd_transcript = [
        "gffread",
        augustus_gff,
        "-g", output_fasta,
        "-w", augustus_transcripts
    ]
    
    try:
        subprocess.run(cmd_transcript, check=True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Transcript FASTA saved to: {augustus_transcripts}..")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] gffread failed: {e}")

# Main
if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Find all files *_BH.txt
    blast_files = glob.glob(str(BLAST_RESULTS_DIR/"*_BH.txt"))
    
    if not blast_files:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] No BLAST file found, run previous steps first!")
        sys.exit(1)
    
    # Processar cada arquivo BLAST
    for blast_file in blast_files:
        genus = Path(blast_file).stem.replace("_BH", "")
        try:
            process_genus(genus)
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ALERT] Error processing {genus}: {str(e)}")
            continue

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][FINISHED] All genus processed")
