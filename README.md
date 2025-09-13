# Swarmia MCP Server

A Model Context Protocol (MCP) server that provides access to Swarmia's Export API. This server allows you to fetch various metrics and reports from Swarmia including pull request metrics, DORA metrics, investment balance reports, software capitalization reports, and effort reporting.

## Features

This MCP server provides access to the following Swarmia Export API endpoints:

- **Pull Request Metrics** - Cycle time, review rate, merge time, PRs in progress, etc.
- **DORA Metrics** - Deployment frequency, change lead time, change failure rate, mean time to recovery
- **Investment Balance** - Monthly FTE data and investment category breakdowns
- **Software Capitalization Report** - Employee contributions to capitalizable work
- **Software Capitalization Employees** - FTE effort breakdown by month for each employee
- **Effort Reporting** - Authors and their FTE for each issue in a given month

## Prerequisites

- Python 3.8 or higher
- A Swarmia account with API access
- A Swarmia API token (obtain from Settings/API tokens in your Swarmia dashboard)

## Integration with MCP Clients

To use this MCP server with your favourite MCP client (E.g. Claude, Cursor etc.):

1. **Ensure depedancies are installed**
```bash
make install
```

2. **Add the following to your MCP configuration**
```json
   {
     "mcpServers": {
       "swarmia": {
         "command": "/path/to/swarmia-mcp/venv/bin/python3",
         "args": ["/path/to/swarmia-mcp/swarmia_mcp_server.py"],
         "env": {
           "SWARMIA_API_TOKEN": "your_api_token_here"
         }
       }
     }
   }
```

3. **Restart your client application**

4. **Ask for some metrics**
   Example queries:
     - "Analyze our team's pull request cycle time trends"
     - "Get the software capitalization report for Q1 2024"
     - "Show me effort reporting for last month"

## Installation for Development

1. Clone or download this repository
2. Install the required dependencies and setup the project:

```bash
make install
```

3. Set up your Swarmia API token as an environment variable:

```bash
export SWARMIA_API_TOKEN="your_api_token_here"
```

### Quick Setup

For a complete setup including dependency installation and environment checks:

```bash
make setup
```

## Usage

### Running the MCP Server

To run the server:

```bash
make run
```

Or directly:

```bash
python3 swarmia_mcp_server.py
```

The server will start and listen for MCP client connections via stdio.

### Available Tools

The server provides the following tools:

#### 1. `get_pull_request_metrics`
Get pull request metrics for the organization.

**Parameters:**
- `timeframe` (optional): Predefined timeframe (`last_7_days`, `last_14_days`, `last_30_days`, etc.)
- `start_date` (optional): Start date in YYYY-MM-DD format (alternative to timeframe)
- `end_date` (optional): End date in YYYY-MM-DD format (alternative to timeframe)
- `timezone` (optional): Timezone for data aggregation (default: UTC)

**Returns:** CSV data with columns including Start Date, End Date, Team, Cycle Time, Review Rate, Time to first review, PRs merged/week, Merge Time, PRs in progress, Contributors.

#### 2. `get_dora_metrics`
Get DORA metrics for the organization.

**Parameters:**
- `timeframe` (optional): Predefined timeframe
- `start_date` (optional): Start date in YYYY-MM-DD format
- `end_date` (optional): End date in YYYY-MM-DD format
- `timezone` (optional): Timezone for data aggregation
- `app` (optional): Deployment application name(s), comma-separated
- `environment` (optional): Deployment environment(s), comma-separated

**Returns:** CSV data with DORA metrics including Deployment Frequency, Change Lead Time, Average Time to Deploy, Change Failure Rate, Mean Time to Recovery, Deployment Count.

#### 3. `get_investment_balance`
Get investment balance statistics using the Effort model.

**Parameters:**
- `start_date` (required): First day of the month in YYYY-MM-DD format
- `end_date` (required): Last day of the month in YYYY-MM-DD format
- `timezone` (optional): Timezone for data aggregation

**Returns:** CSV data with investment categories, FTE months, relative percentages, and activity counts.

#### 4. `get_software_capitalization_report`
Get software capitalization report with employee contributions.

**Parameters:**
- `start_date` (required): First day of the start month in YYYY-MM-DD format
- `end_date` (required): Last day of the end month in YYYY-MM-DD format
- `timezone` (optional): Timezone for data aggregation

**Returns:** CSV data with employee details, capitalizable work, developer months, and additional context.

#### 5. `get_software_capitalization_employees`
Get list of employees with FTE effort breakdown by month.

**Parameters:**
- `year` (required): Year for the report (e.g., 2024)
- `timezone` (optional): Timezone for data aggregation

**Returns:** CSV data with employee details and monthly FTE breakdowns.

#### 6. `get_effort_reporting`
Get effort reporting for authors and their FTE for each issue.

**Parameters:**
- `month` (required): Month in YYYY-MM-DD format (first day of the month)
- `timezone` (optional): Timezone for data aggregation
- `custom_field` (optional): Jira field ID to include as Custom field column
- `group_by` (optional): How FTE rows should be grouped (`highestLevelIssue`, `lowestLevelIssue`, `customField`)

**Returns:** CSV data with author details, FTE contributions, and issue information.

## Configuration

### Environment Variables

- `SWARMIA_API_TOKEN`: Your Swarmia API token (required)

### Timeframes

The following predefined timeframes are available:
- `last_7_days`
- `last_14_days`
- `last_30_days`
- `last_60_days`
- `last_90_days`
- `last_180_days`
- `last_365_days`

### Timezones

You can specify any timezone using tz database identifiers (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`). The default is UTC.

## API Reference

This MCP server is based on the [Swarmia Export API documentation](https://help.swarmia.com/getting-started/integrations/data-export/export-api).

### Base URL
```
https://app.swarmia.com/api/v0
```

### Authentication
The server uses token-based authentication. Your API token is passed as a query parameter to all requests.

## Error Handling

The server includes comprehensive error handling for:
- Missing or invalid API tokens
- HTTP request failures
- Invalid parameters
- API rate limiting
- Network connectivity issues

## Logging

The server logs all activities at the INFO level. You can adjust the logging level by modifying the `logging.basicConfig()` call in the server code.

## Development

### Available Make Targets

The project includes a comprehensive Makefile with the following targets:

- `make help` - Show available targets and help information
- `make install` - Install dependencies and setup the project
- `make setup` - Complete setup (install + environment checks)
- `make test` - Test the API connection and server functionality
- `make run` - Run the MCP server
- `make check-env` - Check if required environment variables are set
- `make clean` - Clean up temporary files
- `make format` - Format code with black (if available)
- `make lint` - Lint code with flake8 (if available)
- `make type-check` - Type check with mypy (if available)
- `make quality` - Run all quality checks
- `make info` - Show project information

### Testing

To test the server:

```bash
make test
```

## Example Usage

Here's an example of how you might use this server with an MCP client:

```python
# Example: Get pull request metrics for the last 30 days
result = await client.call_tool(
    "get_pull_request_metrics",
    {
        "timeframe": "last_30_days",
        "timezone": "America/New_York"
    }
)

# Example: Get DORA metrics for a specific date range
result = await client.call_tool(
    "get_dora_metrics",
    {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "app": "my-app",
        "environment": "production"
    }
)

# Example: Get investment balance for January 2024
result = await client.call_tool(
    "get_investment_balance",
    {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
)
```

## Troubleshooting

### Common Issues

1. **"SWARMIA_API_TOKEN environment variable is required"**
   - Make sure you've set the `SWARMIA_API_TOKEN` environment variable
   - Verify your token is valid and has the necessary permissions

2. **"API request failed with status 401"**
   - Your API token may be invalid or expired
   - Check your token in the Swarmia dashboard

3. **"API request failed with status 403"**
   - Your token may not have permission to access the requested data
   - Contact your Swarmia administrator

4. **"Request failed: Connection timeout"**
   - Check your internet connection
   - Verify that `app.swarmia.com` is accessible from your network

### Getting Help

- Check the [Swarmia Export API documentation](https://help.swarmia.com/getting-started/integrations/data-export/export-api)
- Review the Swarmia API token settings in your dashboard
- Contact Swarmia support for API-related issues
