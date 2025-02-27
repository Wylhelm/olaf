from crewai.tools import BaseTool
from typing import Type, List, Optional, Dict
from pydantic import BaseModel, Field
import requests
import os
from datetime import datetime, timedelta
import json

class TomTomTrafficToolInput(BaseModel):
    """Input schema for TomTomTrafficTool."""
    region: str = Field(..., description="Region to get traffic data for")
    route_type: str = Field(default="fastest", description="Type of route optimization (fastest/shortest)")

class TomTomTrafficTool(BaseTool):
    name: str = "TomTom Traffic Data Tool"
    description: str = """
    Retrieves real-time traffic data and optimizes routes using TomTom API.
    Provides traffic flow information, incidents, and optimal routing for snow removal operations.
    """
    args_schema: Type[BaseModel] = TomTomTrafficToolInput
    api_key: Optional[str] = None
    base_url: str = "https://api.tomtom.com"
    
    # Region to coordinates mapping with major road intersections
    # Coordinates in [longitude, latitude] format for GeoJSON compatibility
    region_coordinates: Dict[str, List[List[float]]] = {
        "Quebec": [
            [-71.2080, 46.8139],  # Old Quebec
            [-71.2329, 46.8483],  # Saint-Roch
            [-71.2477, 46.8270],  # Saint-Jean-Baptiste
            [-71.2205, 46.8131],  # Parliament Hill
            [-71.2312, 46.8163],  # Grande Allée
            [-71.2356, 46.8082],  # Plains of Abraham
            [-71.2434, 46.8137],  # Avenue Cartier
            [-71.2757, 46.7737],  # Sainte-Foy
            [-71.1534, 46.8063],  # Beauport
            [-71.2281, 46.8225],  # Saint-Jean Street
            [-71.2179, 46.8156],  # Rue Saint-Louis
            [-71.2073, 46.8147],  # Dufferin Terrace
            [-71.2197, 46.8119]   # Côte de la Montagne
        ]
    }
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('TOMTOM_API_KEY')
        if not self.api_key:
            raise ValueError("TOMTOM_API_KEY environment variable is required")

    def _get_traffic_incidents(self, bbox: str) -> dict:
        """Get traffic incidents in the specified bounding box."""
        endpoint = f"{self.base_url}/traffic/services/5/incidentDetails"
        params = {
            'key': self.api_key,
            'bbox': bbox,
            'fields': "{incidents{geometry{type,coordinates},properties{iconCategory,startTime,endTime,length,delay,roadNumbers}}}",
            'language': 'en-GB',
            'timeValidityFilter': 'present',
            'categoryFilter': 'RoadClosed,RoadWorks,Accident',  # Removed 'Jam' to focus on important incidents
            'maxResults': 25  # Limit the number of incidents
        }

        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def _calculate_route(self, coordinates: List[List[float]], route_type: str) -> dict:
        """Calculate optimal route between given coordinates."""
        try:
            print(f"DEBUG: Calculating route with coordinates={coordinates}")
            # TomTom expects coordinates in latitude,longitude format
            waypoints = [f"{coord[1]:.6f},{coord[0]:.6f}" for coord in coordinates]  # Convert to lat,lon for TomTom API
            locations = ':'.join(waypoints)
            print(f"DEBUG: Formatted locations={locations}")
            
            endpoint = f"{self.base_url}/routing/1/calculateRoute/{locations}/json"
            params = {
                'key': self.api_key,
                'routeType': route_type,
                'traffic': 'true',
                'travelMode': 'truck'  # Appropriate for snow removal vehicles
            }
            print(f"DEBUG: Route request params={params}")
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"DEBUG: Route response={json.dumps(data, indent=2)}")
            return data
        except Exception as e:
            print(f"DEBUG: Error in _calculate_route: {str(e)}")
            return {"routes": []}
    
    def _get_traffic_flow(self, lon: float, lat: float) -> dict:
        """Get traffic flow data for a specific point."""
        try:
            print(f"DEBUG: Getting traffic flow for lon={lon}, lat={lat}")
            point = f"{lat:.6f},{lon:.6f}"
            print(f"DEBUG: Formatted point={point}")
            
            endpoint = f"{self.base_url}/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                'key': self.api_key,
                'point': point,
                'unit': 'KMPH'
            }
            print(f"DEBUG: Request params={params}")
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"DEBUG: Traffic flow response={json.dumps(data, indent=2)}")
            
            speed = 0
            if 'flowSegmentData' in data:
                flow_data = data['flowSegmentData']
                if isinstance(flow_data, dict) and 'currentSpeed' in flow_data:
                    try:
                        speed = float(flow_data['currentSpeed'])
                    except (ValueError, TypeError):
                        print(f"DEBUG: Could not convert speed to float: {flow_data['currentSpeed']}")
                        speed = 0
            
            return {"flowSegmentData": {"currentSpeed": speed}}
            
        except Exception as e:
            print(f"DEBUG: Error in _get_traffic_flow: {str(e)}")
            raise

    def _run(self, region: str, route_type: str = "fastest") -> str:
        """Main execution method for the tool."""
        try:
            print(f"DEBUG: Starting _run with region={region}, route_type={route_type}")
            coordinates = self.region_coordinates.get(region)
            if not coordinates:
                return json.dumps({
                    "error": "Invalid region",
                    "details": f"Region '{region}' not found. Available regions: {list(self.region_coordinates.keys())}"
                })

            # Calculate bounding box with smaller padding for better focus
            lats = [float(coord[1]) for coord in coordinates]
            lons = [float(coord[0]) for coord in coordinates]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            print(f"DEBUG: Calculated center point: lon={center_lon}, lat={center_lat}")
            
            # Add padding of roughly 500m
            padding = 0.005  # approximately 500m in decimal degrees
            min_lon = max(min(lons) - padding, -180)
            max_lon = min(max(lons) + padding, 180)
            min_lat = max(min(lats) - padding, -90)
            max_lat = min(max(lats) + padding, 90)
            bbox = f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"

            # Get traffic incidents first
            incidents = self._get_traffic_incidents(bbox)
            print(f"DEBUG: Got traffic incidents response")
            
            # Get traffic flow data for the region center point
            flow = self._get_traffic_flow(center_lon, center_lat)
            print(f"DEBUG: Traffic flow result={json.dumps(flow, indent=2)}")

            # Calculate route using the region's coordinates
            route = self._calculate_route(coordinates, route_type)
            print(f"DEBUG: Got route response")

            # Format result with proper GeoJSON
            result = {
                "currentTrafficFlow": {
                    "speed": flow.get('flowSegmentData', {}).get('currentSpeed', 0)
                },
                "routes": [],
                "incidents": [],
                "roadClosures": []
            }

            # Extract and format route from TomTom response
            if route.get('routes'):
                for route_obj in route['routes']:
                    if route_obj.get('legs'):
                        route_points = []
                        for leg in route_obj['legs']:
                            if leg.get('points'):
                                # Sample points to reduce data volume while maintaining route shape
                                points = leg['points']
                                step = max(1, len(points) // 100)  # Take max 100 points per leg
                                for i in range(0, len(points), step):
                                    point = points[i]
                                    try:
                                        lon = float(point.get('longitude', 0))
                                        lat = float(point.get('latitude', 0))
                                        if -180 <= lon <= 180 and -90 <= lat <= 90:
                                            route_points.append([lon, lat])
                                    except (ValueError, TypeError) as e:
                                        print(f"DEBUG: Error converting point coordinates: {e}")
                                        continue

                        if route_points:
                            result["routes"].append({
                                "id": "route1",
                                "priority": 1,
                                "geometry": {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "LineString",
                                        "coordinates": route_points
                                    }
                                }
                            })

            # Process incidents into GeoJSON format with time-based filtering
            current_time = datetime.now()
            for incident in incidents.get('incidents', []):
                try:
                    coords = incident.get('geometry', {}).get('coordinates', [])
                    props = incident.get('properties', {})
                    
                    # Skip if coordinates are invalid
                    if not coords or not isinstance(coords, list) or len(coords) < 2:
                        continue

                    # Parse incident time
                    start_time = datetime.fromisoformat(props.get('startTime', '').replace('Z', '+00:00'))
                    if current_time - start_time > timedelta(hours=6):
                        continue  # Skip incidents older than 6 hours
                        
                    lat = float(coords[1])
                    lon = float(coords[0])
                    
                    # Ensure coordinates are within the bounding box with some margin
                    if not (min_lon - padding <= lon <= max_lon + padding and 
                           min_lat - padding <= lat <= max_lat + padding):
                        continue
                        
                    if props.get('iconCategory') == 6:  # Road closure
                        result["roadClosures"].append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "type": "Road Closure",
                                "description": f"Road closed - {props.get('roadNumbers', [''])[0]}"
                            }
                        })
                    else:
                        incident_type = "Traffic incident"
                        if props.get('iconCategory') == 1:
                            incident_type = "Accident"
                        elif props.get('iconCategory') == 8:
                            incident_type = "Road works"
                            
                        result["incidents"].append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "type": incident_type,
                                "description": f"{incident_type} - {props.get('roadNumbers', [''])[0]}"
                            }
                        })
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error processing incident: {e}")
                    continue

            return json.dumps(result, indent=2)

        except requests.exceptions.RequestException as e:
            print(f"DEBUG: RequestException: {str(e)}")
            return json.dumps({
                "error": "Traffic API request failed",
                "details": str(e)
            })
        except Exception as e:
            print(f"DEBUG: Unexpected error: {str(e)}")
            return json.dumps({
                "error": "An unexpected error occurred",
                "details": str(e)
            })
