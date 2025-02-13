from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import JSONSearchTool, ScrapeWebsiteTool
from .tools.local_inventory_tool import LocalInventoryTool
from .tools.report_generator_tool import ReportGeneratorTool
from .tools.data_transformer_tool import DataTransformerTool
from .tools.tomtom_traffic_tool import TomTomTrafficTool
from .tools.weather_data_tool import WeatherDataTool
from pathlib import Path
import os
from datetime import datetime

@CrewBase
class AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew():
    """AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractors crew"""

    @agent
    def global_planification(self) -> Agent:
        return Agent(
            config=self.agents_config['global_planification'],
            tools=[
                JSONSearchTool(),
                WeatherDataTool(),
                TomTomTrafficTool(),
                LocalInventoryTool()
            ],
        )

    @agent
    def weather_monitor(self) -> Agent:
        return Agent(
            config=self.agents_config['weather_monitor'],
            tools=[
                WeatherDataTool(),
                ScrapeWebsiteTool()  # Keep as backup for additional weather sources
            ],
        )

    @agent
    def stock_resources_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_resources_manager'],
            tools=[
                ScrapeWebsiteTool(),
                LocalInventoryTool()
            ],
        )

    @agent
    def route_optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config['route_optimizer'],
            tools=[
                TomTomTrafficTool(),
                ScrapeWebsiteTool()
            ],
        )

    @agent
    def notifications_alerts_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['notifications_alerts_manager'],
            tools=[
                JSONSearchTool(),
                DataTransformerTool(),
                ReportGeneratorTool()
            ],
        )

    @task
    def global_planning(self) -> Task:
        return Task(
            config=self.tasks_config['global_planning'],
            tools=[
                WeatherDataTool(),
                TomTomTrafficTool(),
                LocalInventoryTool()
            ],
        )

    @task
    def weather_data_collection(self) -> Task:
        return Task(
            config=self.tasks_config['weather_data_collection'],
            tools=[
                WeatherDataTool(),
                ScrapeWebsiteTool()  # Keep as backup for additional weather sources
            ],
        )

    @task
    def traffic_data_integration(self) -> Task:
        return Task(
            config=self.tasks_config['traffic_data_integration'],
            tools=[
                ScrapeWebsiteTool(),
                TomTomTrafficTool()
            ],
        )

    @task
    def resource_monitoring(self) -> Task:
        return Task(
            config=self.tasks_config['resource_monitoring'],
            tools=[JSONSearchTool()],
        )

    @task
    def route_optimization(self) -> Task:
        return Task(
            config=self.tasks_config['route_optimization'],
            tools=[
                ScrapeWebsiteTool(),
                TomTomTrafficTool()
            ],
        )

    @task
    def stakeholder_communication(self) -> Task:
        return Task(
            config=self.tasks_config['stakeholder_communication'],
            tools=[
                JSONSearchTool(),
                DataTransformerTool(),
                ReportGeneratorTool()
            ],
            description="""Transform collected data and generate a comprehensive snow removal operations report:
            1. Use the data transformer tool to process data from:
               - Weather monitor (current conditions and forecast)
               - Stock resources manager (salt and fuel inventory)
               - Route optimizer (traffic and route data)
            2. Generate an interactive HTML report using the transformed data that includes:
               - Current weather conditions and forecast
               - Resource levels and depot status
               - Route coverage and efficiency metrics
               - Fleet status and deployment
               - Critical alerts and notifications
            
            The report should provide stakeholders with clear insights into current operations and any areas needing attention."""
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractors crew"""
        start_time = datetime.now()
        print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] OLAF initialized, kicking off tasks...")

        crew_instance = Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        print(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] All tasks completed in {elapsed_time:.2f} seconds.")

        return crew_instance
