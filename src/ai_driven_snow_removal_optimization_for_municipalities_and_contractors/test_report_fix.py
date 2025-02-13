import json
from tools.report_generator_tool import create_tool as create_report_tool
from tools.data_transformer_tool import create_tool as create_transformer_tool

def test_report_with_agent_data():
    """Test report generation with the agent's data format."""
    
    print("1. Preparing test data...")
    
    # Sample data in the format provided by the agent
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
    
    print("✓ Test data prepared")
    
    print("\n2. Transforming data...")
    # Transform the data
    transformer_tool = create_transformer_tool()
    transformed_data = transformer_tool._run(
        weather_data=weather_data,
        fuel_data=fuel_data,
        salt_data=salt_data,
        traffic_data=traffic_data
    )
    print("✓ Data successfully transformed")
    
    # Validate transformation result
    try:
        result_dict = json.loads(transformed_data)
        if "error" in result_dict:
            print(f"\nError: Transformation failed - {result_dict['error']}")
            print(f"Details: {result_dict['details']}")
            return None
    except json.JSONDecodeError:
        print("\nError: Failed to parse transformed data")
        return None
    
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

if __name__ == "__main__":
    print("Starting report generation test with agent data...\n")
    report_path = test_report_with_agent_data()
    
    if report_path:
        print(f"\nTest completed successfully!")
        print(f"You can view the report at: {report_path}")
    else:
        print("\nTest failed to generate report.")
