from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta

class WeatherForecastEntry(BaseModel):
    """Single weather forecast entry with strict validation."""
    time: str = Field(..., description="Forecast timestamp in ISO format")
    snowfall: float = Field(..., ge=0, description="Expected snowfall amount in cm")
    temp: float = Field(..., description="Temperature in Celsius")

    @validator('time')
    def validate_time_format(cls, v):
        try:
            # First try direct ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            try:
                # If that fails, try to parse as a general timestamp
                now = datetime.now()
                if v.lower() == 'later':
                    # Add 3 hours for 'later' entries
                    future = now + timedelta(hours=3)
                    return future.isoformat()
                else:
                    # Try to parse time or use current time
                    try:
                        # Assume it's just a time, add today's date
                        return f"{now.date()}T{v}Z"
                    except:
                        # If all else fails, use current time
                        return now.isoformat()
            except Exception as e:
                print(f"Error standardizing time format: {e}")
                # Return current time as fallback
                return datetime.now().isoformat()

class WeatherAlert(BaseModel):
    """Weather alert with severity level validation."""
    level: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert description")

    @validator('level')
    def validate_level(cls, v):
        valid_levels = {'info', 'warning', 'danger'}
        if v.lower() not in valid_levels:
            raise ValueError(f'Level must be one of {valid_levels}')
        return v.lower()

class WeatherData(BaseModel):
    """Weather data with comprehensive validation."""
    current_temp: float = Field(..., description="Current temperature in Celsius")
    current_conditions: str = Field(..., min_length=1, description="Current weather description")
    accumulation: float = Field(..., ge=0, description="Snow accumulation in cm")
    forecast: List[WeatherForecastEntry] = Field(default_factory=list)
    alerts: List[WeatherAlert] = Field(default_factory=list)

class DepotStatus(BaseModel):
    """Depot status with color validation."""
    name: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    status_color: str = Field(..., pattern='^(success|warning|danger|info)$')

class ResourceData(BaseModel):
    """Resource inventory data with range validation."""
    salt_level: float = Field(..., ge=0, le=100, description="Salt inventory percentage")
    fuel_level: float = Field(..., ge=0, le=100, description="Fuel inventory percentage")
    depots: List[DepotStatus] = Field(default_factory=list)

    @validator('salt_level', 'fuel_level')
    def validate_percentage(cls, v):
        return round(min(max(v, 0), 100), 1)

class RouteData(BaseModel):
    """Route optimization data with validation."""
    active_routes: int = Field(..., ge=0, description="Number of active routes")
    coverage: float = Field(..., ge=0, le=100, description="Coverage percentage")
    efficiency_scores: Dict[str, float] = Field(
        ...,
        description="Route efficiency scores"
    )
    priority_zones: Dict[str, List[Union[float, str]]] = Field(
        ...,
        description="Priority zone statuses"
    )

    @validator('efficiency_scores')
    def validate_efficiency_scores(cls, v):
        return {k: round(min(max(float(score), 0), 100), 1) for k, score in v.items()}

    @validator('priority_zones')
    def validate_priority_zones(cls, v):
        valid_colors = {'success', 'warning', 'danger', 'info'}
        for zone, [score, color] in v.items():
            if not isinstance(score, (int, float)) or not (0 <= float(score) <= 100):
                raise ValueError(f'Invalid score for zone {zone}')
            if color.lower() not in valid_colors:
                raise ValueError(f'Invalid color for zone {zone}')
        return v

class VehicleStatus(BaseModel):
    """Vehicle status with validation."""
    id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    status_color: str = Field(..., pattern='^(success|warning|danger|info)$')
    region: str = Field(..., min_length=1)
    priority: str = Field(..., pattern='^(High|Medium|Low)$')

class FleetData(BaseModel):
    """Fleet management data with validation."""
    vehicles: List[VehicleStatus] = Field(default_factory=list)

class MapIncident(BaseModel):
    """Map incident with location validation."""
    type: int = Field(..., ge=0, le=9, description="Incident type (1=Accident, 6=Road Closed, 8=Road Works, 9=Traffic Jam)")
    description: str = Field(..., min_length=1)
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

class MapRoute(BaseModel):
    """Map route with geometry validation."""
    id: str = Field(..., min_length=1)
    priority: int = Field(..., ge=1, le=3)
    geometry: Dict = Field(...)

    @validator('geometry')
    def validate_geometry(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Geometry must be a dictionary')
        
        if 'type' not in v or v['type'] != 'Feature':
            raise ValueError('Invalid GeoJSON Feature type')
            
        if 'geometry' not in v:
            raise ValueError('Missing geometry object')
            
        geometry = v['geometry']
        if not isinstance(geometry, dict):
            raise ValueError('Geometry object must be a dictionary')
            
        if 'type' not in geometry or geometry['type'] != 'LineString':
            raise ValueError('Invalid GeoJSON geometry type')
            
        if 'coordinates' not in geometry:
            raise ValueError('Missing coordinates array')
            
        coordinates = geometry['coordinates']
        if not isinstance(coordinates, list):
            raise ValueError('Coordinates must be an array')
            
        if not coordinates:
            raise ValueError('Coordinates array cannot be empty')
            
        for coord in coordinates:
            if not isinstance(coord, list) or len(coord) != 2:
                raise ValueError('Each coordinate must be an array of [longitude, latitude]')
            lon, lat = coord
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError('Coordinates must be numbers')
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                raise ValueError('Invalid coordinate values')
                
        return v

class MapData(BaseModel):
    """Map visualization data with validation."""
    routes: List[MapRoute] = Field(default_factory=list)
    incidents: List[MapIncident] = Field(default_factory=list)

class OperationalData(BaseModel):
    """Complete operational data model with cross-validation."""
    weather_data: WeatherData
    resource_data: ResourceData
    route_data: RouteData
    fleet_data: FleetData
    alerts_data: List[WeatherAlert] = Field(default_factory=list)
    map_data: Optional[MapData] = None

    @validator('alerts_data', always=True)
    def validate_and_enhance_alerts(cls, v, values):
        alerts = list(v)
        
        # Add resource alerts
        if 'resource_data' in values:
            resource_data = values['resource_data']
            if resource_data.salt_level < 30:
                alerts.append(WeatherAlert(
                    level='warning',
                    message=f'Salt inventory critical at {resource_data.salt_level:.1f}%'
                ))
            if resource_data.fuel_level < 30:
                alerts.append(WeatherAlert(
                    level='warning',
                    message=f'Fuel inventory critical at {resource_data.fuel_level:.1f}%'
                ))

        # Add weather-based alerts
        if 'weather_data' in values:
            weather_data = values['weather_data']
            if weather_data.accumulation > 20:
                alerts.append(WeatherAlert(
                    level='danger',
                    message=f'Heavy snow accumulation: {weather_data.accumulation:.1f}cm'
                ))
            if weather_data.current_temp < -20:
                alerts.append(WeatherAlert(
                    level='warning',
                    message=f'Extreme cold temperature: {weather_data.current_temp:.1f}°C'
                ))

        return alerts

    class Config:
        validate_assignment = True
        extra = 'forbid'
