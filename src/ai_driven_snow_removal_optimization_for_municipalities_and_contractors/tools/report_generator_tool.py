from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import os
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio


class ReportGeneratorInput(BaseModel):
    tool_input: str = Field(
        description="A JSON string containing report data with weather, traffic, inventory, and recommendations sections",
        examples=['''{
            "content": {
                "title": "Snow Removal Operations Report",
                "sections": [
                    {
                        "header": "Weather Dashboard",
                        "content": {
                            "current_conditions": {
                                "temperature": -1.28,
                                "conditions": "Snowy",
                                "wind_speed": 4.12,
                                "road_surface_temp": -4.28
                            },
                            "forecast": [
                                {
                                    "time": "2025-02-04 00:00",
                                    "expected_snow": "3.13 mm",
                                    "snow_risk": "High",
                                    "road_condition": "Snowy"
                                }
                            ]
                        }
                    }
                ]
            }
        }''']
    )


class ReportGeneratorTool(BaseTool):
    name: str = "Generate HTML Report"
    args_schema: Type[BaseModel] = ReportGeneratorInput
    description: str = """
    A tool that generates an interactive HTML report with the provided content and visualizations.

    Expected JSON structure:
    {
      "content": {
        "title": "Report Title",
        "sections": [
          {
            "header": "Weather Dashboard",
            "content": {
              "current_conditions": {
                "temperature": number,
                "conditions": string,
                "wind_speed": number,
                "road_surface_temp": number
              },
              "forecast": [
                {
                  "time": "YYYY-MM-DD HH:mm",
                  "expected_snow": "X.XX mm",
                  "snow_risk": "High|Medium|Low",
                  "road_condition": string
                }
              ]
            }
          },
          {
            "header": "Route Optimization",
            "content": {
              "traffic_data": {
                "current_conditions": string,
                "traffic_speed": string,
                "traffic_incidents": [
                  {
                    "type": string,
                    "description": string,
                    "location": {"latitude": number, "longitude": number},
                    "start_time": "ISO datetime",
                    "end_time": "ISO datetime"
                  }
                ]
              },
              "optimized_route": {
                "length": string,
                "travel_time": string,
                "segments": [
                  {
                    "start": "ISO datetime",
                    "end": "ISO datetime",
                    "start_point": {"latitude": number, "longitude": number},
                    "end_point": {"latitude": number, "longitude": number}
                  }
                ]
              }
            }
          },
          {
            "header": "Resource Inventory",
            "content": {
              "inventory_levels": {"resource": "amount"},
              "recent_usage": {"resource": "usage rate"},
              "projected_needs": {"resource": "projected amount"},
              "low_inventory_alerts": {
                "resource": {
                  "Threshold": "amount",
                  "Current Level": "amount",
                  "Alert": string
                }
              }
            }
          },
          {
            "header": "Operational Recommendations",
            "content": {
              "priority_based_schedules": string,
              "completion_estimates": string
            }
          }
        ]
      }
    }

    Features:
    - Interactive weather visualizations
    - Traffic and route mapping
    - Resource inventory tracking
    - Mobile-responsive design
    - Color-coded alerts and status indicators
    """

    def _format_weather_section(self, content: Dict[str, Any]) -> str:
        """Format weather dashboard section"""
        current = content.get('current_conditions', {})
        forecast = content.get('forecast', [])

        # Create weather visualization
        fig = go.Figure()

        # Add current conditions
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=current.get('temperature', 0),
            title={'text': "Temperature (°C)"},
            delta={'reference': current.get('road_surface_temp', 0)},
            domain={'row': 0, 'column': 0}
        ))

        # Add forecast data if available
        if forecast:
            times = []
            snow_amounts = []
            for f in forecast:
                times.append(f.get('time', ''))
                snow_amounts.append(float(f.get('expected_snow', '0').split()[0]))

            fig.add_trace(go.Bar(
                x=times,
                y=snow_amounts,
                name='Expected Snow (mm)',
                marker_color='#3498db'
            ))

        fig.update_layout(
            title='Weather Forecast',
            height=400,
            grid={'rows': 2, 'columns': 1},
            margin=dict(t=50, b=50, l=50, r=50)
        )

        weather_plot = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

        return f"""
        <div class="section weather-section">
            <h2>Weather Dashboard</h2>
            <div class="conditions-grid">
                <div class="condition-item">
                    <span class="label">Temperature:</span>
                    <span class="value">{current.get('temperature', 'N/A')}°C</span>
                </div>
                <div class="condition-item">
                    <span class="label">Conditions:</span>
                    <span class="value">{current.get('conditions', 'N/A')}</span>
                </div>
                <div class="condition-item">
                    <span class="label">Wind Speed:</span>
                    <span class="value">{current.get('wind_speed', 'N/A')} m/s</span>
                </div>
                <div class="condition-item">
                    <span class="label">Road Surface Temp:</span>
                    <span class="value">{current.get('road_surface_temp', 'N/A')}°C</span>
                </div>
            </div>
            {weather_plot}
            <div class="forecast-details">
                <h3>Detailed Forecast</h3>
                <div class="forecast-grid">
                    {''.join([f'''
                    <div class="forecast-item">
                        <div class="time">{f.get('time', '')}</div>
                        <div class="snow">Expected Snow: {f.get('expected_snow', 'N/A')}</div>
                        <div class="risk">Risk Level: <span class="risk-{f.get('snow_risk', '').lower()}">{f.get('snow_risk', 'N/A')}</span></div>
                        <div class="road">Road Condition: {f.get('road_condition', 'N/A')}</div>
                    </div>
                    ''' for f in forecast])}
                </div>
            </div>
        </div>
        """

    def _format_traffic_section(self, content: Dict[str, Any]) -> str:
        """Format traffic and route optimization section"""
        traffic_data = content.get('traffic_data', {})
        route_data = content.get('optimized_route', {})

        # Create traffic incidents visualization
        incidents = traffic_data.get('traffic_incidents', [])
        if incidents:
            fig = go.Figure()

            # Add incidents as scatter points on a map
            lats = [inc['location']['latitude'] for inc in incidents]
            lons = [inc['location']['longitude'] for inc in incidents]
            texts = [f"{inc['type']}: {inc['description']}" for inc in incidents]

            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='markers+text',
                marker=dict(size=12, color='red'),
                text=texts,
                textposition="top center"
            ))

            fig.update_layout(
                mapbox_style="carto-positron",
                mapbox=dict(
                    center=dict(lat=sum(lats) / len(lats), lon=sum(lons) / len(lons)),
                    zoom=12
                ),
                height=400,
                margin=dict(t=0, b=0, l=0, r=0)
            )

            traffic_map = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        else:
            traffic_map = ""

        return f"""
        <div class="section traffic-section">
            <h2>Route Optimization</h2>
            <div class="traffic-conditions">
                <h3>Current Traffic Conditions</h3>
                <div class="conditions-grid">
                    <div class="condition-item">
                        <span class="label">Status:</span>
                        <span class="value">{traffic_data.get('current_conditions', 'N/A')}</span>
                    </div>
                    <div class="condition-item">
                        <span class="label">Speed:</span>
                        <span class="value">{traffic_data.get('traffic_speed', 'N/A')}</span>
                    </div>
                </div>
            </div>

            {traffic_map}

            <div class="route-details">
                <h3>Optimized Route Details</h3>
                <div class="metric-item">
                    <span class="label">Total Distance:</span>
                    <span class="value">{route_data.get('length', 'N/A')}</span>
                </div>
                <div class="metric-item">
                    <span class="label">Estimated Time:</span>
                    <span class="value">{route_data.get('travel_time', 'N/A')}</span>
                </div>

                <h4>Route Segments</h4>
                <div class="segments-container">
                    {''.join([f'''
                    <div class="route-segment">
                        <div class="segment-time">
                            <span class="label">Time:</span>
                            <span class="value">{segment.get('start', '').split('T')[1]} - {segment.get('end', '').split('T')[1]}</span>
                        </div>
                        <div class="segment-points">
                            <div>From: ({segment.get('start_point', {}).get('latitude', 'N/A')}, {segment.get('start_point', {}).get('longitude', 'N/A')})</div>
                            <div>To: ({segment.get('end_point', {}).get('latitude', 'N/A')}, {segment.get('end_point', {}).get('longitude', 'N/A')})</div>
                        </div>
                    </div>
                    ''' for segment in route_data.get('segments', [])])}
                </div>
            </div>
        </div>
        """

    def _format_inventory_section(self, content: Dict[str, Any]) -> str:
        """Format resource inventory section"""
        inventory = content.get('inventory_levels', {})
        usage = content.get('recent_usage', {})
        needs = content.get('projected_needs', {})
        alerts = content.get('low_inventory_alerts', {})

        # Create inventory visualization
        fig = go.Figure()

        # Add current levels vs thresholds
        resources = []
        current_levels = []
        thresholds = []

        for resource, alert_info in alerts.items():
            resources.append(resource)
            current_level = float(alert_info['Current Level'].split()[0])
            threshold = float(alert_info['Threshold'].split()[0])
            current_levels.append(current_level)
            thresholds.append(threshold)

        if resources:
            fig.add_trace(go.Bar(
                name='Current Level',
                x=resources,
                y=current_levels,
                marker_color='#3498db'
            ))

            fig.add_trace(go.Bar(
                name='Threshold',
                x=resources,
                y=thresholds,
                marker_color='#e74c3c'
            ))

            fig.update_layout(
                title='Resource Inventory Levels vs Thresholds',
                barmode='group',
                height=400,
                margin=dict(t=50, b=50, l=50, r=50)
            )

            inventory_plot = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        else:
            inventory_plot = ""

        print("[DEBUG] inventory_levels content:", json.dumps(inventory, indent=2))
        if not inventory:
            print("[ERROR] Inventory data is missing!")
        else:
            print(f"[DEBUG] Inventory Items Found: {list(inventory.keys())}")

        return f"""
        <div class="section inventory-section">
            <h2>Resource Inventory</h2>
            {inventory_plot}

            <div class="inventory-details">
                <h3>Current Inventory Levels</h3>
                <div class="inventory-grid">
                    {''.join([f'''
                    <div class="inventory-item">
                        <div class="resource-name">{resource}</div>
                        <div class="current-level">Current: {level}</div>
                        <div class="usage-rate">Usage: {usage.get(resource, 'N/A')}</div>
                        <div class="projected">Projected Need: {needs.get(resource, 'N/A')}</div>
                        <div class="alert-status">Status: {alerts.get(resource, {}).get('Alert', 'N/A')}</div>
                    </div>
                    ''' for resource, level in inventory.items()])}
                </div>
            </div>
        </div>
        """

    def _run(self, tool_input: str) -> str:
        """Generate an interactive HTML report with the provided content and visualizations"""
        try:
            # Parse the input JSON string
            try:
                # Expect tool_input to be a valid JSON string (as provided by the Pydantic model)
                data = json.loads(tool_input)
            except json.JSONDecodeError as e:
                return f"Error parsing JSON input: {str(e)}\nInput received: {tool_input}"

            content = data.get('content', {})
            if not content:
                return "Error: No content found in the input data"

            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent.parent
            reports_dir = project_root / 'reports'
            os.makedirs(reports_dir, exist_ok=True)

            # Generate report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'snow_removal_report_{timestamp}.html'
            report_path = reports_dir / filename

            # Process sections
            sections_html = ""
            for section in content.get('sections', []):
                if section['header'] == 'Weather Dashboard':
                    sections_html += self._format_weather_section(section['content'])
                elif section['header'] == 'Route Optimization':
                    sections_html += self._format_traffic_section(section['content'])
                elif section['header'] == 'Resource Inventory':
                    sections_html += self._format_inventory_section(section['content'])
                elif section['header'] == 'Operational Recommendations':
                    sections_html += f"""
                    <div class="section recommendations-section">
                        <h2>Operational Recommendations</h2>
                        <div class="recommendations">
                            <p>{section['content'].get('priority_based_schedules', '')}</p>
                            <p>{section['content'].get('completion_estimates', '')}</p>
                        </div>
                    </div>
                    """

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{content.get('title', 'Snow Removal Report')}</title>
                <style>
                    :root {{
                        --primary-color: #2c3e50;
                        --secondary-color: #3498db;
                        --accent-color: #e74c3c;
                        --background-color: #f8f9fa;
                        --text-color: #343a40;
                        --border-color: #dee2e6;
                    }}

                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}

                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        background-color: var(--background-color);
                        color: var(--text-color);
                        padding: 2rem;
                    }}

                    .report-container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}

                    h1, h2, h3, h4 {{
                        color: var(--primary-color);
                        margin-bottom: 1rem;
                    }}

                    h1 {{
                        background-color: var(--primary-color);
                        color: white;
                        padding: 2rem;
                        margin: 0;
                        text-align: center;
                    }}

                    .timestamp {{
                        text-align: right;
                        color: #6c757d;
                        padding: 1rem 2rem;
                        border-bottom: 1px solid var(--border-color);
                    }}

                    .section {{
                        padding: 2rem;
                        border-bottom: 1px solid var(--border-color);
                    }}

                    .conditions-grid, .inventory-grid, .forecast-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 1.5rem;
                        margin: 1.5rem 0;
                    }}

                    .condition-item, .inventory-item, .forecast-item, .route-segment {{
                        background-color: var(--background-color);
                        padding: 1.5rem;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    }}

                    .label {{
                        color: #6c757d;
                        font-weight: 500;
                    }}

                    .value {{
                        font-weight: 600;
                        color: var(--primary-color);
                    }}

                    .risk-high {{ color: var(--accent-color); }}
                    .risk-medium {{ color: #f39c12; }}
                    .risk-low {{ color: #27ae60; }}

                    .recommendations {{
                        background-color: #e8f4f8;
                        padding: 1.5rem;
                        border-radius: 8px;
                        margin-top: 1rem;
                    }}

                    .plotly-graph-div {{
                        margin: 2rem 0;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    }}

                    .segments-container {{
                        display: flex;
                        flex-direction: column;
                        gap: 1rem;
                        margin-top: 1rem;
                    }}

                    .route-segment {{
                        background-color: var(--background-color);
                        padding: 1rem;
                        border-radius: 8px;
                    }}

                    .segment-time {{
                        margin-bottom: 0.5rem;
                        font-weight: 500;
                    }}

                    .segment-points {{
                        color: #666;
                        font-size: 0.9em;
                    }}

                    @media (max-width: 768px) {{
                        body {{
                            padding: 1rem;
                        }}

                        .section {{
                            padding: 1.5rem;
                        }}

                        .conditions-grid, .inventory-grid, .forecast-grid {{
                            grid-template-columns: 1fr;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <h1>{content.get('title', 'Snow Removal Report')}</h1>
                    <div class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                    {sections_html}
                </div>
            </body>
            </html>
            """

            print("[DEBUG] Final HTML Content:\n", html_content[:500])  # Print only the first 500 characters to check
            try:
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("[DEBUG] Report successfully written to file.")
            except Exception as e:
                print(f"[ERROR] Writing report failed: {e}")
                return f"Error writing report: {str(e)}"

            return f"HTML report generated successfully: {report_path}"

        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return f"Error generating report: {str(e)}\nInput received: {tool_input}"