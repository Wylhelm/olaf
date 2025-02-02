from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import JSONSearchTool, ScrapeWebsiteTool
from .tools.local_inventory_tool import LocalInventoryTool
from .tools.report_generator_tool import ReportGeneratorTool
from .tools.tomtom_traffic_tool import TomTomTrafficTool
from pathlib import Path
import os
from datetime import datetime

@CrewBase
class AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew():
    """AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractors crew"""

    @agent
    def global_planification(self) -> Agent:
        config = self.agents_config['global_planification']
        if 'model' in config:
            if config['model'].startswith('ollama/'):
                config['llm'] = config['model']
                config['api_base_url'] = config.pop('api_base')
                del config['model']
            elif config['model'].startswith('lmstudio/'):
                model_name = config['model'].replace('lmstudio/', '')
                config['model'] = model_name
                config['api_key'] = 'not-needed'
                config['base_url'] = config.pop('api_base')
                config['model_type'] = 'openai'
            
        return Agent(
            config=config,
            tools=[
                JSONSearchTool(),
                ScrapeWebsiteTool(),
                TomTomTrafficTool(),
                LocalInventoryTool(),
                ReportGeneratorTool()
            ],
        )

    @agent
    def weather_monitor(self) -> Agent:
        config = self.agents_config['weather_monitor']
        if 'model' in config:
            if config['model'].startswith('ollama/'):
                config['llm'] = config['model']
                config['api_base_url'] = config.pop('api_base')
                del config['model']
            elif config['model'].startswith('lmstudio/'):
                model_name = config['model'].replace('lmstudio/', '')
                config['model'] = model_name
                config['api_key'] = 'not-needed'
                config['base_url'] = config.pop('api_base')
                config['model_type'] = 'openai'
            
        return Agent(
            config=config,
            tools=[
                ScrapeWebsiteTool(),
                TomTomTrafficTool()
            ],
        )

    @agent
    def stock_resources_manager(self) -> Agent:
        config = self.agents_config['stock_resources_manager']
        if 'model' in config:
            if config['model'].startswith('ollama/'):
                config['llm'] = config['model']
                config['api_base_url'] = config.pop('api_base')
                del config['model']
            elif config['model'].startswith('lmstudio/'):
                model_name = config['model'].replace('lmstudio/', '')
                config['model'] = model_name
                config['api_key'] = 'not-needed'
                config['base_url'] = config.pop('api_base')
                config['model_type'] = 'openai'
            
        return Agent(
            config=config,
            tools=[
                JSONSearchTool(),
                ScrapeWebsiteTool(),
                LocalInventoryTool()
            ],
        )

    @agent
    def route_optimizer(self) -> Agent:
        config = self.agents_config['route_optimizer']
        if 'model' in config:
            if config['model'].startswith('ollama/'):
                config['llm'] = config['model']
                config['api_base_url'] = config.pop('api_base')
                del config['model']
            elif config['model'].startswith('lmstudio/'):
                model_name = config['model'].replace('lmstudio/', '')
                config['model'] = model_name
                config['api_key'] = 'not-needed'
                config['base_url'] = config.pop('api_base')
                config['model_type'] = 'openai'
            
        return Agent(
            config=config,
            tools=[
                ScrapeWebsiteTool(),
                TomTomTrafficTool()
            ],
        )

    @agent
    def notifications_alerts_manager(self) -> Agent:
        config = self.agents_config['notifications_alerts_manager']
        if 'model' in config:
            if config['model'].startswith('ollama/'):
                config['llm'] = config['model']
                config['api_base_url'] = config.pop('api_base')
                del config['model']
            elif config['model'].startswith('lmstudio/'):
                model_name = config['model'].replace('lmstudio/', '')
                config['model'] = model_name
                config['api_key'] = 'not-needed'
                config['base_url'] = config.pop('api_base')
                config['model_type'] = 'openai'
            
        return Agent(
            config=config,
            tools=[
                JSONSearchTool(),
                ReportGeneratorTool()
            ],
        )


    @task
    def global_planning(self) -> Task:
        return Task(
            config=self.tasks_config['global_planning'],
            tools=[
                JSONSearchTool(),
                ScrapeWebsiteTool(),
                TomTomTrafficTool(),
                LocalInventoryTool(),
                ReportGeneratorTool()
            ],
        )

    @task
    def weather_data_collection(self) -> Task:
        return Task(
            config=self.tasks_config['weather_data_collection'],
            tools=[ScrapeWebsiteTool()],
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
                ReportGeneratorTool()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractors crew"""
        print("OLAF initialized, kicking off tasks...")
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
