from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pathlib import Path
import os
from datetime import datetime

class ReportGeneratorToolInput(BaseModel):
    """Input schema for ReportGeneratorTool."""
    content: str = Field(
        ...,
        description="The content to include in the HTML report"
    )

class ReportGeneratorTool(BaseTool):
    name: str = "Generate HTML Report"
    description: str = "A tool that generates an HTML report with the provided content and saves it in the reports folder."
    args_schema: Type[BaseModel] = ReportGeneratorToolInput

    def _run(self, content: str) -> str:
        """Generate an HTML report with the provided content"""
        # Get the project root directory (three levels up from this file)
        project_root = Path(__file__).parent.parent.parent.parent
        reports_dir = project_root / 'reports'
        os.makedirs(reports_dir, exist_ok=True)
        report_path = reports_dir / f'snow_removal_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OLAF - Snow Removal Optimization Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .report-container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                .timestamp {{
                    text-align: right;
                    color: #7f8c8d;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                }}
                .content {{
                    white-space: pre-wrap;
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <h1>OLAF - Snow Removal Optimization Report</h1>
                <div class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div class="content">
                    {content}
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return f"HTML report generated: {report_path}"
