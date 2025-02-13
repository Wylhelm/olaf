import json
from tools.report_generator_tool import create_tool

# Create properly formatted test data
test_data = {
    "weather_data": {
        "current_temp": -9.72,
        "current_conditions": "Icy roads",
        "accumulation": 0.0,
        "forecast": [
            {
                "time": "21:00",
                "snowfall": 5.42,
                "temp": -9.72
            }
        ],
        "alerts": [
            {
                "level": "warning",
                "message": "Snow expected"
            }
        ]
    },
    "resource_data": {
        "salt_level": 75.0,
        "fuel_level": 60.0,
        "depots": [
            {
                "name": "Main Depot",
                "status": "Operational",
                "status_color": "success"
            }
        ]
    },
    "route_data": {
        "active_routes": 2,
        "coverage": 75.0,
        "efficiency_scores": {
            "Route A": 85.0,
            "Route B": 78.0
        },
        "priority_zones": {
            "Highway Network": [80, "success"],
            "Emergency Routes": [70, "warning"],
            "Commercial": [60, "danger"]
        }
    },
    "fleet_data": {
        "vehicles": [
            {
                "id": "Truck 1",
                "status": "Operational",
                "status_color": "success",
                "region": "Zone 1",
                "priority": "High"
            }
        ]
    },
    "alerts_data": [
        {
            "level": "danger",
            "message": "Replenishment required"
        },
        {
            "level": "warning", 
            "message": "Heavy snowfall expected"
        }
    ]
}

def test_report_generation():
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
