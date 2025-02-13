import json
from tools.report_generator_tool import create_tool

def test_report_generation():
    # Create sample data following the exact schema
    test_data = {
        "weather_data": {
            "current_temp": -9.72,
            "current_conditions": "High risk of snow and icy conditions.",
            "accumulation": 5.42,
            "forecast": [
                {
                    "time": "Next hours",
                    "snowfall": 5.42,
                    "temp": -9.72
                },
                {
                    "time": "Future",
                    "snowfall": 2.32,
                    "temp": -9.0
                },
                {
                    "time": "Future",
                    "snowfall": 1.83,
                    "temp": -8.5
                },
                {
                    "time": "Future",
                    "snowfall": 0.37,
                    "temp": -8.0
                }
            ],
            "alerts": [
                {
                    "level": "High",
                    "message": "Immediate action needed for predicted high snowfall."
                }
            ]
        },
        "resource_data": {
            "salt_level": 575.0,
            "fuel_level": 7500.0,
            "depots": [
                {
                    "name": "Central Depot",
                    "status": "Operational",
                    "status_color": "Green"
                },
                {
                    "name": "North Depot",
                    "status": "Operational",
                    "status_color": "Green"
                }
            ]
        },
        "route_data": {
            "active_routes": 2,
            "coverage": 80.0,
            "efficiency_scores": {
                "Route 138": 75.0,
                "Rue de la rivière": 65.0
            },
            "priority_zones": {
                "Centre Ville": [90.0, "High"],
                "Levis": [75.0, "Medium"]
            }
        },
        "fleet_data": {
            "vehicles": [
                {
                    "id": "Truck 1",
                    "status": "Active",
                    "status_color": "Green",
                    "region": "Centre Ville",
                    "priority": "High"
                },
                {
                    "id": "Truck 2",
                    "status": "Active",
                    "status_color": "Green",
                    "region": "Levis",
                    "priority": "Medium"
                }
            ]
        },
        "alerts_data": [
            {
                "level": "High",
                "message": "Immediate action for snow removal in high priority zones"
            },
            {
                "level": "Medium",
                "message": "Monitor traffic incidents and adjust routes accordingly"
            }
        ]
    }

    # Create tool instance
    report_tool = create_tool()
    
    # Convert data to JSON string - this is the key part that was failing before
    # We pass the data directly as a JSON string, not wrapped in another dictionary
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
