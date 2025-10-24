#!/usr/bin/env python3
"""
Create distance distribution graph for members living under 5km from store.

This script reads the distance calculation results and creates a bar chart
showing the distribution of members in 0.5km increments up to 5km.
"""

import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path
from typing import Dict, List


def setup_matplotlib():
    """Setup matplotlib for better looking plots."""
    plt.style.use('default')
    plt.rcParams.update({
        'figure.figsize': (12, 6),
        'font.size': 10,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
    })


def load_distance_data(input_file: Path) -> Dict:
    """Load distance calculation results."""
    if not input_file.exists():
        print(f"Error: Input file does not exist: {input_file}")
        sys.exit(1)
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)


def create_distance_histogram(distances: List[float], max_distance: float = 5.0, step: float = 0.5) -> tuple:
    """Create histogram data for distance distribution."""
    # Filter distances under max_distance
    filtered_distances = [d for d in distances if d <= max_distance]
    
    # Create bins
    bins = np.arange(0, max_distance + step, step)
    
    # Calculate histogram
    counts, bin_edges = np.histogram(filtered_distances, bins=bins)
    
    # Create bin labels (center of each bin)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    return bin_centers, counts, len(filtered_distances)


def plot_distance_distribution(data: Dict, output_file: Path, max_distance: float = 5.0, step: float = 0.5):
    """Create and save distance distribution plot."""
    setup_matplotlib()
    
    # Extract distances
    distances = [member["distance_km"] for member in data["members"]]
    
    # Create histogram data
    bin_centers, counts, total_under_5km = create_distance_histogram(distances, max_distance, step)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create bar chart
    bars = ax.bar(bin_centers, counts, width=step*0.8, alpha=0.7, color='steelblue', edgecolor='navy', linewidth=0.5)
    
    # Customize the plot
    ax.set_xlabel('Distance from Store (km)', fontsize=12)
    ax.set_ylabel('Number of Members', fontsize=12)
    ax.set_title(f'Distance Distribution of Members Living Within {max_distance}km of Store\n(Step: {step}km, Total: {total_under_5km} members)', fontsize=14)
    
    # Set x-axis ticks to match bin centers
    ax.set_xticks(bin_centers)
    ax.set_xticklabels([f'{x:.1f}' for x in bin_centers], rotation=45)
    
    # Add grid
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   str(count), ha='center', va='bottom', fontsize=9)
    
    # Add statistics text box
    stats_text = f"""Statistics for members ≤{max_distance}km:
Total: {total_under_5km} members
Average: {np.mean([d for d in distances if d <= max_distance]):.2f} km
Median: {np.median([d for d in distances if d <= max_distance]):.2f} km
Min: {min([d for d in distances if d <= max_distance]):.3f} km"""
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Distance distribution plot saved to: {output_file}")
    
    # Print summary statistics
    print(f"\nDistance Distribution Summary (≤{max_distance}km):")
    print(f"Total members: {total_under_5km}")
    print(f"Percentage of all members: {(total_under_5km/len(distances)*100):.1f}%")
    print(f"Average distance: {np.mean([d for d in distances if d <= max_distance]):.2f} km")
    print(f"Median distance: {np.median([d for d in distances if d <= max_distance]):.2f} km")
    
    print(f"\nDistribution by {step}km bins:")
    for center, count in zip(bin_centers, counts):
        if count > 0:
            range_start = center - step/2
            range_end = center + step/2
            print(f"{range_start:.1f}-{range_end:.1f}km: {count} members ({count/total_under_5km*100:.1f}%)")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Create distance distribution graph")
    parser.add_argument(
        "--input",
        type=str,
        default="data/distances/member_distances.json",
        help="Input JSON file from calculate_distances.py (default: data/distances/member_distances.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/distances/distance_distribution.png",
        help="Output image file (default: data/distances/distance_distribution.png)",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=5.0,
        help="Maximum distance to include in graph (default: 5.0)",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.5,
        help="Distance step size for bins (default: 0.5)",
    )
    return parser.parse_args()


def main():
    """Main plotting workflow."""
    args = parse_arguments()
    
    # Load distance data
    input_file = Path(args.input)
    data = load_distance_data(input_file)
    
    # Create output directory if needed
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create and save plot
    plot_distance_distribution(data, output_file, args.max_distance, args.step)


if __name__ == "__main__":
    main()