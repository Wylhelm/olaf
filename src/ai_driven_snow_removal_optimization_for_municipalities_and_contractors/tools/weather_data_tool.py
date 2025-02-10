from crewai.tools import BaseTool
from typing import Type, Dict, List, ClassVar
from pydantic import BaseModel, Field
import requests
import json
from datetime import datetime
import os

class WeatherDataToolInput(BaseModel):
    """Input schema for WeatherDataTool."""
    region: str = Field(
        ...,
        description="Region to get weather data for (e.g., Montreal, Toronto, Quebec)"
    )
    forecast_days: int = Field(
        default=1,
        description="Number of days to forecast (1-5)"
    )

class WeatherDataTool(BaseTool):
    name: str = "Weather Data Collection Tool"
    description: str = """
    Retrieves detailed weather data including current conditions and forecasts.
    Specializes in snow-related weather conditions critical for snow removal operations.
    Provides data about:
    - Temperature
    - Snowfall amount
    - Snow accumulation
    - Precipitation probability
    - Wind conditions
    - Road surface temperature estimates
    """
    args_schema: Type[BaseModel] = WeatherDataToolInput
    api_key: str = None
    base_url: str = "http://api.openweathermap.org/data/2.5"
    
    # Region to coordinates mapping (matching TomTomTrafficTool)
    region_coordinates: ClassVar[Dict[str, List[float]]] = {
        "Toronto": [43.6532, -79.3832],
        "Montreal": [45.5017, -73.5673],
        "Quebec": [46.8139, -71.2080]
    }
    
    def __init__(self):
        super().__init__()
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable is required")
        self.api_key = api_key
    
    def _get_current_weather(self, lat: float, lon: float) -> dict:
        """Get current weather conditions."""
        endpoint = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def _get_forecast(self, lat: float, lon: float, days: int) -> dict:
        """Get weather forecast."""
        endpoint = f"{self.base_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric',
            'cnt': min(days * 8, 40)  # 8 measurements per day, max 5 days
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    def _estimate_road_surface_temp(self, air_temp: float, cloud_cover: int, is_night: bool) -> float:
        """
        Estimate road surface temperature based on air temperature and conditions.
        This is a simplified model - in production, you'd want a more sophisticated calculation.
        """
        # Road surface is typically warmer than air during day and colder at night
        if is_night:
            # At night, road surface can be 2-4°C colder than air temperature
            temp_diff = -3 * (cloud_cover / 100)  # More clouds = less cooling
        else:
            # During day, road surface can be 10-15°C warmer than air temperature
            temp_diff = 12 * (1 - cloud_cover / 100)  # More clouds = less warming
            
        return air_temp + temp_diff
    
    def _analyze_snow_conditions(self, weather_data: dict) -> dict:
        """Analyze weather data for snow-related conditions."""
        snow_conditions = {
            'has_snow': False,
            'snow_amount_mm': 0,
            'snow_risk': 'low',
            'road_condition': 'clear'
        }
        
        # Check for snow in weather conditions
        for weather in weather_data.get('weather', []):
            if weather['id'] in [600, 601, 602]:  # Snow condition codes
                snow_conditions['has_snow'] = True
                break
        
        # Get snow amount if available
        if 'snow' in weather_data:
            snow_conditions['snow_amount_mm'] = float(weather_data.get('snow', {}).get('3h', '0') or 0)
        
        # Assess snow risk based on temperature and precipitation
        temp = weather_data['main']['temp']
        if temp <= 0 and weather_data['main'].get('humidity', 0) > 80:
            snow_conditions['snow_risk'] = 'high'
        elif temp <= 2:
            snow_conditions['snow_risk'] = 'medium'
        
        # Assess road conditions
        if snow_conditions['has_snow']:
            if temp <= -5:
                snow_conditions['road_condition'] = 'icy'
            else:
                snow_conditions['road_condition'] = 'snowy'
        elif temp <= 0:
            snow_conditions['road_condition'] = 'potential ice'
        
        return snow_conditions

    def _run(self, region: str, forecast_days: int = 1) -> str:
        """
        Main execution method for the tool.
        
        Args:
            region: The region to analyze
            forecast_days: Number of days to forecast (1-5)
            
        Returns:
            JSON string containing weather data and analysis
        """
        try:
            # Validate and get coordinates
            coordinates = self.region_coordinates.get(region)
            if not coordinates:
                return json.dumps({
                    "error": "Invalid region",
                    "details": f"Region '{region}' not found. Available regions: {list(self.region_coordinates.keys())}"
                })
            
            lat, lon = coordinates
            current = self._get_current_weather(lat, lon)
            forecast = self._get_forecast(lat, lon, forecast_days)
            
            # Process current conditions
            current_conditions = self._analyze_snow_conditions(current)
            current_conditions['temperature'] = current['main']['temp']
            current_conditions['wind_speed'] = current['wind']['speed']
            current_conditions['road_surface_temp'] = self._estimate_road_surface_temp(
                current['main']['temp'],
                current['clouds']['all'],
                'n' in current.get('sys', {}).get('pod', 'n')
            )
            
            # Process forecast
            forecast_conditions = []
            for item in forecast['list']:
                conditions = self._analyze_snow_conditions(item)
                conditions['timestamp'] = item['dt_txt']
                conditions['temperature'] = item['main']['temp']
                conditions['wind_speed'] = item['wind']['speed']
                conditions['road_surface_temp'] = self._estimate_road_surface_temp(
                    item['main']['temp'],
                    item['clouds']['all'],
                    'n' in item.get('sys', {}).get('pod', 'n')
                )
                forecast_conditions.append(conditions)
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "region": region,
                "current_conditions": current_conditions,
                "forecast": forecast_conditions,
                "alerts": {
                    "snow_expected": any(f['has_snow'] for f in forecast_conditions),
                    "icy_conditions_risk": any(
                        f['road_condition'] in ['icy', 'potential ice'] 
                        for f in forecast_conditions
                    )
                }
            }
            
            return json.dumps(result, indent=2)
            
        except requests.exceptions.RequestException as e:
            return json.dumps({
                "error": "Weather API request failed",
                "details": str(e)
            })
        except Exception as e:
            return json.dumps({
                "error": "An unexpected error occurred",
                "details": str(e)
            })
