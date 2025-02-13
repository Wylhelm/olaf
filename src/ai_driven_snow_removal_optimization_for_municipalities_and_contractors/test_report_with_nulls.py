import json
from tools.report_generator_tool import create_tool

def test_report_generation():
    # Test data with null values matching the agent's output
    test_data = {
        "weather_data": {
            "current_temp": -9.86,
            "current_conditions": "Icy",
            "accumulation": 0.75,
            "forecast": [
                {"time": "Next few hours", "snowfall": 0.75, "temp": -9.86}
            ],
            "alerts": [
                {"level": "Medium", "message": "Additional snowfall expected, accumulate 5-10 mm in the next hours"}
            ]
        },
        "resource_data": {
            "salt_level": None,
            "fuel_level": None,
            "depots": []
        },
        "route_data": {
            "active_routes": 3,
            "coverage": None,
            "efficiency_scores": {},
            "priority_zones": {}
        },
        "fleet_data": {
            "vehicles": []
        },
        "alerts_data": [
            {"level": "High", "message": "Traffic incidents and road closures detected, monitor closely and reroute as needed."}
        ]
    }

    # Create tool instance
    report_tool = create_tool()
    
    # Convert data to JSON string
    input_str = json.dumps(test_data)
    
    # Generate report
    try:
        report_path = report_tool._run(input_str)
        print(f"Report generated successfully at: {report_path}")
        return report_path
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return None

if __name__ == "__main__":
    test_report_generation()
