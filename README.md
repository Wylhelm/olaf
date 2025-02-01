# OLAF - AI-Driven Snow Removal Optimization System

OLAF (Optimization for Local Area Facilities) is an intelligent snow removal management system built using CrewAI that helps municipalities and contractors optimize their snow removal operations through AI-driven decision making.

## Overview

OLAF uses a crew of specialized AI agents working together to handle different aspects of snow removal operations:

- **Global Planner**: Oversees and coordinates overall snow removal strategy
- **Weather Monitor**: Tracks and analyzes weather conditions and forecasts
- **Stock Resources Manager**: Manages inventory of salt and fuel resources
- **Route Optimizer**: Determines optimal snow removal routes
- **Notifications Manager**: Handles stakeholder communications and alerts

## Features

- **Weather Integration**: Real-time weather data collection and analysis
- **Traffic Analysis**: Integration of traffic data for route optimization
- **Resource Management**: 
  - Tracking of salt and fuel inventory levels
  - Smart resource allocation based on weather conditions
- **Route Optimization**: AI-powered route planning considering multiple factors
- **Stakeholder Communication**: Automated report generation and notifications
- **Multiple Operation Modes**:
  - Run: Execute snow removal optimization
  - Train: Train the AI crew with historical data
  - Test: Evaluate system performance
  - Replay: Review previous operations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/olaf.git
cd olaf
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

## Usage

OLAF can be run in different modes using the following commands:

```bash
# Regular execution
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main run

# Training mode
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main train <iterations> <filename>

# Test mode
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main test <iterations> <model_name>

# Replay mode
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main replay <task_id>
```

## Project Structure

```
olaf/
├── src/
│   └── ai_driven_snow_removal_optimization_for_municipalities_and_contractors/
│       ├── crew.py           # Core CrewAI implementation
│       ├── main.py          # Entry point and execution modes
│       ├── tools/           # Custom tools
│       │   ├── local_inventory_tool.py    # Resource inventory management
│       │   └── report_generator_tool.py   # HTML report generation
│       └── config/          # Configuration files
├── reports/                 # Generated HTML reports
├── knowledge/              # Knowledge base
└── db/                     # Database files
```

## Tools

### Local Inventory Tool
- Manages and queries local inventory of resources (salt and fuel)
- Supports semantic search of inventory data
- Maintains real-time inventory levels

### Report Generator Tool
- Generates formatted HTML reports
- Includes timestamps and operation details
- Provides clean, professional layout for stakeholder communication

## Configuration

The system uses several configuration files:

- `.env`: Environment variables and API keys
- `config/agents.yaml`: Agent configurations and roles
- `config/tasks.yaml`: Task definitions and parameters

## Reports

Reports are automatically generated in HTML format and stored in the `reports/` directory. Each report includes:
- Timestamp of generation
- Operation details
- Resource usage
- Route optimizations
- Weather conditions
- Stakeholder notifications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]
