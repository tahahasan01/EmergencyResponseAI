# CrisisSim — Agentic AI for Disaster Response

A comprehensive simulation framework for testing LLM-based agentic AI systems in crisis response scenarios. This system implements multiple reasoning frameworks and realistic disaster response mechanics.

## 🚀 Features

### LLM-Based Reasoning Frameworks
- **ReAct**: Reasoning + Acting framework for crisis response planning
- **Reflexion**: Memory-based planning with critique and improvement
- **Chain-of-Thought (CoT)**: Step-by-step reasoning approach
- **Plan-and-Execute**: Two-phase strategic planning and execution

### Enhanced Environment Features
- **Battery System**: Drones consume battery and must recharge at depots
- **Medic Movement Penalty**: Medics move slower when carrying survivors
- **Resource Management**: Trucks have limited water/tools and must resupply
- **Enhanced Fire Spread**: Realistic fire propagation with building vulnerability
- **Aftershock System**: Dynamic disasters that create new obstacles
- **Hospital Triage**: Priority-based queuing system for survivors

### Advanced GUI
- **Visual Entity Representation**: Unique shapes/colors for all entities
- **Resource Status Display**: Battery levels, water/tool status with color coding
- **Comprehensive Statistics**: Real-time metrics and performance indicators
- **Enhanced Charts**: Performance tracking that stops on termination

### Experiment Infrastructure
- **Automated Testing**: Batch experiments across maps, strategies, and seeds
- **Comprehensive Logging**: JSONL logs for every tick with prompts/responses
- **Results Aggregation**: CSV summaries and statistical analysis
- **Visualization Tools**: Required plots and additional analysis charts

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd crisis-sim
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**:
   ```bash
   # For Groq (recommended)
   export GROQ_API_KEY="your_groq_api_key_here"
   
   # For Gemini
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```

## 🎯 Usage

### Running Single Experiments

```bash
# Run with ReAct strategy
python main.py --map configs/map_small.yaml --provider groq --strategy react --seed 42

# Run with Reflexion strategy
python main.py --map configs/map_medium.yaml --provider groq --strategy reflexion --seed 123

# Run with Chain-of-Thought
python main.py --map configs/map_hard.yaml --provider groq --strategy cot --seed 456

# Run with Plan-and-Execute
python main.py --map configs/map_small.yaml --provider groq --strategy plan_execute --seed 789
```

### Running the GUI

```bash
# Start the web interface
python server.py

# Access at http://127.0.0.1:8522
```

### Running Batch Experiments

```bash
# Run comprehensive experiment suite
python eval/harness.py

# This will run:
# - 3 maps × 4 strategies × 5 seeds = 60 experiments
# - Save results to results/raw/
# - Generate aggregated CSV in results/agg/
```

### Generating Plots

```bash
# Create all required visualizations
python eval/plots.py

# Plots will be saved to results/plots/
```

## 📊 Experiment Protocol

The system is designed to run comprehensive experiments:

- **Maps**: `map_small.yaml`, `map_medium.yaml`, `map_hard.yaml`
- **Strategies**: `react`, `reflexion`, `cot`, `plan_execute`
- **Seeds**: 5 random seeds per map-strategy combination
- **Total**: 60 experiments minimum

### Output Structure

```
results/
├── raw/                    # Individual experiment JSON files
├── agg/                    # Aggregated CSV summaries
└── plots/                  # Generated visualizations

logs/
└── strategy=<name>/        # JSONL logs per strategy
    └── run=<id>/          # Per-run logs
        ├── tick000.jsonl  # Tick-by-tick conversation logs
        ├── tick001.jsonl
        └── ...
```

## 🔧 Configuration

### Map Configuration

Maps are defined in YAML format:

```yaml
width: 20
height: 20
depot: [1, 1]
hospitals:
  - [17, 2]
  - [15, 15]
buildings:
  - [5, 5]
  - [6, 5]
initial_fires:
  - [8, 3]
rubble:
  - [7, 7]
survivors: 15
```

### Environment Parameters

Key parameters in the simulation:

- `p_fire_spread`: Probability of fire spreading (default: 0.15)
- `p_aftershock`: Probability of aftershock per tick (default: 0.02)
- `hospital_service_rate`: Patients served per tick per hospital (default: 2)

## 📈 Metrics Tracked

- **Rescue Metrics**: Survivors rescued, deaths, average rescue time
- **Efficiency Metrics**: Fires extinguished, roads cleared, energy used
- **Quality Metrics**: Invalid JSON attempts, replans, hospital overflows
- **Resource Metrics**: Battery levels, water/tool consumption

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_system.py
```

This will verify:
- All modules can be imported
- Planning strategies generate valid plans
- Environment features are properly implemented
- Configuration files exist
- Evaluation tools are available

## 📝 Logging and Debugging

### LLM Response Logging

Every tick generates detailed logs:

```jsonl
{"role": "system", "content": "Crisis response planning for tick 0"}
{"role": "user", "content": "Current crisis situation: {...}"}
{"role": "assistant", "content": "FINAL_JSON: {\"commands\": [...]}"}
```

### Error Handling

- Invalid JSON responses increment `invalid_json` metric
- Failed planning attempts increment `replans` metric
- Resource depletion prevents agent actions

## 🎨 Customization

### Adding New Strategies

1. Create a new module in `reasoning/`
2. Implement the required interface:
   ```python
   def strategy_name_plan(context, scratchpad=""):
       return ("final", json.dumps(plan_dict))
   ```
3. Add to `reasoning/planner.py`

### Adding New Environment Features

1. Extend `env/dynamics.py` with new mechanics
2. Update `env/world.py` to integrate new features
3. Add metrics tracking in the model

## 📚 Architecture

```
crisis-sim/
├── main.py                 # CLI experiment runner
├── server.py               # Web GUI server
├── reasoning/              # LLM reasoning frameworks
│   ├── planner.py         # Strategy dispatcher
│   ├── react.py           # ReAct implementation
│   ├── reflexion.py       # Reflexion with memory
│   ├── cot.py             # Chain-of-Thought
│   ├── plan_execute.py    # Plan-and-Execute
│   └── llm_client.py      # API client (Groq/Gemini)
├── env/                    # Simulation environment
│   ├── world.py           # Main simulation model
│   ├── agents.py          # Agent implementations
│   └── dynamics.py        # World dynamics
├── configs/                # Map configurations
├── eval/                   # Experiment infrastructure
│   ├── harness.py         # Batch experiment runner
│   └── plots.py           # Visualization tools
└── results/                # Experiment outputs
```

## 🤝 Contributing

1. Follow the existing code structure
2. Ensure all tests pass: `python test_system.py`
3. Add comprehensive logging for new features
4. Update documentation for any new capabilities

## 📄 License

This project is part of the Agentic AI course assignment. Please refer to your course materials for usage guidelines.

## 🆘 Troubleshooting

### Common Issues

1. **API Key Not Set**: Ensure `GROQ_API_KEY` environment variable is set
2. **Import Errors**: Run `python test_system.py` to identify missing dependencies
3. **Planning Failures**: Check logs for LLM response errors
4. **GUI Not Loading**: Verify Mesa installation and port availability

### Performance Tips

- Use lower temperature settings (0.1) for more consistent LLM responses
- Limit scratchpad length to control token usage
- Monitor API rate limits for production use

---

**Happy Crisis Response Planning! 🚑🚒🚁**
