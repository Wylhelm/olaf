import json
from tools.report_generator_tool import create_tool as create_report_tool
from tools.data_transformer_tool import create_tool as create_transformer_tool
from tools.weather_data_tool import create_tool as create_weather_tool
from tools.local_inventory_tool import create_tool as create_inventory_tool
from tools.tomtom_traffic_tool import create_tool as create_traffic_tool

def test_report_generation():
    """Test the complete report generation workflow using actual data from tools."""
    
    print("1. Collecting data from source tools...")
    
    # Get weather data
    weather_tool = create_weather_tool()
    weather_data = weather_tool._run()
    print("✓ Weather data collected")
    
    # Get inventory data
    inventory_tool = create_inventory_tool()
    fuel_data = inventory_tool._run(resource_type="fuel")
    salt_data = inventory_tool._run(resource_type="salt")
    print("✓ Inventory data collected")
    
    # Get traffic data
    traffic_tool = create_traffic_tool()
    traffic_data = traffic_tool._run()
    print("✓ Traffic data collected")
    
    print("\n2. Transforming data...")
    # Transform collected data
    transformer_tool = create_transformer_tool()
    transformed_data = transformer_tool._run(
        weather_data=weather_data,
        fuel_data=fuel_data,
        salt_data=salt_data,
        traffic_data=traffic_data
    )
    print("✓ Data successfully transformed")
    
    print("\n3. Generating report...")
    # Generate report using transformed data
    report_tool = create_report_tool()
    try:
        report_path = report_tool._run(transformed_data)
        print(f"✓ Report generated successfully at: {report_path}")
        return report_path
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return None

# Example of expected data structure after transformation
expected_data_structure = {
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

def validate_data_structure(data):
    """Validate that the transformed data matches the expected structure."""
    try:
        data_dict = json.loads(data)
        required_sections = ['weather_data', 'resource_data', 'route_data', 'fleet_data', 'alerts_data']
        
        # Check all required sections exist
        missing_sections = [section for section in required_sections if section not in data_dict]
        if missing_sections:
            print(f"Warning: Missing sections in transformed data: {', '.join(missing_sections)}")
            return False
            
        # Validate weather_data structure
        weather = data_dict.get('weather_data', {})
        if not all(key in weather for key in ['current_temp', 'current_conditions', 'accumulation', 'forecast', 'alerts']):
            print("Warning: Incomplete weather_data structure")
            return False
            
        # Validate resource_data structure
        resources = data_dict.get('resource_data', {})
        if not all(key in resources for key in ['salt_level', 'fuel_level', 'depots']):
            print("Warning: Incomplete resource_data structure")
            return False
            
        # Validate route_data structure
        routes = data_dict.get('route_data', {})
        if not all(key in routes for key in ['active_routes', 'coverage', 'efficiency_scores', 'priority_zones']):
            print("Warning: Incomplete route_data structure")
            return False
            
        print("✓ Data structure validation passed")
        return True
    except json.JSONDecodeError:
        print("Error: Invalid JSON data")
        return False
    except Exception as e:
        print(f"Error validating data structure: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting report generation test...\n")
    report_path = test_report_generation()
    
    if report_path:
        print(f"\nTest completed successfully!")
        print(f"You can view the report at: {report_path}")
    else:
        print("\nTest failed to generate report.")
