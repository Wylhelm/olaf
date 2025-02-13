import json
from tools.data_transformer_tool import create_tool

def test_simple_transformation():
    """Test the data transformer with simple input structures."""
    
    # Create test data matching the agent's input format
    weather_data = json.dumps({
        "current_temp": -9.64,
        "current_conditions": "icy",
        "accumulation": 0.0,
        "forecast": [{
            "time": "2025-02-14 00:00:00",
            "snowfall": 0.232,
            "temp": -12.42
        }],
        "alerts": [{
            "level": "high",
            "message": "Icy conditions alert"
        }]
    })
    
    fuel_data = json.dumps({
        "fuel_level": 50.0
    })
    
    salt_data = json.dumps({
        "salt_level": 50.0
    })
    
    traffic_data = json.dumps({
        "active_routes": 8,
        "coverage": 75.0,
        "efficiency_scores": {
            "Route_A": 95.0,
            "Route_B": 85.0
        },
        "priority_zones": {
            "Zone_1": [100.0, "high"],
            "Zone_2": [80.0, "medium"]
        }
    })
    
    # Transform the data
    transformer = create_tool()
    result = transformer._run(
        weather_data=weather_data,
        fuel_data=fuel_data,
        salt_data=salt_data,
        traffic_data=traffic_data
    )
    
    # Print the result
    print("\nTransformed Data:")
    print(result)
    
    # Validate the result
    try:
        result_dict = json.loads(result)
        if "error" in result_dict:
            print("\nTransformation failed:")
            print(f"Error: {result_dict['error']}")
            print(f"Details: {result_dict['details']}")
            return False
            
        # Check for required sections
        required_sections = ['weather_data', 'resource_data', 'route_data', 'fleet_data', 'alerts_data']
        missing_sections = [section for section in required_sections if section not in result_dict]
        if missing_sections:
            print(f"\nMissing sections: {', '.join(missing_sections)}")
            return False
            
        print("\nTransformation successful!")
        return True
    except json.JSONDecodeError:
        print("\nFailed to parse transformed data as JSON")
        return False
    except Exception as e:
        print(f"\nValidation error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing data transformer with simple input structures...")
    success = test_simple_transformation()
    print(f"\nTest {'passed' if success else 'failed'}")
