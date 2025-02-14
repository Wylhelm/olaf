from crewai.tools import BaseTool
from typing import Dict, Any, Optional
import json
from datetime import datetime


def safe_parse_json(json_str: Optional[str], nested: bool = False) -> Dict[str, Any]:
    """
    Safely parse a JSON string, with support for nested JSON strings.
    Returns an empty dict if the input is empty or invalid.
    
    Args:
        json_str: The JSON string to parse
        nested: If True, attempts to parse strings within the JSON as JSON objects
    """
    if not json_str or not json_str.strip():
        return {}
    try:
        data = json.loads(json_str)
        if nested:
            # Handle nested JSON strings
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        # Keep original string if it's not valid JSON
                        continue
        return data
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}


class DataTransformerTool(BaseTool):
    """Tool for transforming data from various sources into the report generator format."""
    
    name: str = "Data Transformer"
    description: str = (
        "Transforms data from WeatherDataTool, LocalInventoryTool, and TomTomTrafficTool "
        "into the format required by ReportGeneratorTool."
    )

    def _transform_weather_data(self, weather_data: Any) -> Dict[str, Any]:
        """Transform weather data into report format."""
        try:
            if not weather_data:
                return {
                    "current_temp": 0.0,
                    "current_conditions": "No data",
                    "accumulation": 0.0,
                    "forecast": [],
                    "alerts": [],
                    "weather_chart_data": "{}"
                }
            
            # If weather_data is a string, attempt to parse it.
            if isinstance(weather_data, str):
                try:
                    weather_data = json.loads(weather_data)
                except json.JSONDecodeError:
                    print(f"Invalid weather_data JSON: {weather_data}")
                    return {
                        "current_temp": 0.0,
                        "current_conditions": "Invalid data",
                        "accumulation": 0.0,
                        "forecast": [],
                        "alerts": [{
                            "level": "error",
                            "message": "Invalid weather data format"
                        }],
                        "weather_chart_data": "{}"
                    }
            
            current_weather = weather_data.get('current_weather_conditions', {})
            forecast = current_weather.get('snowfall_predictions', [])
            labels, temp_data, precip_data, snow_data = [], [], [], []
            
            # Build arrays for chart data
            for entry in forecast:
                labels.append(entry.get('date_time', '').split()[1])  # Get time part only
                temp_data.append(float(current_weather.get('temperature', 0)))
                precip_data.append(0)  # No precipitation data provided
                snow_data.append(float(entry.get('snow_amount', 0)))
            
            chart_data = {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Temperature (°C)",
                        "data": temp_data,
                        "borderColor": "#ff6384",
                        "fill": False
                    },
                    {
                        "label": "Precipitation (mm)",
                        "data": precip_data,
                        "borderColor": "#36a2eb",
                        "fill": False
                    },
                    {
                        "label": "Snowfall (cm)",
                        "data": snow_data,
                        "borderColor": "#4bc0c0",
                        "fill": False
                    }
                ]
            }
            
            # Build forecast entries with expected key names
            transformed_forecast = []
            for entry in forecast:
                transformed_forecast.append({
                    "time": entry.get('time', ''),
                    "snowfall": entry.get('predicted_snow', 0),
                    "temp": entry.get('temperature', 0)
                })
            
            return {
                "current_temp": float(current_weather.get('temperature', 0.0)),
                "current_conditions": str(current_weather.get('snow_alert', 'No data')),
                "accumulation": float(current_weather.get('current_snow_amount', 0.0)),
                "forecast": [{
                    "time": entry.get('date_time', '').split()[1],
                    "snowfall": float(entry.get('snow_amount', 0)),
                    "temp": float(current_weather.get('temperature', 0.0))
                } for entry in forecast],
                "alerts": [{
                    "level": alert.get('level', '').lower(),
                    "message": alert.get('message', '')
                } for alert in weather_data.get('alerts', [])],
                "weather_chart_data": json.dumps(chart_data, separators=(',', ': '), ensure_ascii=False)
            }
        except Exception as e:
            print(f"Error transforming weather data: {e}")
            return {
                "current_temp": 0.0,
                "current_conditions": "Error",
                "accumulation": 0.0,
                "forecast": [],
                "alerts": [{
                    "level": "error",
                    "message": f"Failed to transform weather data: {e}"
                }],
                "weather_chart_data": "{}"
            }
    
    def _transform_inventory_data(self, fuel_data: Any, salt_data: Any) -> Dict[str, Any]:
        """Transform inventory data into report format."""
        try:
            if not fuel_data or not salt_data:
                return {
                    "salt_level": 50.0,
                    "fuel_level": 50.0,
                    "depots": [{
                        "name": "Main Depot",
                        "status": "Unknown",
                        "status_color": "warning"
                    }]
                }
            
            # Parse JSON strings if needed
            if isinstance(fuel_data, str):
                try:
                    fuel_data = json.loads(fuel_data)
                except json.JSONDecodeError:
                    print(f"Invalid fuel_data JSON: {fuel_data}")
                    fuel_data = {"fuel_level": 50.0}
            if isinstance(salt_data, str):
                try:
                    salt_data = json.loads(salt_data)
                except json.JSONDecodeError:
                    print(f"Invalid salt_data JSON: {salt_data}")
                    salt_data = {"salt_level": 50.0}
            
            fuel_level = float(fuel_data.get('fuel_level', 0))
            salt_level = float(salt_data.get('salt_level', 0))
            
            return {
                "salt_level": salt_level,
                "fuel_level": fuel_level,
                "depots": [{
                    "name": "Main Depot",
                    "status": "Operational" if salt_level > 30 and fuel_level > 30 else "Low Stock",
                    "status_color": "success" if salt_level > 30 and fuel_level > 30 else "warning"
                }]
            }
        except Exception as e:
            print(f"Error transforming inventory data: {e}")
            return {
                "salt_level": 50.0,
                "fuel_level": 50.0,
                "depots": [{
                    "name": "Main Depot",
                    "status": "Unknown",
                    "status_color": "warning"
                }]
            }
    
    def _transform_traffic_data(self, traffic_data: Any) -> Dict[str, Any]:
        """Transform traffic data into report format."""
        try:
            if not traffic_data:
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
            
            if isinstance(traffic_data, str):
                try:
                    traffic_data = json.loads(traffic_data)
                except json.JSONDecodeError:
                    print(f"Invalid traffic_data JSON: {traffic_data}")
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
            
            fleet_data = traffic_data.get('fleet_data', {})
            vehicles = fleet_data.get('vehicles', [])
            active_routes = traffic_data.get('active_routes', 0)
            coverage = float(traffic_data.get('coverage', 0))
            
            route_data = {
                "active_routes": active_routes,
                "coverage": float(coverage),
                "efficiency_scores": traffic_data.get('efficiency_scores', {
                    f"Route {i+1}": 85.0 - (i * 5)
                    for i in range(active_routes if active_routes > 0 else 1)
                }),
                "priority_zones": traffic_data.get('priority_zones', {
                    "Highway Network": [80.0, "success"],
                    "Emergency Routes": [70.0, "warning"],
                    "Commercial": [60.0, "danger"]
                })
            }
            
            fleet_data = {
                "vehicles": [{
                    "id": vehicle.get('id', ''),
                    "status": vehicle.get('status', ''),
                    "status_color": vehicle.get('status_color', '').lower(),
                    "region": vehicle.get('region', ''),
                    "priority": vehicle.get('priority', '')
                } for vehicle in vehicles]
            }
            
            result = {
                "route_data": route_data,
                "fleet_data": fleet_data
            }
            
            # Add map data if available
            if 'optimized_route' in traffic_data:
                optimized_routes = traffic_data['optimized_route'].get('routes', [])
                result["map_data"] = {
                    "routes": [
                        {
                            "id": route.get('id', f'route-{i}'),
                            "priority": i + 1,
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [coord[1], coord[0]] for coord in route.get('legs', [{}])[0].get('points', [])
                                ]
                            }
                        }
                        for i, route in enumerate(optimized_routes)
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
            print(f"Error transforming traffic data: {e}")
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
    
    def _run(
        self,
        weather_data: str = None,
        fuel_data: str = None,
        salt_data: str = None,
        traffic_data: str = None
    ) -> str:
        """
        Transform data from various sources into the report generator format.
        
        Args:
            weather_data: JSON string from WeatherDataTool
            fuel_data: JSON string from LocalInventoryTool (fuel)
            salt_data: JSON string from LocalInventoryTool (salt)
            traffic_data: JSON string from TomTomTrafficTool
            
        Returns:
            JSON string in ReportGeneratorTool format.
        """
        # Safely parse input data with nested JSON support
        weather_parsed = safe_parse_json(weather_data, nested=True)
        fuel_parsed = safe_parse_json(fuel_data, nested=True)
        salt_parsed = safe_parse_json(salt_data, nested=True)
        traffic_parsed = safe_parse_json(traffic_data, nested=True)
        
        weather_transformed = self._transform_weather_data(weather_parsed)
        inventory_transformed = self._transform_inventory_data(fuel_parsed, salt_parsed)
        traffic_transformed = self._transform_traffic_data(traffic_parsed)
        
        combined_result = {
            "weather_data": weather_transformed,
            "resource_data": inventory_transformed,
            **traffic_transformed,  # Unpack route_data, fleet_data, (and map_data if available)
            "alerts_data": [
                *weather_transformed.get('alerts', []),
                {
                    "level": "warning" if inventory_transformed["salt_level"] < 30 else "info",
                    "message": f"Salt inventory at {inventory_transformed['salt_level']:.1f}%"
                },
                {
                    "level": "warning" if inventory_transformed["fuel_level"] < 30 else "info",
                    "message": f"Fuel inventory at {inventory_transformed['fuel_level']:.1f}%"
                }
            ],
            "weather_chart_data": weather_transformed.get('weather_chart_data', '{}')
        }
        
        return json.dumps(combined_result, indent=2, separators=(',', ': '), ensure_ascii=False, default=str)


def create_tool() -> DataTransformerTool:
    """Factory function to create an instance of the DataTransformerTool."""
    return DataTransformerTool()
