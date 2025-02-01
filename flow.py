from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

class SnowRemovalState(BaseModel):
    weather_data: str = ""
    traffic_data: str = ""
    resources: str = ""
    routes: str = ""
    notifications: str = ""

class SnowRemovalFlow(Flow[SnowRemovalState]):
    @start()
    def collect_weather_data(self):
        print("Collecting weather data")
        self.state.weather_data = "Weather data collected"
        return self.state.weather_data

    @listen(collect_weather_data)
    def integrate_traffic_data(self, weather_data):
        print("Integrating traffic data")
        self.state.traffic_data = "Traffic data integrated"
        return self.state.traffic_data

    @listen(integrate_traffic_data)
    def monitor_resources(self, traffic_data):
        print("Monitoring resources")
        self.state.resources = "Resources monitored"
        return self.state.resources

    @listen(monitor_resources)
    def optimize_routes(self, resources):
        print("Optimizing routes")
        self.state.routes = "Routes optimized"
        return self.state.routes

    @listen(optimize_routes)
    def send_notifications(self, routes):
        print("Sending notifications")
        self.state.notifications = "Notifications sent"
        return self.state.notifications

if __name__ == "__main__":
    flow = SnowRemovalFlow()
    flow.plot()
