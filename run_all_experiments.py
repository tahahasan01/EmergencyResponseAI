#!/usr/bin/env python3
"""
Run all experiments for the CrisisSim assignment.
This script executes the full experimental pipeline:
1. Run experiments across all map-strategy-seed combinations
2. Aggregate results
3. Generate plots
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from eval.harness import run_experiment_batch
from eval.aggregate_results import aggregate_results
from eval.plots import create_required_plots

def main():
    print("🚀 Starting CrisisSim Experiments")
    print("=" * 50)
    
    # Define experiment parameters
    maps = [
        "configs/map_small.yaml",
        "configs/map_medium.yaml", 
        "configs/map_hard.yaml"
    ]
    
    strategies = [
        "react",
        "reflexion", 
        "plan_execute",
        "cot"  # Chain-of-Thought
    ]
    
    seeds = [42, 123, 456, 789, 999]  # 5 seeds as required
    
    print(f"📋 Experiment Plan:")
    print(f"  Maps: {len(maps)} ({[Path(m).stem for m in maps]})")
    print(f"  Strategies: {len(strategies)} ({strategies})")
    print(f"  Seeds: {len(seeds)} ({seeds})")
    print(f"  Total experiments: {len(maps) * len(strategies) * len(seeds)}")
    print()
    
    # Step 1: Run batch experiments
    print("🔬 Step 1: Running batch experiments...")
    try:
        results = run_experiment_batch(maps, strategies, seeds, max_ticks=300)
        print(f"✅ Completed {len(results)} experiments successfully")
    except Exception as e:
        print(f"❌ Error in batch experiments: {e}")
        return
    
    # Step 2: Aggregate results
    print("\n📊 Step 2: Aggregating results...")
    try:
        df = aggregate_results("results/raw", "results/agg")
        if df is None:
            print("❌ No results to aggregate")
            return
        print(f"✅ Aggregated {len(df)} results")
    except Exception as e:
        print(f"❌ Error aggregating results: {e}")
        return
    
    # Step 3: Generate plots
    print("\n📈 Step 3: Generating plots...")
    try:
        create_required_plots("results", "results/plots")
        print("✅ All plots generated successfully")
    except Exception as e:
        print(f"❌ Error generating plots: {e}")
        return
    
    print("\n🎉 All experiments completed successfully!")
    print("📁 Results saved to:")
    print("  - Raw results: results/raw/")
    print("  - Aggregated CSV: results/agg/summary.csv") 
    print("  - Plots: results/plots/")
    print("  - Logs: logs/strategy=<name>/run=<id>/")
    print("\n📊 You can now review the results and create your report!")

if __name__ == "__main__":
    main()
