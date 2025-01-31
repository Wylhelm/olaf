from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import JSONSearchTool, ScrapeWebsiteTool
from .tools.local_inventory_tool import LocalInventoryTool

@CrewBase
class AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractorsCrew():
    """AiDrivenSnowRemovalOptimizationForMunicipalitiesAndContractors crew"""

    @agent
    def global_planification(self) -> Agent:
        return Agent(
            config=self.agents_config['global_planification'],
            tools=[JSONSearchTool()],
        )

    @agent
    def weather_monitor(self) -> Agent:
        return Agent(
            config=self.agents_config['weather_monitor'],
            tools=[ScrapeWebsiteTool()],
        )

    @agent
    def stock_resources_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_resources_manager'],
            tools=[
                JSONSearchTool(),
                ScrapeWebsiteTool(),
                LocalInventoryTool()
            ],
        )

    @agent
    def route_optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config['route_optimizer'],
            tools=[ScrapeWebsiteTool()],
        )

    @agent
    def notifications_alerts_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['notifications_alerts_manager'],
            tools=[JSONSearchTool()],
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
            tools=[ScrapeWebsiteTool()],
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
            tools=[ScrapeWebsiteTool()],
        )

    @task
    def stakeholder_communication(self) -> Task:
        return Task(
            config=self.tasks_config['stakeholder_communication'],
            tools=[JSONSearchTool()],
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
