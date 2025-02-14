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
            
            current_conditions = weather_data.get('currentConditions', {})
            forecast = weather_data.get('forecast', [])
            labels, temp_data, precip_data, snow_data = [], [], [], []
            
            # Build arrays for chart data
            for entry in forecast:
                time = entry.get('time', '')
                # Extract time part from ISO format
                time_part = time.split('T')[1].split('-')[0] if 'T' in time else time
                labels.append(time_part)
                temp_data.append(float(entry.get('temp', 0)))
                precip_data.append(0)  # No precipitation data provided
                snow_data.append(float(entry.get('snowfall', 0)))
            
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
            
            return {
                "current_temp": float(current_conditions.get('temperature', 0.0)),
                "current_conditions": str(current_conditions.get('description', 'No data')),
                "accumulation": float(current_conditions.get('accumulation', 0.0)),
                "forecast": [{
                    "time": entry.get('time', '').split('T')[1].split('-')[0] if 'T' in entry.get('time', '') else entry.get('time', ''),
                    "snowfall": float(entry.get('snowfall', 0)),
                    "temp": float(entry.get('temp', 0))
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
            
            total_fuel = float(fuel_data.get('diesel', 0)) + float(fuel_data.get('gasoline', 0))
            total_salt = float(salt_data.get('rockSalt', 0)) + float(salt_data.get('treatedSalt', 0))
            
            # Calculate percentages (assuming max capacity is double the current amount)
            fuel_level = min((total_fuel / (total_fuel * 2)) * 100, 100) if total_fuel > 0 else 0
            salt_level = min((total_salt / (total_salt * 2)) * 100, 100) if total_salt > 0 else 0
            
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
                    },
                    "map_data": {
                        "routes": [{
                            "id": "route1",
                            "priority": 1,
                            "geometry": {
                                "type": "Feature",
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": [
                                        [-71.2080, 46.8139],
                                        [-71.2329, 46.8483],
                                        [-71.2757, 46.7737],
                                        [-71.1534, 46.8063]
                                    ]
                                }
                            }
                        }],
                        "incidents": []
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
            
            # Parse traffic data if it's a string
            if isinstance(traffic_data, str):
                traffic_data = json.loads(traffic_data)

            current_traffic = traffic_data.get('currentTrafficFlow', {})
            incidents_list = current_traffic.get('incidents', [])
            road_closures = current_traffic.get('roadClosures', [])
            
            # Extract route data from traffic response
            route_data = current_traffic.get('optimized_route', {})
            route_points = []
            if route_data and 'routes' in route_data and route_data['routes']:
                points = route_data['routes'][0].get('legs', [{}])[0].get('points', [])
                route_points = [[point.get('longitude'), point.get('latitude')] for point in points if point.get('longitude') and point.get('latitude')]

            # If no route points found, use default Quebec route
            if not route_points:
                route_points = [
                    [-71.2080, 46.8139],
                    [-71.2329, 46.8483],
                    [-71.2757, 46.7737],
                    [-71.1534, 46.8063]
                ]

            # Calculate active routes based on incidents and closures
            active_routes = max(1, len(incidents_list) + len(road_closures))
            
            # Calculate coverage based on traffic speed
            speed = float(current_traffic.get('speed', 0))
            coverage = min(100, max(0, (speed / 50) * 100))  # Assuming 50 km/h is optimal
            
            # Generate route data
            route_data = {
                "active_routes": active_routes,
                "coverage": float(coverage),
                "efficiency_scores": {
                    f"Route {i+1}": 85.0 - (i * 5)
                    for i in range(active_routes)
                },
                "priority_zones": {
                    "Highway Network": [80.0, "success"],
                    "Emergency Routes": [70.0, "warning"],
                    "Commercial": [60.0, "danger"]
                }
            }
            
            # Generate fleet data based on incidents and closures
            fleet_data = {
                "vehicles": [
                    {
                        "id": f"Truck {i+1}",
                        "status": "Active",
                        "status_color": "success",
                        "region": f"Zone {i+1}",
                        "priority": "High" if i < len(incidents_list) else "Medium"
                    }
                    for i in range(active_routes)
                ]
            }
            
            # Process incidents for map display
            map_incidents = []
            for incident in incidents_list:
                if isinstance(incident, str):
                    # Try to extract coordinates from string format
                    try:
                        coords = incident.split("at ")[1].split(", ")
                        map_incidents.append({
                            "type": 1,  # Default to accident type
                            "description": incident,
                            "longitude": float(coords[1]),
                            "latitude": float(coords[0])
                        })
                    except (IndexError, ValueError):
                        continue
                elif isinstance(incident, dict) and 'geometry' in incident:
                    coords = incident['geometry'].get('coordinates', [])
                    if len(coords) >= 2:
                        map_incidents.append({
                            "type": incident.get('properties', {}).get('iconCategory', 1),
                            "description": incident.get('properties', {}).get('description', 'No description'),
                            "longitude": coords[0],
                            "latitude": coords[1]
                        })

            result = {
                "route_data": route_data,
                "fleet_data": fleet_data,
                "map_data": {
                    "routes": [{
                        "id": "route1",
                        "priority": 1,
                        "geometry": {
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": route_points
                            }
                        }
                    }],
                    "incidents": map_incidents
                }
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
            "map_data": traffic_transformed.get('map_data', {
                "routes": [],
                "incidents": []
            }),
            "weather_chart_data": weather_transformed.get('weather_chart_data', '{}')
        }
        
        return json.dumps(combined_result, indent=2, separators=(',', ': '), ensure_ascii=False, default=str)


def create_tool() -> DataTransformerTool:
    """Factory function to create an instance of the DataTransformerTool."""
    return DataTransformerTool()
