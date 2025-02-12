from crewai.tools import BaseTool
from typing import Type, Optional, Dict, Any, List, ClassVar
from pydantic import BaseModel, Field
import json
from pathlib import Path
from datetime import datetime


class LocalInventoryToolInput(BaseModel):
    """Input schema for LocalInventoryTool."""
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
    Returns structured inventory data or suggestions for retry if no match found.
    """
    args_schema: Type[BaseModel] = LocalInventoryToolInput

    # Define standard inventory paths with proper type annotation
    INVENTORY_PATHS: ClassVar[Dict[str, str]] = {
        'fuel': 'fuel_inv.json',
        'salt': 'salt_inv.json'
    }

    def _initialize_inventory_files(self) -> None:
        """Initialize inventory files with default data if they don't exist."""
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

        # Create individual inventory files if they do not exist
        for resource, data in default_data.items():
            file_path = base_path / f'{resource}_inv.json'
            if not file_path.exists():
                file_path.write_text(json.dumps(data, indent=2))

    def _get_suggested_paths(self, search_query: str) -> List[str]:
        """Get suggested paths based on search query."""
        suggestions = []
        query_terms = search_query.lower().split()

        if any(term in ['fuel', 'gasoline', 'diesel'] for term in query_terms):
            suggestions.append(self.INVENTORY_PATHS['fuel'])
        if any(term in ['salt', 'rock_salt', 'treated_salt'] for term in query_terms):
            suggestions.append(self.INVENTORY_PATHS['salt'])

        return suggestions or list(self.INVENTORY_PATHS.values())

    def _load_inventory_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load inventory data from specified file."""
        try:
            full_path = Path(__file__).parent.parent / file_path
            if full_path.exists():
                return json.loads(full_path.read_text())
            return None
        except Exception as e:
            return {"error": f"Error reading inventory file: {str(e)}"}

    def _search_inventory(self, query: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Search inventory data based on query terms with relaxed matching."""
        query_terms = query.lower().split()

        # Relaxed helper function: returns True if any query term is present in text
        def matches_query(text: str) -> bool:
            text = text.lower()
            return any(term in text for term in query_terms)

        # Try to match specific 'inventory' section first
        if 'inventory' in data:
            text_to_search = json.dumps(data['inventory']).lower()
            if matches_query(text_to_search):
                return {'inventory': data['inventory']}

        # If no specific match found, search the entire content
        text_to_search = json.dumps(data).lower()
        if matches_query(text_to_search):
            return data

        return {}

    def _run(self, search_query: str, json_path: str) -> str:
        """
        Execute inventory search with improved error handling and suggestions.
        Args:
            search_query: Search terms for filtering inventory data.
            json_path: Path to inventory data file.
        Returns:
            JSON string containing:
            - Matching inventory data (if found)
            - Search metadata
            - Suggested alternatives if no matches
            - Error details if applicable.
        """
        try:
            # Initialize inventory files if needed
            self._initialize_inventory_files()

            # Get suggested paths based on query
            suggested_paths = self._get_suggested_paths(search_query)

            # Try to load and search the specified path
            data = self._load_inventory_data(json_path)
            if data is None:
                return json.dumps({
                    "status": "error",
                    "message": f"Invalid path: {json_path}",
                    "suggested_paths": suggested_paths,
                    "example_queries": [
                        "fuel current_level",
                        "salt inventory",
                        "usage rate"
                    ]
                }, indent=2)

            if "error" in data:
                return json.dumps({
                    "status": "error",
                    "message": data["error"],
                    "suggested_paths": suggested_paths
                }, indent=2)

            # Search the data using the relaxed matching function
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
                    "example_queries": [
                        "fuel current_level",
                        "salt inventory",
                        "usage rate"
                    ]
                }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error processing inventory search: {str(e)}",
                "query": search_query,
                "path": json_path
            }, indent=2)