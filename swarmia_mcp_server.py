#!/usr/bin/env python3
"""
Swarmia MCP Server

A Model Context Protocol (MCP) server that provides access to Swarmia's Export API.
This server allows you to fetch various metrics and reports from Swarmia including:
- Pull request metrics
- DORA metrics
- Investment balance reports
- Software capitalization reports
- Effort reporting

Based on: https://help.swarmia.com/getting-started/integrations/data-export/export-api
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Swarmia API configuration
SWARMIA_BASE_URL = "https://app.swarmia.com/api/v0"
DEFAULT_TIMEFRAME = "last_7_days"
DEFAULT_TIMEZONE = "UTC"

# Available timeframes
TIMEFRAMES = [
    "last_7_days",
    "last_14_days", 
    "last_30_days",
    "last_60_days",
    "last_90_days",
    "last_180_days",
    "last_365_days"
]

class SwarmiaAPIClient:
    """Client for interacting with Swarmia's Export API."""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = SWARMIA_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Make a request to the Swarmia API and return CSV data."""
        if params is None:
            params = {}
        
        # Add token to params
        params["token"] = self.token
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API request failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Request failed: {e}")
    
    async def get_pull_request_metrics(
        self,
        timeframe: str = DEFAULT_TIMEFRAME,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timezone: str = DEFAULT_TIMEZONE
    ) -> str:
        """Get pull request metrics for the organization."""
        params = {
            "timezone": timezone
        }
        
        if timeframe:
            params["timeframe"] = timeframe
        elif start_date and end_date:
            params["startDate"] = start_date
            params["endDate"] = end_date
        
        return await self._make_request("/reports/pullRequests", params)
    
    async def get_dora_metrics(
        self,
        timeframe: str = DEFAULT_TIMEFRAME,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timezone: str = DEFAULT_TIMEZONE,
        app: Optional[str] = None,
        environment: Optional[str] = None
    ) -> str:
        """Get DORA metrics for the organization."""
        params = {
            "timezone": timezone
        }
        
        if timeframe:
            params["timeframe"] = timeframe
        elif start_date and end_date:
            params["startDate"] = start_date
            params["endDate"] = end_date
        
        if app:
            params["app"] = app
        if environment:
            params["environment"] = environment
        
        return await self._make_request("/reports/dora", params)
    
    async def get_investment_balance(
        self,
        start_date: str,
        end_date: str,
        timezone: str = DEFAULT_TIMEZONE
    ) -> str:
        """Get investment balance statistics using the Effort model."""
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "timezone": timezone
        }
        
        return await self._make_request("/reports/investment", params)
    
    async def get_software_capitalization_report(
        self,
        start_date: str,
        end_date: str,
        timezone: str = DEFAULT_TIMEZONE
    ) -> str:
        """Get software capitalization report."""
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "timezone": timezone
        }
        
        return await self._make_request("/reports/capex", params)
    
    async def get_software_capitalization_employees(
        self,
        year: int,
        timezone: str = DEFAULT_TIMEZONE
    ) -> str:
        """Get list of employees with FTE effort breakdown by month."""
        params = {
            "year": year,
            "timezone": timezone
        }
        
        return await self._make_request("/reports/capex/employees", params)
    
    async def get_effort_reporting(
        self,
        month: str,
        timezone: str = DEFAULT_TIMEZONE,
        custom_field: Optional[str] = None,
        group_by: str = "highestLevelIssue"
    ) -> str:
        """Get effort reporting for authors and their FTE for each issue."""
        params = {
            "month": month,
            "timezone": timezone,
            "groupBy": group_by
        }
        
        if custom_field:
            params["customField"] = custom_field
        
        return await self._make_request("/reports/fte", params)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Global API client instance
api_client: Optional[SwarmiaAPIClient] = None

def get_api_client() -> SwarmiaAPIClient:
    """Get or create the API client instance."""
    global api_client
    if api_client is None:
        token = os.getenv("SWARMIA_API_TOKEN")
        if not token:
            raise Exception("SWARMIA_API_TOKEN environment variable is required")
        api_client = SwarmiaAPIClient(token)
    return api_client

# MCP Server setup
server = Server("swarmia-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Swarmia API tools."""
    tools = [
        Tool(
            name="get_pull_request_metrics",
            description="Get pull request metrics for the organization including cycle time, review rate, merge time, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "enum": TIMEFRAMES,
                        "description": "Predefined timeframe for the data",
                        "default": DEFAULT_TIMEFRAME
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date in YYYY-MM-DD format (alternative to timeframe)"
                    },
                    "end_date": {
                        "type": "string", 
                        "format": "date",
                        "description": "End date in YYYY-MM-DD format (alternative to timeframe)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for data aggregation (e.g., America/New_York)",
                        "default": DEFAULT_TIMEZONE
                    }
                }
            }
        ),
        Tool(
            name="get_dora_metrics",
            description="Get DORA metrics including deployment frequency, change lead time, change failure rate, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "enum": TIMEFRAMES,
                        "description": "Predefined timeframe for the data",
                        "default": DEFAULT_TIMEFRAME
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date in YYYY-MM-DD format (alternative to timeframe)"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date", 
                        "description": "End date in YYYY-MM-DD format (alternative to timeframe)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for data aggregation (e.g., America/New_York)",
                        "default": DEFAULT_TIMEZONE
                    },
                    "app": {
                        "type": "string",
                        "description": "Deployment application name(s), separated by commas if more than one"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Deployment environment(s), separated by commas if more than one"
                    }
                }
            }
        ),
        Tool(
            name="get_investment_balance",
            description="Get investment balance statistics using the Effort model (monthly FTE data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "First day of the month in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Last day of the month in YYYY-MM-DD format"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for data aggregation (e.g., America/New_York)",
                        "default": DEFAULT_TIMEZONE
                    }
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="get_software_capitalization_report",
            description="Get software capitalization report with employee contributions to capitalizable work",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "First day of the start month in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Last day of the end month in YYYY-MM-DD format"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for data aggregation (e.g., America/New_York)",
                        "default": DEFAULT_TIMEZONE
                    }
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="get_software_capitalization_employees",
            description="Get list of employees with FTE effort breakdown for each month of the year",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Year for the report (e.g., 2024)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for data aggregation (e.g., America/New_York)",
                        "default": DEFAULT_TIMEZONE
                    }
                },
                "required": ["year"]
            }
        ),
        Tool(
            name="get_effort_reporting",
            description="Get effort reporting showing authors and their FTE for each issue in a given month",
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {
                        "type": "string",
                        "format": "date",
                        "description": "Month in YYYY-MM-DD format (first day of the month)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for data aggregation (e.g., America/New_York)",
                        "default": DEFAULT_TIMEZONE
                    },
                    "custom_field": {
                        "type": "string",
                        "description": "Jira field ID to be included as Custom field column"
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["highestLevelIssue", "lowestLevelIssue", "customField"],
                        "description": "How FTE rows should be grouped",
                        "default": "highestLevelIssue"
                    }
                },
                "required": ["month"]
            }
        )
    ]
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls to Swarmia API endpoints."""
    try:
        client = get_api_client()
        
        if name == "get_pull_request_metrics":
            result = await client.get_pull_request_metrics(
                timeframe=arguments.get("timeframe") or DEFAULT_TIMEFRAME,
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                timezone=arguments.get("timezone", DEFAULT_TIMEZONE)
            )
            
        elif name == "get_dora_metrics":
            result = await client.get_dora_metrics(
                timeframe=arguments.get("timeframe") or DEFAULT_TIMEFRAME,
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                timezone=arguments.get("timezone", DEFAULT_TIMEZONE),
                app=arguments.get("app"),
                environment=arguments.get("environment")
            )
            
        elif name == "get_investment_balance":
            result = await client.get_investment_balance(
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
                timezone=arguments.get("timezone", DEFAULT_TIMEZONE)
            )
            
        elif name == "get_software_capitalization_report":
            result = await client.get_software_capitalization_report(
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
                timezone=arguments.get("timezone", DEFAULT_TIMEZONE)
            )
            
        elif name == "get_software_capitalization_employees":
            result = await client.get_software_capitalization_employees(
                year=arguments["year"],
                timezone=arguments.get("timezone", DEFAULT_TIMEZONE)
            )
            
        elif name == "get_effort_reporting":
            result = await client.get_effort_reporting(
                month=arguments["month"],
                timezone=arguments.get("timezone", DEFAULT_TIMEZONE),
                custom_field=arguments.get("custom_field"),
                group_by=arguments.get("group_by", "highestLevelIssue")
            )
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return {
            "content": [{"type": "text", "text": result}],
            "isError": False
        }
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }

async def main():
    """Main entry point for the MCP server."""
    # Initialize the server
    options = InitializationOptions(
        server_name="swarmia-mcp",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities=None,
        ),
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            options,
        )

if __name__ == "__main__":
    asyncio.run(main())
