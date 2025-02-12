from crewai.tools import BaseTool
from typing import Type, Dict, Any, List, ClassVar, Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path
from datetime import datetime

class LocalInventoryToolInput(BaseModel):
    search_query: str = Field(
        ...,
        description="Search query for inventory data (e.g., 'fuel levels', 'salt stock')"
    )
    json_path: str = Field(
        ...,
        description="JSON path to search. Valid paths: ['fuel_inv.json', 'salt_inv.json']"
    )

class LocalInventoryTool(BaseTool):
    name: str = "Search Inventory Data"
    description: str = """
    Search and retrieve inventory data from local JSON files.
    Available data includes:
    - Current inventory levels
    - Usage rates and patterns
    - Thresholds and alerts
    - Historical data
    Valid search paths:
    - fuel_inv.json: Fuel-related data
    - salt_inv.json: Salt-related data
    Returns structured inventory data or suggestions for retry if no match is found.
    """
    args_schema: Type[BaseModel] = LocalInventoryToolInput
    INVENTORY_PATHS: ClassVar[Dict[str, str]] = {
        'fuel': 'fuel_inv.json',
        'salt': 'salt_inv.json'
    }

    def _initialize_inventory_files(self) -> None:
        base_path = Path(__file__).parent.parent
        default_data = {
            'fuel': {
                'inventory': {
                    'current_level': 2000,
                    'unit': 'liters',
                    'threshold': 500,
                    'usage_rate': '400 liters per storm',
                    'last_updated': None
                },
                'metadata': {
                    'type': 'fuel',
                    'measuring_unit': 'liters',
                    'update_frequency': 'hourly'
                }
            },
            'salt': {
                'inventory': {
                    'current_level': 500,
                    'unit': 'tons',
                    'threshold': 100,
                    'usage_rate': '50 tons per storm',
                    'last_updated': None
                },
                'metadata': {
                    'type': 'salt',
                    'measuring_unit': 'tons',
                    'update_frequency': 'hourly'
                }
            }
        }
        for resource, data in default_data.items():
            file_path = base_path / f'{resource}_inv.json'
            if not file_path.exists():
                file_path.write_text(json.dumps(data, indent=2))

    def _get_suggested_paths(self, search_query: str) -> List[str]:
        suggestions = []
        query_terms = search_query.lower().split()
        if any(term in ['fuel', 'gasoline', 'diesel'] for term in query_terms):
            suggestions.append(self.INVENTORY_PATHS['fuel'])
        if any(term in ['salt', 'rock_salt', 'treated_salt'] for term in query_terms):
            suggestions.append(self.INVENTORY_PATHS['salt'])
        return suggestions or list(self.INVENTORY_PATHS.values())

    def _load_inventory_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            full_path = Path(__file__).parent.parent / file_path
            if full_path.exists():
                return json.loads(full_path.read_text())
            return None
        except Exception as e:
            return {"error": f"Error reading inventory file: {str(e)}"}

    def _search_inventory(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        query_terms = query.lower().split()

        def matches_query(text: str) -> bool:
            return any(term in text.lower() for term in query_terms)

        if 'inventory' in data:
            if matches_query(json.dumps(data['inventory'])):
                return {'inventory': data['inventory']}
        if matches_query(json.dumps(data)):
            return data
        return {}

    def _run(self, search_query: str, json_path: str) -> str:
        try:
            self._initialize_inventory_files()
            suggested_paths = self._get_suggested_paths(search_query)
            data = self._load_inventory_data(json_path)
            if data is None:
                return json.dumps({
                    "status": "error",
                    "message": f"Invalid path: {json_path}",
                    "suggested_paths": suggested_paths,
                    "example_queries": ["fuel current_level", "salt inventory", "usage rate"]
                }, indent=2)
            if "error" in data:
                return json.dumps({
                    "status": "error",
                    "message": data["error"],
                    "suggested_paths": suggested_paths
                }, indent=2)
            results = self._search_inventory(search_query, data)
            if results:
                return json.dumps({
                    "status": "success",
                    "query": search_query,
                    "path": json_path,
                    "data": results,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "source": "local_inventory"
                    }
                }, indent=2)
            else:
                return json.dumps({
                    "status": "no_results",
                    "message": f"No inventory data found matching query: {search_query}",
                    "suggested_paths": suggested_paths,
                    "example_queries": ["fuel current_level", "salt inventory", "usage rate"]
                }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error processing inventory search: {str(e)}",
                "query": search_query,
                "path": json_path
            }, indent=2)
