from datetime import datetime
import os
from typing import Dict, List, Any
import json
from crewai.tools import BaseTool

class ReportGeneratorTool(BaseTool):
    """Tool for generating interactive HTML dashboard reports for snow removal operations."""
    
    name: str = "Report Generator"
    description: str = """Generates interactive HTML dashboard reports for snow removal operations.
    
    Input should be a JSON string containing:
    {
        "weather_data": {
            "current_temp": float,
            "current_conditions": str,
            "accumulation": float,
            "forecast": [{"time": str, "snowfall": float, "temp": float}, ...],
            "alerts": [...]
        },
        "resource_data": {
            "salt_level": float,
            "fuel_level": float,
            "depots": [{"name": str, "status": str, "status_color": str}, ...]
        },
        "route_data": {
            "active_routes": int,
            "coverage": float,
            "efficiency_scores": {"route_name": float, ...},
            "priority_zones": {"zone_name": [float, str], ...}
        },
        "fleet_data": {
            "vehicles": [{"id": str, "status": str, "status_color": str, "region": str, "priority": str}, ...]
        },
        "alerts_data": [{"level": str, "message": str}, ...]
    }"""

    template_path: str = ""

    def __init__(self):
        super().__init__()
        self.template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'reports',
            'snow_removal_dashboard_template.html'
        )
        
    def _run(self, input_str: str = "") -> str:
        """
        Generate an interactive HTML dashboard report using the provided data.
        
        Args:
            input_str: JSON string containing:
                {
                    "weather_data": {...},
                    "resource_data": {...},
                    "route_data": {...},
                    "fleet_data": {...},
                    "alerts_data": [...]
                }
                
        Returns:
            str: Path to the generated report file
        """
        if not input_str:
            raise ValueError("Input string cannot be empty. Must provide JSON data following the schema.")
            
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}. Ensure the data is a valid JSON string and not double-encoded.")
            
        # Validate required sections
        required_sections = ['weather_data', 'resource_data', 'route_data', 'fleet_data', 'alerts_data']
        missing_sections = [section for section in required_sections if section not in data]
        if missing_sections:
            raise ValueError(f"Missing required sections: {', '.join(missing_sections)}")
            
        try:
            weather_data = data['weather_data']
            # Validate and sanitize weather_data structure
            required_weather_fields = ['current_temp', 'current_conditions', 'accumulation', 'forecast', 'alerts']
            for field in required_weather_fields:
                if field not in weather_data or weather_data[field] is None:
                    if field in ['current_temp', 'accumulation']:
                        weather_data[field] = 0.0
                    elif field == 'current_conditions':
                        weather_data[field] = 'No data available'
                    elif field == 'forecast':
                        weather_data[field] = []
                    elif field == 'alerts':
                        weather_data[field] = []
                
            resource_data = data['resource_data']
            # Validate and sanitize resource_data structure
            required_resource_fields = ['salt_level', 'fuel_level', 'depots']
            for field in required_resource_fields:
                if field not in resource_data or resource_data[field] is None:
                    if field in ['salt_level', 'fuel_level']:
                        resource_data[field] = 0.0
                    elif field == 'depots':
                        resource_data[field] = []
                
            route_data = data['route_data']
            # Validate and sanitize route_data structure
            required_route_fields = ['active_routes', 'coverage', 'efficiency_scores', 'priority_zones']
            for field in required_route_fields:
                if field not in route_data or route_data[field] is None:
                    if field == 'active_routes':
                        route_data[field] = 0
                    elif field == 'coverage':
                        route_data[field] = 0.0
                    elif field in ['efficiency_scores', 'priority_zones']:
                        route_data[field] = {}
                
            fleet_data = data['fleet_data']
            # Validate and sanitize fleet_data structure
            if 'vehicles' not in fleet_data or fleet_data['vehicles'] is None:
                fleet_data['vehicles'] = []
                
            alerts_data = data['alerts_data']
            # Validate and sanitize alerts_data structure
            if not isinstance(alerts_data, list) or alerts_data is None:
                alerts_data = []
                data['alerts_data'] = alerts_data
            
            # Add a system alert if any data is missing
            has_missing_data = (
                not weather_data['forecast'] or
                not resource_data['depots'] or
                not fleet_data['vehicles'] or
                not route_data['efficiency_scores'] and not route_data['priority_zones']
            )
            if has_missing_data:
                alerts_data.append({
                    "level": "warning",
                    "message": "Some data is currently unavailable. Dashboard showing partial information."
                })
                
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
        except TypeError as e:
            raise ValueError(f"Invalid data type in structure: {str(e)}")
        # Read template
        with open(self.template_path, 'r') as f:
            template = f.read()
            
        # Generate timestamp for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Replace weather data
        weather_updates = {
            'current_temp': f"{weather_data['current_temp']}°C",
            'current_conditions': weather_data['current_conditions'],
            'accumulation': f"{weather_data['accumulation']}cm",
            'weather_chart_data': json.dumps({
                'labels': [entry['time'] for entry in weather_data['forecast']],
                'datasets': [
                    {
                        'label': 'Snowfall (cm/h)',
                        'data': [entry['snowfall'] for entry in weather_data['forecast']],
                        'borderColor': '#3498db',
                        'tension': 0.4
                    },
                    {
                        'label': 'Temperature (°C)',
                        'data': [entry['temp'] for entry in weather_data['forecast']],
                        'borderColor': '#e74c3c',
                        'tension': 0.4
                    }
                ]
            })
        }
        
        # Replace resource data
        resource_updates = {
            'salt_level': f"{resource_data['salt_level']}%",
            'fuel_level': f"{resource_data['fuel_level']}%",
            'depots_table': '\n'.join([
                f"""
                <tr>
                    <td>{depot['name']}</td>
                    <td><span class="badge bg-{depot['status_color']}">{depot['status']}</span></td>
                </tr>
                """ for depot in resource_data['depots']
            ])
        }
        
        # Replace route data
        route_updates = {
            'active_routes': str(route_data['active_routes']),
            'coverage': f"{route_data['coverage']}%",
            'route_chart_data': json.dumps({
                'labels': list(route_data['efficiency_scores'].keys()),
                'datasets': [{
                    'label': 'Route Efficiency Score',
                    'data': list(route_data['efficiency_scores'].values()),
                    'backgroundColor': '#3498db'
                }]
            }),
            'priority_zones': '\n'.join([
                f"""<div class="progress-bar bg-{color}" role="progressbar" 
                    style="width: {percentage}%" aria-valuenow="{percentage}">
                    {zone} ({percentage}%)</div>"""
                for zone, (percentage, color) in route_data['priority_zones'].items()
            ])
        }
        
        # Replace fleet data
        fleet_updates = {
            'fleet_table': '\n'.join([
                f"""
                <tr>
                    <td>{vehicle['id']}</td>
                    <td><span class="badge bg-{vehicle['status_color']}">{vehicle['status']}</span></td>
                    <td>{vehicle['region']}</td>
                    <td>{vehicle['priority']}</td>
                </tr>
                """ for vehicle in fleet_data['vehicles']
            ])
        }
        
        # Replace alerts
        alerts_updates = {
            'alerts_section': '\n'.join([
                f"""
                <div class="alert alert-{alert['level']}" role="alert">
                    <i class="fas fa-{self._get_alert_icon(alert['level'])}"></i> {alert['message']}
                </div>
                """ for alert in alerts_data
            ])
        }
        
        # Get TomTom API key from environment
        tomtom_api_key = os.getenv('TOMTOM_API_KEY')
        if not tomtom_api_key:
            print("Warning: TOMTOM_API_KEY not found in environment variables")
            tomtom_api_key = ''

        # Apply all updates to template
        report_content = template
        for key, value in {
            **weather_updates, 
            **resource_updates, 
            **route_updates, 
            **fleet_updates, 
            **alerts_updates,
            'tomtom_api_key': tomtom_api_key
        }.items():
            placeholder = f"{{{{data.{key}}}}}"
            if key in ['weather_chart_data', 'route_chart_data']:
                # For chart data, we need to ensure it's properly escaped for JavaScript
                report_content = report_content.replace(
                    placeholder,
                    value.replace('\\', '\\\\').replace('"', '\\"')
                )
            else:
                report_content = report_content.replace(placeholder, str(value))
            
        # Save report
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'reports',
            f'snow_removal_report_{timestamp}.html'
        )
        
        with open(report_path, 'w') as f:
            f.write(report_content)
            
        return report_path
        
    def _get_alert_icon(self, level: str) -> str:
        """Get the appropriate Font Awesome icon for alert level."""
        return {
            'danger': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        }.get(level, 'info-circle')

    def update_report_data(self, report_path: str, 
                          section: str, 
                          data: Dict[str, Any]) -> None:
        """
        Update specific sections of an existing report with new data.
        
        Args:
            report_path: Path to the report file
            section: Section identifier ('weather', 'resources', 'routes', 'fleet', 'alerts')
            data: New data for the section
        """
        # Implementation for real-time updates if needed
        pass

def create_tool() -> ReportGeneratorTool:
    """Factory function to create an instance of the ReportGeneratorTool."""
    return ReportGeneratorTool()
