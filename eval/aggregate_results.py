#!/usr/bin/env python3
"""
Aggregate experiment results into summary CSV for plotting.
"""

import json
import pandas as pd
from pathlib import Path
import glob

def aggregate_results(results_dir="results/raw", output_dir="results/agg"):
    """Aggregate all experiment results into a summary CSV."""
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all result files
    result_files = glob.glob(f"{results_dir}/*.json")
    print(f"Found {len(result_files)} result files")
    
    results = []
    
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract filename info
            filename = Path(file_path).stem
            parts = filename.split('_')
            
            # Parse strategy and map from filename
            if len(parts) >= 3:
                map_name = parts[0] + "_" + parts[1]  # map_small, map_medium, map_hard
                strategy = parts[2]
                seed = parts[3] if len(parts) > 3 else "unknown"
            else:
                map_name = "unknown"
                strategy = "unknown"
                seed = "unknown"
            
            # Add metadata
            data['map'] = map_name
            data['strategy'] = strategy
            data['seed'] = seed
            data['filename'] = filename
            
            results.append(data)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    if results:
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Save aggregated results
        output_file = Path(output_dir) / "summary.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ Aggregated {len(results)} results to {output_file}")
        
        # Show summary
        print(f"\n📊 Results Summary:")
        print(f"Strategies: {df['strategy'].unique()}")
        print(f"Maps: {df['map'].unique()}")
        print(f"Total experiments: {len(df)}")
        
        return df
    else:
        print("❌ No valid results found")
        return None

if __name__ == "__main__":
    print("🔍 Aggregating CrisisSim Results")
    print("=" * 40)
    
    df = aggregate_results()
    
    if df is not None:
        print("\n🎉 Aggregation complete!")
        print("📁 You can now run: python generate_assignment_plots.py")
