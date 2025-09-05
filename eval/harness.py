# eval/harness.py
import os
import sys
import json
import time
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
import yaml

def run_experiment(map_path, strategy, seed, max_ticks=300):
    """
    Run a single experiment with the given parameters.
    
    Args:
        map_path: Path to the map configuration file
        strategy: Planning strategy to use (react, reflexion, plan_execute)
        seed: Random seed for reproducibility
        max_ticks: Maximum number of simulation ticks
    
    Returns:
        dict: Experiment results and metrics
    """
    
    # Import here to avoid circular imports
    from env.world import CrisisModel
    from reasoning.planner import make_plan
    
    # Load map configuration
    with open(map_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create model
    model = CrisisModel(
        width=config.get('width', 20),
        height=config.get('height', 20),
        rng_seed=seed,
        config=config,
        render=False
    )
    
    # Run simulation
    transcript = []
    start_time = time.time()
    
    for tick in range(max_ticks):
        # Check termination conditions
        if not model.running:
            break
            
        # Get current state
        state = model.summarize_state()
        
        # Generate plan using the specified strategy
        # Convert transcript items to strings for scratchpad
        scratchpad_items = []
        for item in transcript[-10:]:
            if isinstance(item, dict):
                scratchpad_items.append(f"Tick {item.get('tick', '?')}: {item.get('plan', {}).get('commands', [])}")
            else:
                scratchpad_items.append(str(item))
        
        plan = make_plan(state, strategy=strategy, scratchpad="\n".join(scratchpad_items))
        
        # Apply plan
        model.set_plan(plan.get("commands", []))
        
        # Log this tick
        tick_log = {
            "tick": tick,
            "context": state,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        }
        transcript.append(tick_log)
        
        # Step the model
        model.step()
        
        # Check if all survivors are resolved
        total_survivors = getattr(model, 'total_survivors', None)
        if total_survivors and (model.rescued + model.deaths >= total_survivors):
            break
    
    end_time = time.time()
    
    # Collect final metrics
    results = {
        "experiment_id": f"{Path(map_path).stem}_{strategy}_{seed}_{int(time.time())}",
        "map": Path(map_path).stem,
        "strategy": strategy,
        "seed": seed,
        "ticks": len(transcript),
        "runtime_seconds": end_time - start_time,
        "rescued": model.rescued,
        "deaths": model.deaths,
        "avg_rescue_time": getattr(model, 'avg_rescue_time', 0.0),
        "fires_extinguished": model.fires_extinguished,
        "roads_cleared": model.roads_cleared,
        "energy_used": model.energy_used,
        "tool_calls": model.tool_calls,
        "invalid_json": model.invalid_json,
        "replans": model.replans,
        "hospital_overflow_events": model.hospital_overflow_events,
        "transcript": transcript
    }
    
    return results

def save_results(results, output_dir="results"):
    """
    Save experiment results to the specified directory.
    
    Args:
        results: Experiment results dictionary
        output_dir: Directory to save results in
    """
    
    # Create output directories
    raw_dir = Path(output_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Save raw results
    raw_file = raw_dir / f"{results['experiment_id']}.json"
    with open(raw_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save transcript logs
    logs_dir = Path("logs") / f"strategy={results['strategy']}" / f"run={results['experiment_id']}"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    for tick_data in results['transcript']:
        tick_num = tick_data['tick']
        tick_file = logs_dir / f"tick{tick_num:03d}.jsonl"
        
        with open(tick_file, 'w') as f:
            # Write system prompt
            f.write(json.dumps({
                "role": "system",
                "content": f"Crisis response planning for tick {tick_num}"
            }) + "\n")
            
            # Write context
            f.write(json.dumps({
                "role": "user",
                "content": f"Current crisis situation: {json.dumps(tick_data['context'])}"
            }) + "\n")
            
            # Write plan
            f.write(json.dumps({
                "role": "assistant",
                "content": f"FINAL_JSON: {json.dumps(tick_data['plan'])}"
            }) + "\n")
    
    print(f"Saved results to {raw_file}")
    print(f"Saved logs to {logs_dir}")

def run_experiment_batch(maps, strategies, seeds, max_ticks=300):
    """
    Run a batch of experiments.
    
    Args:
        maps: List of map file paths
        strategies: List of strategy names
        seeds: List of random seeds
        max_ticks: Maximum ticks per experiment
    """
    
    all_results = []
    
    for map_path in maps:
        for strategy in strategies:
            for seed in seeds:
                print(f"Running {map_path} with {strategy} strategy, seed {seed}")
                
                try:
                    results = run_experiment(map_path, strategy, seed, max_ticks)
                    save_results(results)
                    all_results.append(results)
                    
                    # Print summary
                    print(f"  Completed: {results['rescued']} rescued, {results['deaths']} deaths, {results['ticks']} ticks")
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    continue
    
    return all_results

def aggregate_results(results_dir="results"):
    """
    Aggregate all experiment results into a summary CSV.
    
    Args:
        results_dir: Directory containing raw results
    """
    
    import pandas as pd
    
    raw_dir = Path(results_dir) / "raw"
    agg_dir = Path(results_dir) / "agg"
    agg_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all results
    all_results = []
    for json_file in raw_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            result = json.load(f)
            # Remove transcript to keep CSV manageable
            if 'transcript' in result:
                del result['transcript']
            all_results.append(result)
    
    if not all_results:
        print("No results found to aggregate")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_results)
    
    # Save aggregated results
    summary_file = agg_dir / "summary.csv"
    df.to_csv(summary_file, index=False)
    
    print(f"Saved aggregated results to {summary_file}")
    print(f"Total experiments: {len(all_results)}")
    
    # Print summary statistics
    print("\nSummary by strategy:")
    strategy_summary = df.groupby('strategy').agg({
        'rescued': ['mean', 'std'],
        'deaths': ['mean', 'std'],
        'ticks': ['mean', 'std'],
        'fires_extinguished': ['mean', 'std'],
        'roads_cleared': ['mean', 'std']
    }).round(2)
    
    print(strategy_summary)
    
    return df

if __name__ == "__main__":
    # Example usage - REMOVED 'cot' STRATEGY
    maps = ["configs/map_small.yaml", "configs/map_medium.yaml", "configs/map_hard.yaml"]
    strategies = ["react", "reflexion", "plan_execute"]  # Removed 'cot'
    seeds = [42, 123, 456, 789, 999]
    
    print("Starting experiment batch...")
    results = run_experiment_batch(maps, strategies, seeds)
    
    print("\nAggregating results...")
    aggregate_results()
    
    print("Experiment batch completed!")