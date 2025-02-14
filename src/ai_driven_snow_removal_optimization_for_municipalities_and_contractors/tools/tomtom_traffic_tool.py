from crewai.tools import BaseTool
from typing import Type, List, Optional, Dict
from pydantic import BaseModel, Field
import requests
import os
from datetime import datetime
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
    
    # Region to coordinates mapping
    region_coordinates: Dict[str, List[List[float]]] = {
        # "Toronto": [
        #     [43.6532, -79.3832],  # Downtown Toronto
        #     [43.7046, -79.3590],  # North York
        #     [43.6481, -79.4143],  # West Toronto
        #     [43.6389, -79.3515]   # East Toronto
        # ],
        # "Montreal": [
        #     [45.5017, -73.5673],  # Downtown Montreal
        #     [45.5088, -73.5878],  # Plateau Mont-Royal
        #     [45.4697, -73.6132],  # Westmount
        #     [45.5461, -73.6369]   # Outremont
        # ],
        "Quebec": [
            [46.8139, -71.2080],  # Old Quebec
            [46.8483, -71.2329],  # Saint-Roch
            [46.7737, -71.2757],  # Sainte-Foy
            [46.8063, -71.1534]   # Beauport
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
            'fields': "{incidents{geometry{type,coordinates},properties{iconCategory,startTime,endTime,length}}}",
            'language': 'en-GB',
            't': -1,
            'categoryFilter': 'Accident,RoadClosed,RoadWorks,Jam',
            'timeValidityFilter': 'present'
        }

        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def _calculate_route(self, coordinates: List[List[float]], route_type: str) -> dict:
        """Calculate optimal route between given coordinates."""
        waypoints = [f"{coord[0]},{coord[1]}" for coord in coordinates]
        locations = ':'.join(waypoints)
        
        endpoint = f"{self.base_url}/routing/1/calculateRoute/{locations}/json"
        params = {
            'key': self.api_key,
            'routeType': route_type,
            'traffic': 'true',
            'travelMode': 'truck'  # Appropriate for snow removal vehicles
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def _get_traffic_flow(self, coordinates: List[List[float]]) -> dict:
        """Get traffic flow data along the route."""
        # Calculate the bounding box from the coordinates
        lats = [coord[0] for coord in coordinates]
        lons = [coord[1] for coord in coordinates]
        min_lat = max(min(lats), -90)
        max_lat = min(max(lats), 90)
        min_lon = max(min(lons), -180)
        max_lon = min(max(lons), 180)
        # Compute the center of the bounding box
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        point = f"{center_lat:.6f},{center_lon:.6f}"
        
        # Flow Segment Data endpoint expects a point, not a bbox.
        endpoint = f"{self.base_url}/traffic/services/4/flowSegmentData/absolute/10/json"
        params = {
            'key': self.api_key,
            'point': point,
            'unit': 'KMPH'
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def _run(self, region: str, route_type: str = "fastest") -> str:
        """Main execution method for the tool."""
        try:
            # Get coordinates for the region
            coordinates = self.region_coordinates.get(region)
            if not coordinates:
                return json.dumps({
                    "error": "Invalid region",
                    "details": f"Region '{region}' not found. Available regions: {list(self.region_coordinates.keys())}"
                })

            # Calculate bounding box for the region based on coordinates
            lats = [coord[0] for coord in coordinates]
            lons = [coord[1] for coord in coordinates]
            min_lon = max(min(lons), -180)
            max_lon = min(max(lons), 180)
            min_lat = max(min(lats), -90)
            max_lat = min(max(lats), 90)
            bbox = f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"

            # Gather all required data
            incidents = self._get_traffic_incidents(bbox)
            route = self._calculate_route(coordinates, route_type)
            flow = self._get_traffic_flow(coordinates)

            # Summarized logging instead of full JSON dump
            incident_count = len(incidents.get('incidents', []))
            road_closures = sum(1 for i in incidents.get('incidents', []) if i['properties'].get('iconCategory') == 6)

            print(f"Traffic Report: {incident_count} incidents, {road_closures} road closures detected.")

            # Extract incidents and format them for the map
            formatted_incidents = []
            formatted_closures = []
            
            for incident in incidents.get('incidents', []):
                props = incident.get('properties', {})
                coords = incident.get('geometry', {}).get('coordinates', [])
                
                if coords and isinstance(coords, list) and len(coords) >= 2:
                    lat = float(coords[1]) if isinstance(coords[1], (int, float, str)) else 0
                    lon = float(coords[0]) if isinstance(coords[0], (int, float, str)) else 0
                    
                    if props.get('iconCategory') == 6:  # Road closure
                        formatted_closures.append(f"Road closed at {lat}, {lon}")
                    else:
                        incident_desc = "Traffic incident"
                        if props.get('iconCategory') == 1:
                            incident_desc = "Accident"
                        elif props.get('iconCategory') == 8:
                            incident_desc = "Road works"
                        elif props.get('iconCategory') == 9:
                            incident_desc = "Traffic jam"
                        formatted_incidents.append(f"{incident_desc} at {lat}, {lon}")

            # Extract and validate route coordinates from the TomTom route response
            route_coords = []
            if route.get('routes') and route['routes'][0].get('legs'):
                for point in route['routes'][0]['legs'][0].get('points', []):
                    lon = float(point.get('longitude', 0))
                    lat = float(point.get('latitude', 0))
                    if -180 <= lon <= 180 and -90 <= lat <= 90:  # Validate coordinates
                        route_coords.append([lon, lat])

            # Format result for the data transformer
            result = {
                "currentTrafficFlow": {
                    "speed": flow.get('flowSegmentData', {}).get('currentSpeed', 0),
                    "incidents": formatted_incidents,
                    "roadClosures": formatted_closures,
                    "optimized_route": {
                        "routes": [{
                            "legs": [{
                                "points": [
                                    {"longitude": coord[0], "latitude": coord[1]}
                                    for coord in route_coords
                                ]
                            }]
                        }]
                    } if route_coords else None
                }
            }

            return json.dumps(result, indent=2)

        except requests.exceptions.RequestException as e:
            return json.dumps({
                "error": "Traffic API request failed",
                "details": str(e)
            })
        except Exception as e:
            return json.dumps({
                "error": "An unexpected error occurred",
                "details": str(e)
            })
