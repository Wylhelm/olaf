from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import os
from typing import Optional


class LocalInventoryToolInput(BaseModel):
    """Input schema for LocalInventoryTool."""
    search_query: str = Field(
        ...,
        description="Mandatory search query you want to use to search the JSON's content"
    )
    json_path: str = Field(
        ...,
        description="Mandatory json path you want to search"
    )


class LocalInventoryTool(BaseTool):
    name: str = "Search a JSON's content"
    description: str = "A tool that can be used to semantic search a query from a JSON's content."
    args_schema: Type[BaseModel] = LocalInventoryToolInput

    def _read_inventory_file(self, file_path: str) -> Optional[dict]:
        """
        Helper method to read and parse a JSON inventory file.
        
        Args:
            file_path: Path to the inventory JSON file
            
        Returns:
            Dict containing the inventory data or None if file cannot be read
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error reading inventory file {file_path}: {str(e)}")
            return None

    def _run(self, search_query: str, json_path: str) -> str:
        """
        Search local inventory files based on the query.
        
        Args:
            search_query: The search query to filter inventory data
            json_path: The path to the JSON file to search ('fuel_inv.json' or 'salt_inv.json')
            
        Returns:
            String containing matching inventory information
        """
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if not json_path.endswith('.json'):
            json_path += '.json'
            
        if json_path not in ['fuel_inv.json', 'salt_inv.json']:
            return json.dumps({
                "status": "error",
                "message": "Invalid JSON path. Use 'fuel_inv.json' or 'salt_inv.json'"
            })
            
        file_path = os.path.join(base_path, json_path)
        data = self._read_inventory_file(file_path)
        
        if not data:
            return json.dumps({
                "status": "error",
                "message": f"Could not read inventory file: {json_path}"
            })
            
        # Determine which inventory type we're dealing with
        inventory_key = 'fuel_inventory' if 'fuel' in json_path else 'salt_inventory'
        
        # Basic semantic search - look for matches in various fields
        search_terms = search_query.lower().split()
        matching_items = []
        
        for item in data[inventory_key]:
            item_str = json.dumps(item).lower()
            if all(term in item_str for term in search_terms):
                matching_items.append(item)
        
        if matching_items:
            return json.dumps({
                "status": "success",
                "source": "local",
                "data": matching_items,
                "metadata": data['metadata']
            }, indent=2)
        
        return json.dumps({
            "status": "error",
            "source": "local",
            "message": f"No matching inventory data found for query: {search_query}"
        })
