<img src="logo2.png" alt="OLAF Logo" width="200"/>

# OLAF - AI-Driven Snow Removal Optimization System

OLAF (Optimization for Local Area Facilities) is an advanced AI-driven system designed to optimize snow removal operations for municipalities and contractors. Using CrewAI technology, it orchestrates multiple specialized AI agents to coordinate and optimize all aspects of snow removal operations.

## Features

- 🌨️ Real-time weather monitoring and forecasting
- 🚛 Dynamic route optimization with traffic integration
- 📊 Resource and inventory management
- 📱 Interactive HTML reporting and stakeholder communication
- 🤖 AI-powered decision making and coordination
- 🗺️ TomTom traffic data integration
- 📈 Automated resource allocation
- ⚡ Real-time operational adjustments

## System Architecture

OLAF employs a multi-agent system using CrewAI, with each agent specializing in specific aspects of snow removal operations:

### Agents

1. **Global Planification Coordinator**
   - Orchestrates overall operations
   - Coordinates between all agents
   - Makes strategic decisions based on integrated data

2. **Weather Monitoring Specialist**
   - Monitors real-time weather conditions
   - Analyzes snow accumulation patterns
   - Predicts weather impacts on operations

3. **Stock and Resources Manager**
   - Tracks inventory levels
   - Optimizes resource distribution
   - Prevents resource shortages

4. **Route Optimization Expert**
   - Creates efficient snow removal routes
   - Integrates traffic and weather data
   - Adapts routes in real-time

5. **Notifications and Alerts Manager**
   - Generates interactive HTML reports
   - Maintains stakeholder communications
   - Creates visual data representations

### Tasks

The system executes the following sequential tasks:

1. **Global Planning**
   - Creates high-level strategy
   - Coordinates all operational aspects

2. **Weather Data Collection**
   - Gathers comprehensive weather data
   - Analyzes conditions and forecasts

3. **Traffic Data Integration**
   - Monitors real-time traffic conditions
   - Identifies road closures and incidents

4. **Resource Monitoring**
   - Tracks inventory levels
   - Calculates resource requirements

5. **Route Optimization**
   - Generates efficient routes
   - Considers all operational factors

6. **Stakeholder Communication**
   - Produces interactive reports
   - Sends automated alerts

## Project Structure

```
olaf/
├── src/
│   └── ai_driven_snow_removal_optimization_for_municipalities_and_contractors/
│       ├── config/
│       │   ├── agents.yaml     # Agent configurations and roles
│       │   └── tasks.yaml      # Task definitions and workflows
│       ├── tools/
│       │   ├── custom_tool.py
│       │   ├── local_inventory_tool.py
│       │   ├── report_generator_tool.py
│       │   ├── tomtom_traffic_tool.py
│       │   └── weather_data_tool.py
│       ├── __init__.py
│       ├── crew.py            # Core CrewAI implementation
│       ├── main.py           # Main execution script
│       ├── fuel_inv.json     # Fuel inventory tracking
│       └── salt_inv.json     # Salt inventory tracking
├── reports/                  # Generated HTML reports
├── knowledge/               # Knowledge base
├── db/                      # Database files
├── requirements.txt         # Project dependencies
├── pyproject.toml          # Project configuration
├── .env.example            # Environment variables template
└── README.md               # Project documentation
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Wylhelm/olaf.git
cd olaf
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and add your API keys:
```
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
TOMTOM_API_KEY=your-tomtom-api-key
OPENWEATHER_API_KEY=your-openweather-api-key
```

## Usage

OLAF provides several operational modes:

### Run Mode
Execute the main operational workflow:
```bash
crew ai run
```

### Training Mode
Train the crew for a specified number of iterations:
```bash
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main train <iterations> <filename>
```

### Replay Mode
Replay execution from a specific task:
```bash
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main replay <task_id>
```

### Test Mode
Test execution with different models:
```bash
python -m src.ai_driven_snow_removal_optimization_for_municipalities_and_contractors.main test <iterations> <model_name>
```

## Tools and Integrations

OLAF integrates several external services and tools:

- **WeatherDataTool**: Interfaces with OpenWeather API for real-time weather data
- **TomTomTrafficTool**: Utilizes TomTom's API for traffic data and route optimization
- **LocalInventoryTool**: Manages local resource inventory tracking
- **ReportGeneratorTool**: Creates interactive HTML reports
- **ScrapeWebsiteTool**: Gathers additional data from online sources
- **JSONSearchTool**: Processes and analyzes JSON data

## Configuration

The system uses YAML configuration files for agents and tasks:

- `config/agents.yaml`: Defines agent roles, goals, and capabilities
- `config/tasks.yaml`: Specifies task descriptions and workflows

## Required API Keys

The following API keys are required for full functionality:

- OpenAI API key (for GPT models)
- Anthropic API key (for Claude models)
- TomTom API key (for traffic data)
- OpenWeather API key (for weather data)

## Output

OLAF generates detailed HTML reports in the `reports/` directory, including:

- Current weather conditions and forecasts
- Optimized route maps with traffic overlay
- Resource inventory status
- Operational recommendations
- Progress tracking

## License

MIT

## Contributors

Cgi Innovation & Immersive Systems Community
