#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import re
from pathlib import Path
import glob
from collections import defaultdict
from datetime import datetime


# Directories
BASE_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = BASE_DIR / "bin"
OUTPUT_DIR = BASE_DIR / "outputs"
INPUT_DIR = BASE_DIR / "inputs"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data" / "genomes"
SCHEMA_DIR = OUTPUT_DIR / "schema"

for d in [OUTPUT_DIR, LOG_DIR, SCHEMA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Read genome files and their sizes
def read_genome_file(genome_file):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Reading genome file: {genome_file}..")
    chromosomes = {}
    current_chr = None
    sequence = ""
    
    try:
        with open(genome_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_chr:
                        chromosomes[current_chr] = len(sequence)
                    
                    # Extract chromosome name
                    header = line[1:].split()
                    current_chr = header[0]
                    sequence = ""
                else:
                    sequence += line
        
        # Add last chromosome
        if current_chr:
            chromosomes[current_chr] = len(sequence)
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] Failed to read genome file {genome_file}: {str(e)}!")
        return {}
    
    print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Found {len(chromosomes)} chromosomes/scaffolds!")
    return chromosomes

# Read GFF file and gather positions
def read_gff_file(gff_file):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Reading GFF file: {gff_file}..")
    positions = defaultdict(list)
    
    try:
        with open(gff_file, 'r') as f:
            count = 0
            for line in f:
                if line.startswith('#'):
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    chrom = parts[0]
                    start = int(parts[3])
                    end = int(parts[4])
                    positions[chrom].append((start, end))
                    count += 1
        print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][DONE] Found {count} hints in {len(positions)} chromosomes/scaffolds!")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] Reading GFF file {gff_file}: {str(e)}!")
    return positions

# Generate visualizations with marked hints
def visualize_chromosomes(chromosomes, positions, output_file):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Generating visualizations for: {output_file}..")
    
    # Order chromosomes
    def chrom_sort_key(x):
        # Pattern 1: Chr1A, Chr2B, etc.
        match = re.match(r'Chr(\d+)([A-Z])', x)
        if match:
            return (int(match.group(1)), match.group(2))
        
        # Pattern 2: chromosome_1, chromosome_2, etc.
        match = re.match(r'chromosome_(\d+)', x)
        if match:
            return (int(match.group(1)), '')
        
        # Pattern 3:
        nums = re.findall(r'\d+', x)
        if nums:
            return (int(nums[0]), x)
        
        # Fallback for alphabetical order
        return (999, x)
    
    # Filter for only chromosomes with hints
    marked_chroms = set(positions.keys())
    
    # Verify match with GFF and genome
    valid_marked_chroms = [chrom for chrom in marked_chroms if chrom in chromosomes]
    
    if not valid_marked_chroms:
        print("  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][WARNING] No hints found for genome, continuing..")
        # If no hints are found, use fallback
        chrom_names = sorted(chromosomes.keys(), key=chrom_sort_key)
        # Limit exibition for 100 chromosomes/scaffolds
        if len(chrom_names) > 100:
            chrom_sizes = [(chrom, chromosomes[chrom]) for chrom in chrom_names]
            chrom_sizes.sort(key=lambda x: x[1], reverse=True)
            selected_chroms = [chrom for chrom, _ in chrom_sizes[:100]]
            selected_chroms.sort(key=chrom_sort_key)
        else:
            selected_chroms = chrom_names
    else:
        # Use only chromosomes/scaffolds with hints
        selected_chroms = sorted(valid_marked_chroms, key=chrom_sort_key)
        print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][STATUS] Showing {len(selected_chroms)} chromosomes/scaffolds with hints, continuing..")
    
    # Define colors
    chrom_color = '#E0E0E0'  # Chromosomes (GRAY)
    chrom_edge_color = '#404040'  # Border (GRAY)
    mark_color = '#D62728'  # Hints (Red)
    
    # Configure matplotlib
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans']
    
    # Configure figure size based on chromosome/scaffolds number
    fig_height = max(10, len(selected_chroms) * 0.3)
    fig_width = 14
    fig = plt.figure(figsize=(fig_width, fig_height), facecolor='white')
    ax = fig.add_subplot(111)
    
    # Configure style
    chrom_width = 0.35
    y_positions = np.arange(len(selected_chroms)) * 1.2
    
    # Scale chromosomes
    max_length = max(chromosomes[chrom] for chrom in selected_chroms)
    scale_factor = 10 / max_length  # Larger chromosome with 10 units
    
    # Draw chromosomes
    for i, chrom in enumerate(selected_chroms):
        length = chromosomes[chrom] * scale_factor
        
        # Draw chromosomes as rectangle with rounded edges
        rect = patches.FancyBboxPatch(
            (0, y_positions[i] - chrom_width/2),
            length, chrom_width,
            boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.05),
            linewidth=0.8, edgecolor=chrom_edge_color, facecolor=chrom_color, alpha=0.9
        )
        ax.add_patch(rect)
        
        # Add chromosomes label
        font_size = max(6, min(9, 300 / len(selected_chroms)))
        ax.text(-0.5, y_positions[i], chrom, va='center', ha='right', 
                fontsize=font_size, fontweight='bold', color='#303030')
        
        # Add hints
        if chrom in positions:
            for start, end in positions[chrom]:
                start_scaled = start * scale_factor
                end_scaled = end * scale_factor
                width_scaled = max(end_scaled - start_scaled, 0.01)
                
                # Draw each hint
                mark = patches.Rectangle(
                    (start_scaled, y_positions[i] - chrom_width/2),
                    width_scaled, chrom_width,
                    linewidth=0, edgecolor=None, facecolor=mark_color, alpha=0.85,
                    zorder=3
                )
                ax.add_patch(mark)
    
    # Configure axes
    ax.set_xlim(-2, 11)
    ax.set_ylim(-1, max(y_positions) + 1)
    
    # Remove axes
    ax.axis('off')
    ax.set_facecolor('white')
    
    # Add titles
    genus_name = os.path.basename(output_file).replace('.png', '')
    plt.title(f'Chromosome visualization with hints - {genus_name}', 
              fontsize=14, fontweight='bold', pad=15)
    
    # Add subtitles
    legend_elements = [
        patches.Patch(facecolor=chrom_color, edgecolor=chrom_edge_color, 
                    label='Chromosomes/Scaffolds', alpha=0.9),
        patches.Patch(facecolor=mark_color, label='Hint region', alpha=0.85)
    ]
    legend = ax.legend(handles=legend_elements, loc='upper right', 
                      frameon=True, framealpha=0.9, fontsize=9)
    legend.get_frame().set_linewidth(0.5)
    
    # Add information about chromosome/scaffolds numbers
    info_box = plt.figtext(0.02, 0.98, f"Total chromosomes/scaffolds: {len(chromosomes)}", 
                fontsize=9, va='top', color='#303030',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='#CCCCCC', 
                          pad=5, boxstyle='round,pad=0.5'))
    plt.figtext(0.02, 0.955, f"Shown chromosomes/scaffolds: {len(selected_chroms)}", 
                fontsize=9, va='top', color='#303030')
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][STATUS] Visualization saved as: {output_file}!")

# Find genome file for each genus
def find_matching_genome_file(genus_name, genome_dir):
    extensions = ['.fa', '.fna', '.fasta']
    for ext in extensions:
        pattern = os.path.join(genome_dir, f"{genus_name}*{ext}")
        files = glob.glob(pattern)
        if files:
            return files[0]
    
    # Fallback if not find genus
    for ext in extensions:
        pattern = os.path.join(genome_dir, f"*{genus_name}*{ext}")
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

# Process all GFF files wit _hints.gff
def process_all_files():
    hint_files = glob.glob(os.path.join(OUTPUT_DIR, "*_hints.gff"))
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][STATUS] Found {len(hint_files)} hint files, continuing..")
    
    for hint_file in hint_files:
        # Extract genus from file
        genus_name = os.path.basename(hint_file).split('_')[0]
        genus_name = genus_name.capitalize()
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][STATUS] Processing {genus_name}..")
        
        # Find genome file
        genome_file = find_matching_genome_file(genus_name, DATA_DIR)
        
        if not genome_file:
            print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] Genome file not found for {genus_name}!")
            continue
        
        # Output file
        output_file = os.path.join(SCHEMA_DIR, f"{genus_name.upper()}.png")
        
        # Read files
        chromosomes = read_genome_file(genome_file)
        if not chromosomes:
            print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][ERROR] Genome and hint files not matching for: {genome_file}!")
            continue
        
        positions = read_gff_file(hint_file)
        if not positions:
            print(f"  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][WARNING] Hint file with nno positions: {hint_file}!")
        
        # Generate visualization
        visualize_chromosomes(chromosomes, positions, output_file)

if __name__ == "__main__":
    print("[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][START] Initializing..")
    process_all_files()
    print("\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][FINISH] Finished!")
