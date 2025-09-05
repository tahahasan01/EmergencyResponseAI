# eval/plots.py
import os
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def create_required_plots(results_dir="results", plots_dir="results/plots"):
    """
    Create all required plots from the experiment results.
    
    Args:
        results_dir: Directory containing results
        plots_dir: Directory to save plots
    """
    
    # Create plots directory
    plots_path = Path(plots_dir)
    plots_path.mkdir(parents=True, exist_ok=True)
    
    # Load aggregated results
    summary_file = Path(results_dir) / "agg" / "summary.csv"
    if not summary_file.exists():
        print(f"Summary file not found: {summary_file}")
        return
    
    df = pd.read_csv(summary_file)
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Bar plot: rescued and deaths by strategy × map
    create_strategy_map_comparison(df, plots_path)
    
    # 2. Line plot: cumulative rescued over ticks
    create_cumulative_rescue_plot(df, plots_path)
    
    # 3. Box plot: average rescue time per strategy
    create_rescue_time_boxplot(df, plots_path)
    
    # 4. Additional useful plots
    create_resource_efficiency_plot(df, plots_path)
    create_success_rate_plot(df, plots_path)
    
    print(f"All plots saved to {plots_path}")

def create_strategy_map_comparison(df, plots_path):
    """Create bar plot comparing rescued and deaths by strategy and map."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Rescued survivors
    pivot_rescued = df.pivot_table(
        values='rescued', 
        index='map', 
        columns='strategy', 
        aggfunc='mean'
    )
    
    pivot_rescued.plot(kind='bar', ax=ax1, color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    ax1.set_title('Average Survivors Rescued by Strategy and Map', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Number of Survivors Rescued')
    ax1.set_xlabel('Map')
    ax1.legend(title='Strategy', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.tick_params(axis='x', rotation=45)
    
    # Deaths
    pivot_deaths = df.pivot_table(
        values='deaths', 
        index='map', 
        columns='strategy', 
        aggfunc='mean'
    )
    
    pivot_deaths.plot(kind='bar', ax=ax2, color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    ax2.set_title('Average Deaths by Strategy and Map', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Number of Deaths')
    ax2.set_xlabel('Map')
    ax2.legend(title='Strategy', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(plots_path / 'strategy_map_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_cumulative_rescue_plot(df, plots_path):
    """Create line plot showing cumulative rescues over time."""
    
    plt.figure(figsize=(12, 8))
    
    # Group by strategy and calculate cumulative rescues
    for strategy in df['strategy'].unique():
        strategy_data = df[df['strategy'] == strategy]
        
        # Calculate average rescues at different tick intervals
        tick_intervals = [25, 50, 75, 100, 150, 200, 250, 300]
        avg_rescues = []
        
        for max_ticks in tick_intervals:
            # Filter data where experiment ran at least this long
            valid_data = strategy_data[strategy_data['ticks'] >= max_ticks]
            if len(valid_data) > 0:
                avg_rescues.append(valid_data['rescued'].mean())
            else:
                avg_rescues.append(np.nan)
        
        # Plot with error bars
        valid_indices = [i for i, x in enumerate(avg_rescues) if not np.isnan(x)]
        if valid_indices:
            plt.plot([tick_intervals[i] for i in valid_indices], 
                    [avg_rescues[i] for i in valid_indices], 
                    marker='o', linewidth=2, label=f'{strategy}', markersize=8)
    
    plt.xlabel('Simulation Ticks', fontsize=12)
    plt.ylabel('Average Cumulative Survivors Rescued', fontsize=12)
    plt.title('Cumulative Survivors Rescued Over Time by Strategy', fontsize=14, fontweight='bold')
    plt.legend(title='Strategy', fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 300)
    
    plt.tight_layout()
    plt.savefig(plots_path / 'cumulative_rescue_over_time.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_rescue_time_boxplot(df, plots_path):
    """Create box plot showing rescue time distribution by strategy."""
    
    plt.figure(figsize=(10, 6))
    
    # Filter out invalid rescue times
    valid_data = df[df['avg_rescue_time'] > 0]
    
    if len(valid_data) > 0:
        # Create box plot
        sns.boxplot(data=valid_data, x='strategy', y='avg_rescue_time', palette='husl')
        plt.title('Distribution of Average Rescue Time by Strategy', fontsize=14, fontweight='bold')
        plt.xlabel('Strategy', fontsize=12)
        plt.ylabel('Average Rescue Time (ticks)', fontsize=12)
        plt.xticks(rotation=45)
        
        # Add individual data points
        sns.stripplot(data=valid_data, x='strategy', y='avg_rescue_time', 
                     color='black', alpha=0.5, size=4)
        
        plt.tight_layout()
        plt.savefig(plots_path / 'rescue_time_distribution.png', dpi=300, bbox_inches='tight')
    else:
        print("No valid rescue time data found for box plot")
    
    plt.close()

def create_resource_efficiency_plot(df, plots_path):
    """Create plot showing resource efficiency metrics."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Fires extinguished
    pivot_fires = df.pivot_table(values='fires_extinguished', index='map', columns='strategy', aggfunc='mean')
    pivot_fires.plot(kind='bar', ax=axes[0,0], color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    axes[0,0].set_title('Fires Extinguished', fontweight='bold')
    axes[0,0].set_ylabel('Count')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # Roads cleared
    pivot_roads = df.pivot_table(values='roads_cleared', index='map', columns='strategy', aggfunc='mean')
    pivot_roads.plot(kind='bar', ax=axes[0,1], color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    axes[0,1].set_title('Roads Cleared', fontweight='bold')
    axes[0,1].set_ylabel('Count')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # Energy used
    pivot_energy = df.pivot_table(values='energy_used', index='map', columns='strategy', aggfunc='mean')
    pivot_energy.plot(kind='bar', ax=axes[1,0], color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    axes[1,0].set_title('Energy Used', fontweight='bold')
    axes[1,0].set_ylabel('Count')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # Invalid JSON attempts
    pivot_invalid = df.pivot_table(values='invalid_json', index='map', columns='strategy', aggfunc='mean')
    pivot_invalid.plot(kind='bar', ax=axes[1,1], color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'])
    axes[1,1].set_title('Invalid JSON Attempts', fontweight='bold')
    axes[1,1].set_ylabel('Count')
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(plots_path / 'resource_efficiency_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_success_rate_plot(df, plots_path):
    """Create plot showing success rates and failure metrics."""
    
    # Calculate success rate (rescued / (rescued + deaths))
    df['success_rate'] = df['rescued'] / (df['rescued'] + df['deaths'])
    df['success_rate'] = df['success_rate'].fillna(0)
    
    plt.figure(figsize=(12, 6))
    
    # Success rate by strategy
    success_by_strategy = df.groupby('strategy')['success_rate'].agg(['mean', 'std']).reset_index()
    
    x_pos = np.arange(len(success_by_strategy))
    plt.bar(x_pos, success_by_strategy['mean'], 
            yerr=success_by_strategy['std'], 
            capsize=5, 
            color=['#2ecc71', '#3498db', '#e74c3c', '#f39c12'],
            alpha=0.8)
    
    plt.xlabel('Strategy', fontsize=12)
    plt.ylabel('Success Rate (rescued / total)', fontsize=12)
    plt.title('Success Rate by Strategy', fontsize=14, fontweight='bold')
    plt.xticks(x_pos, success_by_strategy['strategy'])
    plt.ylim(0, 1)
    
    # Add value labels on bars
    for i, v in enumerate(success_by_strategy['mean']):
        plt.text(i, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_path / 'success_rate_by_strategy.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Create all required plots
    create_required_plots()
    print("All plots generated successfully!")
