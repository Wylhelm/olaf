from crewai.tools import BaseTool
from typing import Dict, Any
import json
from datetime import datetime

class DataTransformerTool(BaseTool):
    """Tool for transforming data from various sources into the report generator format."""
    
    name: str = "Data Transformer"
    description: str = """
    Transforms data from WeatherDataTool, LocalInventoryTool, and TomTomTrafficTool 
    into the format required by ReportGeneratorTool.
    """

    def _transform_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform weather data into report format."""
        try:
            # If weather_data is already a dictionary, use it directly
            if isinstance(weather_data, dict):
                data = weather_data
            # If it's a string, try to parse it as JSON
            elif isinstance(weather_data, str):
                data = json.loads(weather_data)
            else:
                raise ValueError(f"Unexpected weather_data type: {type(weather_data)}")

            # Return data in the expected format
            return {
                "current_temp": float(data.get('current_temp', 0.0)),
                "current_conditions": str(data.get('current_conditions', 'No data')),
                "accumulation": float(data.get('accumulation', 0.0)),
                "forecast": data.get('forecast', []),
                "alerts": data.get('alerts', [])
            }
        except Exception as e:
            print(f"Error transforming weather data: {str(e)}")
            # Return a safe default structure
            return {
                "current_temp": 0.0,
                "current_conditions": "Error",
                "accumulation": 0.0,
                "forecast": [],
                "alerts": [{
                    "level": "error",
                    "message": f"Failed to transform weather data: {str(e)}"
                }]
            }

    def _transform_inventory_data(self, fuel_data: Dict[str, Any], salt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform inventory data into report format."""
        try:
            # Parse JSON strings if needed
            if isinstance(fuel_data, str):
                fuel_data = json.loads(fuel_data)
            if isinstance(salt_data, str):
                salt_data = json.loads(salt_data)

            # Set default values
            fuel_level = 50.0  # Default 50%
            salt_level = 50.0  # Default 50%

            # Get values based on data structure
            if 'data' in fuel_data and 'inventory' in fuel_data['data']:
                # Complex structure
                fuel_level = (fuel_data['data']['inventory'].get('current_level', 0) / 
                            (fuel_data['data']['inventory'].get('threshold', 1) * 5)) * 100
            elif 'fuel_level' in fuel_data:
                # Simple structure
                fuel_level = float(fuel_data['fuel_level'])

            if 'data' in salt_data and 'inventory' in salt_data['data']:
                # Complex structure
                salt_level = (salt_data['data']['inventory'].get('current_level', 0) / 
                            (salt_data['data']['inventory'].get('threshold', 1) * 5)) * 100
            elif 'salt_level' in salt_data:
                # Simple structure
                salt_level = float(salt_data['salt_level'])

            return {
                "salt_level": salt_level,
                "fuel_level": fuel_level,
                "depots": [
                    {
                        "name": "Main Depot",
                        "status": "Operational" if salt_level > 30 and fuel_level > 30 else "Low Stock",
                        "status_color": "success" if salt_level > 30 and fuel_level > 30 else "warning"
                    }
                ]
            }
        except Exception as e:
            print(f"Error transforming inventory data: {str(e)}")
            # Return safe defaults
            return {
                "salt_level": 50.0,
                "fuel_level": 50.0,
                "depots": [
                    {
                        "name": "Main Depot",
                        "status": "Unknown",
                        "status_color": "warning"
                    }
                ]
            }

    def _transform_traffic_data(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform traffic data into report format."""
        try:
            # Parse JSON string if needed
            if isinstance(traffic_data, str):
                traffic_data = json.loads(traffic_data)

            # Set default values
            active_routes = 1
            coverage = 75.0

            # Get values based on data structure
            if 'optimized_route' in traffic_data:
                # Complex structure
                route_data = traffic_data['optimized_route']
                routes = route_data.get('routes', [{}])[0]
                active_routes = len(route_data.get('routes', []))
                
                # Calculate coverage
                total_distance = routes.get('summary', {}).get('lengthInMeters', 0)
                covered_distance = total_distance * 0.8
                coverage = (covered_distance / total_distance * 100) if total_distance > 0 else 75.0
            else:
                # Simple structure
                active_routes = traffic_data.get('active_routes', active_routes)
                coverage = traffic_data.get('coverage', coverage)

            # Build route data structure
            route_data = {
                "active_routes": active_routes,
                "coverage": float(coverage),
                "efficiency_scores": traffic_data.get('efficiency_scores', {
                    f"Route {i+1}": 85.0 - (i * 5)
                    for i in range(active_routes)
                }),
                "priority_zones": traffic_data.get('priority_zones', {
                    "Highway Network": [80.0, "success"],
                    "Emergency Routes": [70.0, "warning"],
                    "Commercial": [60.0, "danger"]
                })
            }

            # Build fleet data structure
            fleet_data = {
                "vehicles": [
                    {
                        "id": f"Truck {i+1}",
                        "status": "Active",
                        "status_color": "success",
                        "region": "Zone 1",
                        "priority": "High"
                    }
                    for i in range(active_routes)
                ]
            }

            result = {
                "route_data": route_data,
                "fleet_data": fleet_data
            }

            # Add map data only if complex structure is present
            if 'optimized_route' in traffic_data:
                result["map_data"] = {
                    "routes": [
                        {
                            "id": route.get('id', f'route-{i}'),
                            "priority": i + 1,
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [[coord[1], coord[0]] for coord in route.get('legs', [{}])[0].get('points', [])]
                            }
                        }
                        for i, route in enumerate(traffic_data['optimized_route'].get('routes', []))
                    ],
                    "incidents": [
                        {
                            "longitude": incident.get('geometry', {}).get('coordinates', [0, 0])[0],
                            "latitude": incident.get('geometry', {}).get('coordinates', [0, 0])[1],
                            "type": incident.get('properties', {}).get('iconCategory', 'Unknown'),
                            "description": incident.get('properties', {}).get('description', 'No description')
                        }
                        for incident in traffic_data.get('incidents', [])
                    ]
                }

            return result
        except Exception as e:
            print(f"Error transforming traffic data: {str(e)}")
            # Return safe defaults
            return {
                "route_data": {
                    "active_routes": 1,
                    "coverage": 75.0,
                    "efficiency_scores": {"Route 1": 85.0},
                    "priority_zones": {
                        "Highway Network": [80.0, "success"],
                        "Emergency Routes": [70.0, "warning"],
                        "Commercial": [60.0, "danger"]
                    }
                },
                "fleet_data": {
                    "vehicles": [{
                        "id": "Truck 1",
                        "status": "Active",
                        "status_color": "success",
                        "region": "Zone 1",
                        "priority": "High"
                    }]
                }
            }

    def _run(self, weather_data: str, fuel_data: str, salt_data: str, traffic_data: str) -> str:
        """
        Transform data from various sources into the report generator format.
        
        Args:
            weather_data: JSON string from WeatherDataTool
            fuel_data: JSON string from LocalInventoryTool (fuel)
            salt_data: JSON string from LocalInventoryTool (salt)
            traffic_data: JSON string from TomTomTrafficTool
            
        Returns:
            JSON string in ReportGeneratorTool format
        """
        try:
            # Transform individual components
            weather_transformed = self._transform_weather_data(weather_data)
            inventory_transformed = self._transform_inventory_data(fuel_data, salt_data)
            traffic_transformed = self._transform_traffic_data(traffic_data)
            
            # Combine all data
            result = {
                "weather_data": weather_transformed,
                "resource_data": inventory_transformed,
                **traffic_transformed,  # Includes route_data, fleet_data, and map_data
                "alerts_data": [
                    *weather_transformed.get('alerts', []),
                    {
                        "level": "warning" if inventory_transformed['salt_level'] < 30 else "info",
                        "message": f"Salt inventory at {inventory_transformed['salt_level']:.1f}%"
                    },
                    {
                        "level": "warning" if inventory_transformed['fuel_level'] < 30 else "info",
                        "message": f"Fuel inventory at {inventory_transformed['fuel_level']:.1f}%"
                    }
                ]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": "Data transformation failed",
                "details": str(e)
            })

def create_tool() -> DataTransformerTool:
    """Factory function to create an instance of the DataTransformerTool."""
    return DataTransformerTool()
