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
        # TomTom expects coordinates in latitude,longitude format
        waypoints = [f"{coord[1]:.6f},{coord[0]:.6f}" for coord in coordinates]  # Convert to lat,lon for TomTom API
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
        lats = [coord[1] for coord in coordinates]  # Extract latitude from [lon, lat]
        lons = [coord[0] for coord in coordinates]  # Extract longitude from [lon, lat]
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

            # Calculate bounding box with padding for better coverage
            lats = [coord[1] for coord in coordinates]  # Extract latitude from [lon, lat]
            lons = [coord[0] for coord in coordinates]  # Extract longitude from [lon, lat]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # Add padding of roughly 2km
            padding = 0.02  # approximately 2km in decimal degrees
            min_lon = max(min(lons) - padding, -180)
            max_lon = min(max(lons) + padding, 180)
            min_lat = max(min(lats) - padding, -90)
            max_lat = min(max(lats) + padding, 90)
            bbox = f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"

            # Get traffic incidents first
            incidents = self._get_traffic_incidents(bbox)
            
            # Get traffic flow data for the region
            flow = self._get_traffic_flow([[center_lat, center_lon]])

            # Calculate route using the region's coordinates for proper road alignment
            route = self._calculate_route(coordinates, route_type)

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
                                for point in leg['points']:
                                    lon = float(point.get('longitude', 0))
                                    lat = float(point.get('latitude', 0))
                                    if -180 <= lon <= 180 and -90 <= lat <= 90:
                                        route_points.append([lon, lat])

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

            # Process incidents into GeoJSON format
            for incident in incidents.get('incidents', []):
                coords = incident.get('geometry', {}).get('coordinates', [])
                props = incident.get('properties', {})
                
                if coords and isinstance(coords, list) and len(coords) >= 2:
                    lat = float(coords[1])
                    lon = float(coords[0])
                    
                    if props.get('iconCategory') == 6:  # Road closure
                        result["roadClosures"].append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "type": "Road Closure",
                                "description": "Road closed"
                            }
                        })
                    else:
                        incident_type = "Traffic incident"
                        if props.get('iconCategory') == 1:
                            incident_type = "Accident"
                        elif props.get('iconCategory') == 8:
                            incident_type = "Road works"
                        elif props.get('iconCategory') == 9:
                            incident_type = "Traffic jam"
                            
                        result["incidents"].append({
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            },
                            "properties": {
                                "type": incident_type,
                                "description": incident_type
                            }
                        })

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
