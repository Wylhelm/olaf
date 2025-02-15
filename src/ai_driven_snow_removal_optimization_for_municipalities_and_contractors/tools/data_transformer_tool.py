from crewai.tools import BaseTool
from typing import Dict, Any, Optional, Union
import json
from datetime import datetime, timedelta
from ..models.data_models import (
    WeatherData, ResourceData, RouteData, FleetData,
    WeatherAlert, WeatherForecastEntry, DepotStatus,
    VehicleStatus, MapData, MapRoute, MapIncident,
    OperationalData
)


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

    def _transform_weather_data(self, weather_data: Any) -> WeatherData:
        """Transform weather data into validated report format."""
        try:
            if not weather_data:
                return WeatherData(
                    current_temp=0.0,
                    current_conditions="No data",
                    accumulation=0.0,
                    forecast=[],
                    alerts=[]
                )
            
            # Standardize weather data format
            def standardize_weather_data(data):
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        print("Error parsing weather data JSON")
                        return {}

                # Handle different possible data structures
                current_conditions = {}
                if 'currentConditions' in data:
                    current_conditions = data['currentConditions']
                elif 'current_conditions' in data:
                    current_conditions = {
                        'temperature': data.get('current_temp', 0.0),
                        'description': data['current_conditions'],
                        'accumulation': data.get('accumulation', 0.0)
                    }

                # Standardize forecast entries
                forecast = []
                raw_forecast = data.get('forecast', [])
                for entry in raw_forecast:
                    time = entry.get('time', '')
                    # If time is not in ISO format, convert it
                    if not ('T' in time and time.endswith('Z')):
                        # Use current date with the time, or default to now
                        now = datetime.now()
                        if time.lower() == 'later':
                            # Add 3 hours for 'later' entries
                            time = (now + timedelta(hours=3)).isoformat()
                        else:
                            # Try to parse time or use current time
                            try:
                                time = f"{now.date()}T{time}Z"
                            except:
                                time = now.isoformat()
                    
                    forecast.append({
                        'time': time,
                        'temp': float(entry.get('temp', 0)),
                        'snowfall': float(entry.get('snowfall', 0))
                    })

                # Standardize alerts
                alerts = []
                for alert in data.get('alerts', []):
                    if isinstance(alert, dict):
                        level = alert.get('level', '').lower()
                        if level not in ['info', 'warning', 'danger']:
                            level = 'warning'  # Default to warning
                        alerts.append({
                            'level': level,
                            'message': alert.get('message', 'No message')
                        })

                return {
                    'currentConditions': current_conditions,
                    'forecast': forecast,
                    'alerts': alerts
                }

            # Standardize the weather data
            standardized_data = standardize_weather_data(weather_data)
            current_conditions = standardized_data['currentConditions']
            forecast = standardized_data['forecast']
            alerts = standardized_data['alerts']

            # Build arrays for chart data
            labels = []
            temp_data = []
            precip_data = []
            snow_data = []
            
            for entry in forecast:
                time = entry['time']
                # Extract time part from ISO format
                time_part = time.split('T')[1].split('Z')[0] if 'T' in time else time
                labels.append(time_part)
                temp_data.append(entry['temp'])
                precip_data.append(0)  # No precipitation data provided
                snow_data.append(entry['snowfall'])
            
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
            
            # Create validated WeatherData object
            validated_weather = WeatherData(
                current_temp=float(current_conditions.get('temperature', 0.0)),
                current_conditions=str(current_conditions.get('description', 'No data')),
                accumulation=float(current_conditions.get('accumulation', 0.0)),
                forecast=[
                    WeatherForecastEntry(
                        time=entry.get('time', datetime.now().isoformat()),
                        snowfall=float(entry.get('snowfall', 0)),
                        temp=float(entry.get('temp', 0))
                    ) for entry in forecast
                ],
                alerts=[
                    WeatherAlert(
                        level=alert.get('level', 'info').lower(),
                        message=alert.get('message', 'No message')
                    ) for alert in weather_data.get('alerts', [])
                ]
            )
            return validated_weather
        except Exception as e:
            print(f"Error transforming weather data: {e}")
            print(f"Error transforming weather data: {e}")
            return WeatherData(
                current_temp=0.0,
                current_conditions="Error",
                accumulation=0.0,
                forecast=[],
                alerts=[
                    WeatherAlert(
                        level="warning",
                        message=f"Failed to transform weather data: {e}"
                    )
                ]
            )
    
    def _transform_inventory_data(self, fuel_data: Any, salt_data: Any) -> ResourceData:
        """Transform inventory data into validated report format."""
        try:
            if not fuel_data or not salt_data:
                return ResourceData(
                    salt_level=50.0,
                    fuel_level=50.0,
                    depots=[
                        DepotStatus(
                            name="Main Depot",
                            status="Unknown",
                            status_color="warning"
                        )
                    ]
                )
            
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
            
            return ResourceData(
                salt_level=salt_level,
                fuel_level=fuel_level,
                depots=[
                    DepotStatus(
                        name="Main Depot",
                        status="Operational" if salt_level > 30 and fuel_level > 30 else "Low Stock",
                        status_color="success" if salt_level > 30 and fuel_level > 30 else "warning"
                    )
                ]
            )
        except Exception as e:
            print(f"Error transforming inventory data: {e}")
            return ResourceData(
                salt_level=50.0,
                fuel_level=50.0,
                depots=[
                    DepotStatus(
                        name="Main Depot",
                        status="Unknown",
                        status_color="warning"
                    )
                ]
            )
    
    def _transform_traffic_data(self, traffic_data: Any) -> Dict[str, Union[RouteData, FleetData, MapData]]:
        """Transform traffic data into validated report format."""
        try:
            if not traffic_data:
                # Create default validated objects
                route_data = RouteData(
                    active_routes=1,
                    coverage=75.0,
                    efficiency_scores={"Route 1": 85.0},
                    priority_zones={
                        "Highway Network": [80.0, "success"],
                        "Emergency Routes": [70.0, "warning"],
                        "Commercial": [60.0, "danger"]
                    }
                )
                
                fleet_data = FleetData(
                    vehicles=[
                        VehicleStatus(
                            id="Truck 1",
                            status="Active",
                            status_color="success",
                            region="Zone 1",
                            priority="High"
                        )
                    ]
                )
                
                map_data = MapData(
                    routes=[],
                    incidents=[]
                )
                
                return {
                    "route_data": route_data,
                    "fleet_data": fleet_data,
                    "map_data": map_data
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
            
            # Standardize traffic data format
            def standardize_traffic_data(data):
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        print("Error parsing traffic data JSON")
                        return {}

                # Handle different possible data structures
                if 'routeOptimizationPlan' in data:
                    # New format
                    traffic_impact = data.get('routeOptimizationPlan', {}).get('trafficImpactAnalysis', {})
                    current_traffic = traffic_impact.get('currentTrafficFlow', {})
                    optimized_routes = data.get('routeOptimizationPlan', {}).get('optimizedRoutes', [])
                elif 'currentTrafficFlow' in data:
                    # Old format
                    current_traffic = data.get('currentTrafficFlow', {})
                    optimized_routes = data.get('optimized_route', {}).get('routes', [])
                else:
                    current_traffic = {}
                    optimized_routes = []

                return {
                    'currentTrafficFlow': current_traffic,
                    'optimizedRoutes': optimized_routes
                }

            # Standardize the traffic data
            standardized_data = standardize_traffic_data(traffic_data)
            current_traffic = standardized_data['currentTrafficFlow']
            incidents_list = current_traffic.get('incidents', [])
            road_closures = current_traffic.get('roadClosures', [])
            
            # Extract route points from optimized routes
            route_points = []
            for route in standardized_data['optimizedRoutes']:
                if isinstance(route, dict):
                    # Handle different route formats
                    if 'route' in route:
                        # New format with direct route array
                        points = route['route']
                        route_points.extend([
                            [point['longitude'], point['latitude']]
                            for point in points
                            if 'longitude' in point and 'latitude' in point
                        ])
                    elif 'legs' in route:
                        # Old format with legs array
                        points = route.get('legs', [{}])[0].get('points', [])
                        route_points.extend([
                            [point.get('longitude'), point.get('latitude')]
                            for point in points
                            if point.get('longitude') and point.get('latitude')
                        ])

            # If no route points found, don't create a route
            if not route_points:
                route_points = []

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
            
            # Process incidents and road closures for map display
            map_incidents = []
            
            # Helper function to process coordinates string
            def parse_coordinates(coord_str):
                try:
                    if not isinstance(coord_str, str):
                        print(f"Invalid coordinate format, expected string but got {type(coord_str)}")
                        return None, None
                        
                    # Try different coordinate formats
                    if ", " in coord_str:
                        lat, lon = coord_str.split(", ")
                    elif "," in coord_str:
                        lat, lon = coord_str.split(",")
                    else:
                        print(f"Invalid coordinate format: {coord_str}")
                        return None, None
                        
                    # Clean and convert coordinates
                    lat = float(lat.strip())
                    lon = float(lon.strip())
                    
                    # Validate coordinate ranges
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        print(f"Coordinates out of range: lat={lat}, lon={lon}")
                        return None, None
                        
                    return lat, lon
                except (ValueError, AttributeError) as e:
                    print(f"Error parsing coordinates {coord_str}: {e}")
                    return None, None

            # Process incidents from either Route Optimization Plan or direct traffic data
            if isinstance(traffic_data, dict):
                # Try Route Optimization Plan format first
                if isinstance(traffic_data, dict):
                    if 'Route Optimization Plan' in traffic_data:
                        route_plan = traffic_data['Route Optimization Plan']
                        traffic_integration = route_plan.get('Traffic Integration', {})
                        current_flow = traffic_integration.get('Current Traffic Flow', {})
                        print("Found Route Optimization Plan data:", json.dumps(current_flow, indent=2))
                    elif 'currentTrafficFlow' in traffic_data:
                        current_flow = traffic_data['currentTrafficFlow']
                        print("Using direct traffic flow data:", json.dumps(current_flow, indent=2))
                    else:
                        # Try to find traffic data in any nested structure
                        for key, value in traffic_data.items():
                            if isinstance(value, dict) and ('Current Traffic Flow' in value or 'currentTrafficFlow' in value):
                                current_flow = value.get('Current Traffic Flow', value.get('currentTrafficFlow', {}))
                                print(f"Found traffic data in {key}:", json.dumps(current_flow, indent=2))
                                break
                        else:
                            print("No valid traffic flow data found in:", json.dumps(traffic_data, indent=2))
                            current_flow = {}
                else:
                    print("Traffic data is not a dictionary:", type(traffic_data))
                    current_flow = {}
                
                # Print debug info
                print("Traffic data structure:", json.dumps(traffic_data, indent=2))
                print("Current flow:", json.dumps(current_flow, indent=2))
                
                # If no data found, try direct traffic data format
                if not current_flow:
                    current_flow = traffic_data.get('currentTrafficFlow', {})
                
                # Process incidents from either format
                incidents = current_flow.get('incidents', [])
                if not incidents:
                    incidents = current_flow.get('Incidents', [])  # Try capitalized key
                print("Processing incidents:", json.dumps(incidents, indent=2))
                for incident in incidents:
                    try:
                        incident_parts = incident.split(" at ")
                        if len(incident_parts) == 2:
                            incident_type = incident_parts[0].lower()
                            lat, lon = parse_coordinates(incident_parts[1])
                            if lat is not None and lon is not None:
                                type_code = 1  # Default to accident
                                if "road works" in incident_type:
                                    type_code = 8
                                elif "road closed" in incident_type:
                                    type_code = 6
                                elif "traffic jam" in incident_type:
                                    type_code = 9
                                
                                map_incidents.append({
                                    "type": type_code,
                                    "description": incident_parts[0],
                                    "latitude": lat,
                                    "longitude": lon
                                })
                    except Exception as e:
                        print(f"Error processing incident: {e}")
                        continue
                
                # Process road closures from either format
                road_closures = current_flow.get('roadClosures', [])
                if not road_closures:
                    road_closures = current_flow.get('Road Closures', [])  # Try capitalized key
                print("Processing road closures:", json.dumps(road_closures, indent=2))
                for closure in road_closures:
                    try:
                        closure_parts = closure.split(" at ")
                        if len(closure_parts) == 2:
                            lat, lon = parse_coordinates(closure_parts[1])
                            if lat is not None and lon is not None:
                                map_incidents.append({
                                    "type": 6,  # Road closure type
                                    "description": "Road Closed",
                                    "latitude": lat,
                                    "longitude": lon
                                })
                    except Exception as e:
                        print(f"Error processing road closure: {e}")
                        continue

            # Process routes from TomTom response
            routes = []
            if isinstance(traffic_data, dict):
                # Try to get route data from different possible structures
                if 'routes' in traffic_data:
                    routes = traffic_data['routes']
                elif 'currentTrafficFlow' in traffic_data:
                    routes = traffic_data.get('routes', [])
                
                # If no routes found in expected locations, search deeper
                if not routes:
                    for key, value in traffic_data.items():
                        if isinstance(value, dict) and 'routes' in value:
                            routes = value['routes']
                            break

            # Process each route and validate its GeoJSON structure
            validated_routes = []
            for route in routes:
                if isinstance(route, dict):
                    # Extract route geometry
                    geometry = route.get('geometry', {})
                    if isinstance(geometry, dict):
                        # Validate coordinates exist and are valid
                        if geometry.get('type') == 'Feature':
                            geom = geometry.get('geometry', {})
                        else:
                            geom = geometry
                        
                        if (geom.get('type') == 'LineString' and 
                            isinstance(geom.get('coordinates', []), list) and 
                            len(geom.get('coordinates', [])) > 1):
                            
                            # Validate each coordinate
                            valid_coords = all(
                                isinstance(coord, list) and 
                                len(coord) == 2 and 
                                -180 <= coord[0] <= 180 and 
                                -90 <= coord[1] <= 90
                                for coord in geom['coordinates']
                            )
                            
                            if valid_coords:
                                if geometry.get('type') == 'Feature':
                                    validated_routes.append(route)
                                else:
                                    validated_routes.append({
                                        'id': route.get('id', 'route1'),
                                        'priority': route.get('priority', 1),
                                        'geometry': {
                                            'type': 'Feature',
                                            'geometry': geometry
                                        }
                                    })

            # Create validated objects
            validated_route_data = RouteData(
                active_routes=active_routes,
                coverage=float(coverage),
                efficiency_scores={
                    f"Route {i+1}": min(85.0 - (i * 5), 100)
                    for i in range(active_routes)
                },
                priority_zones={
                    "Highway Network": [80.0, "success"],
                    "Emergency Routes": [70.0, "warning"],
                    "Commercial": [60.0, "danger"]
                }
            )
            
            validated_fleet_data = FleetData(
                vehicles=[
                    VehicleStatus(
                        id=f"Truck {i+1}",
                        status="Active",
                        status_color="success",
                        region=f"Zone {i+1}",
                        priority="High" if i < len(incidents_list) else "Medium"
                    )
                    for i in range(active_routes)
                ]
            )
            
            validated_map_data = MapData(
                routes=[
                    MapRoute(
                        id=route.get('id', f'route{i+1}'),
                        priority=route.get('priority', i+1),
                        geometry=route['geometry']
                    )
                    for i, route in enumerate(validated_routes)
                ],
                incidents=[
                    MapIncident(
                        type=incident.get('type', 1),
                        description=incident.get('description', 'No description'),
                        longitude=incident.get('longitude', -71.2080),
                        latitude=incident.get('latitude', 46.8139)
                    )
                    for incident in map_incidents
                ]
            )
            
            return {
                "route_data": validated_route_data,
                "fleet_data": validated_fleet_data,
                "map_data": validated_map_data
            }
        except Exception as e:
            print(f"Error transforming traffic data: {e}")
            # Return default validated objects on error
            return {
                "route_data": RouteData(
                    active_routes=1,
                    coverage=75.0,
                    efficiency_scores={"Route 1": 85.0},
                    priority_zones={
                        "Highway Network": [80.0, "success"],
                        "Emergency Routes": [70.0, "warning"],
                        "Commercial": [60.0, "danger"]
                    }
                ),
                "fleet_data": FleetData(
                    vehicles=[
                        VehicleStatus(
                            id="Truck 1",
                            status="Active",
                            status_color="success",
                            region="Zone 1",
                            priority="High"
                        )
                    ]
                ),
                "map_data": MapData(
                    routes=[],
                    incidents=[]
                )
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
        
        try:
            # Create and validate complete operational data
            operational_data = OperationalData(
                weather_data=weather_transformed,
                resource_data=inventory_transformed,
                route_data=traffic_transformed["route_data"],
                fleet_data=traffic_transformed["fleet_data"],
                map_data=traffic_transformed["map_data"]
            )

            # Convert to dict and add weather chart data
            result_dict = operational_data.dict()
            
            # Create weather chart data from forecast
            weather_data = weather_transformed
            forecast = weather_data.forecast
            
            chart_data = {
                "labels": [entry.time.split('T')[1].split('-')[0] if 'T' in entry.time else entry.time for entry in forecast],
                "datasets": [
                    {
                        "label": "Temperature (°C)",
                        "data": [entry.temp for entry in forecast],
                        "borderColor": "#ff6384",
                        "fill": False
                    },
                    {
                        "label": "Snowfall (cm)",
                        "data": [entry.snowfall for entry in forecast],
                        "borderColor": "#4bc0c0",
                        "fill": False
                    }
                ]
            }
            
            result_dict["weather_chart_data"] = json.dumps(chart_data, separators=(',', ': '), ensure_ascii=False)
            
            return json.dumps(result_dict, indent=2, separators=(',', ': '), ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error creating operational data: {e}")
            # Create fallback operational data with default values
            fallback_data = OperationalData(
                weather_data=WeatherData(
                    current_temp=0.0,
                    current_conditions="Error",
                    accumulation=0.0,
                    forecast=[],
                    alerts=[WeatherAlert(level="warning", message=f"Data validation error: {e}")]
                ),
                resource_data=ResourceData(
                    salt_level=50.0,
                    fuel_level=50.0,
                    depots=[DepotStatus(name="Main Depot", status="Unknown", status_color="warning")]
                ),
                route_data=RouteData(
                    active_routes=1,
                    coverage=75.0,
                    efficiency_scores={"Route 1": 85.0},
                    priority_zones={
                        "Highway Network": [80.0, "success"],
                        "Emergency Routes": [70.0, "warning"],
                        "Commercial": [60.0, "danger"]
                    }
                ),
                fleet_data=FleetData(
                    vehicles=[
                        VehicleStatus(
                            id="Truck 1",
                            status="Active",
                            status_color="success",
                            region="Zone 1",
                            priority="High"
                        )
                    ]
                ),
                map_data=MapData(routes=[], incidents=[])
            )
            
            result_dict = fallback_data.dict()
            # Create empty chart data for fallback
            result_dict["weather_chart_data"] = json.dumps({
                "labels": [],
                "datasets": [
                    {
                        "label": "Temperature (°C)",
                        "data": [],
                        "borderColor": "#ff6384",
                        "fill": False
                    },
                    {
                        "label": "Snowfall (cm)",
                        "data": [],
                        "borderColor": "#4bc0c0",
                        "fill": False
                    }
                ]
            }, separators=(',', ': '), ensure_ascii=False)
            
            return json.dumps(result_dict, indent=2, separators=(',', ': '), ensure_ascii=False, default=str)


def create_tool() -> DataTransformerTool:
    """Factory function to create an instance of the DataTransformerTool."""
    return DataTransformerTool()
