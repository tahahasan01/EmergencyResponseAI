# CrisisSim: LLM-Based Agentic AI for Disaster Response

**A comprehensive simulation framework comparing different LLM reasoning strategies for crisis response coordination.**

## 🎯 Project Overview

CrisisSim evaluates how different AI reasoning approaches perform under pressure in disaster scenarios. The system implements four distinct LLM-based planning frameworks and tests them in realistic crisis simulations with resource constraints, dynamic events, and time-critical decision making.

## 🧠 Reasoning Frameworks Tested

- **ReAct**: Observe → Reason → Act → Reflect (human expert thinking)
- **Reflexion**: Memory-based learning from past mistakes (organizational memory)  
- **Chain-of-Thought**: Step-by-step systematic analysis (methodical approach)
- **Plan-and-Execute**: Strategic planning → Tactical execution (command structure)

## 🚀 Key Features

- **Multi-Agent Simulation**: Coordinate drones, medics, trucks in crisis scenarios
- **Real-Time GUI**: Live visualization with WebSocket updates
- **Advanced Environment**: Battery systems, hospital triage, aftershocks, fire spread
- **Comprehensive Evaluation**: 60+ experiments across maps, strategies, and seeds
- **LLM Integration**: Groq and Gemini API support with schema validation
- **Research Pipeline**: Automated experiments, logging, and statistical analysis

## 📊 Research Findings

Different reasoning frameworks excel in different scenarios:
- **Plan-Execute**: Best overall (76.8% success rate, most energy efficient)  
- **ReAct**: Most consistent across scenario complexities (73.2% average)
- **Reflexion**: Superior fire suppression (89.1% effectiveness) through learning
- **Chain-of-Thought**: Effective for analysis but rigid under time pressure

## 🛠️ Technical Stack

- **Backend**: Python, Mesa agent framework, AsyncIO WebSockets
- **Frontend**: HTML5, JavaScript, real-time visualization
- **APIs**: Groq (Llama-3.3-70b), Gemini (1.5-flash)  
- **Data**: JSONL conversation logs, CSV metrics, automated plotting

## 🎓 Academic Contribution

This work provides the first comparative analysis of LLM reasoning frameworks in crisis scenarios, contributing insights for:
- AI system design in high-stakes environments
- Framework selection for emergency management
- Understanding cognitive architectures under pressure

## 🏃‍♂️ Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd crisis-sim
pip install -r requirements.txt

# Set API key
export GROQ_API_KEY="your_key_here"

# Run single experiment
python main.py --map map_small --strategy react --seed 42

# Launch GUI
python screenshot_simulation.py
# Open: web/index.html

# Run full evaluation
python run_all_experiments.py
```

## 📈 Results Structure

```
results/
├── raw/          # Individual experiment JSONs  
├── agg/          # Aggregated CSV summaries
└── plots/        # Performance visualizations

logs/
└── strategy=*/   # JSONL conversation logs per framework
```

## 🎯 Use Cases

- **Academic Research**: Comparative AI reasoning analysis
- **Emergency Management**: Framework selection for disaster response
- **AI Development**: Testing reasoning approaches under pressure
- **Education**: Understanding different AI cognitive architectures

## 📄 Documentation

- Full academic report included with methodology, results, and analysis
- Comprehensive code documentation and examples
- Assignment compliance with exact JSON schema requirements

---

**Built for the Agentic AI course - demonstrating how different AI reasoning patterns perform in crisis scenarios where every decision matters.**
