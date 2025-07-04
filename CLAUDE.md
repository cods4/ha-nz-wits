# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration for New Zealand's WITS (Wholesale Information Trading System) electricity spot price data. The integration connects to the WITS API using OAuth2 authentication to provide real-time electricity pricing information.

## Development Commands

Since this is a Home Assistant custom integration, there are no build or test commands. Development workflow involves:

1. **Installation Testing**: Copy the `custom_components/nz_wits/` directory to a Home Assistant installation's `custom_components/` folder
2. **Validation**: Use Home Assistant's built-in integration validation (no separate lint/test commands)
3. **Debugging**: Use Home Assistant's logging system and developer tools

## Architecture

### Core Components

- **`__init__.py`**: Integration entry point, handles setup/teardown and platform forwarding
- **`api.py`**: WITS API client with OAuth2 authentication and data fetching
- **`coordinator.py`**: Data update coordinator managing API calls and caching
- **`sensor.py`**: Sensor entities for the four pricing schedules
- **`config_flow.py`**: Configuration flow for UI-based setup
- **`const.py`**: Constants and configuration definitions

### Data Flow

1. **Authentication**: OAuth2 client credentials flow to obtain access tokens
2. **Data Fetching**: Coordinator fetches data for all four schedule types every 5 minutes
3. **Entity Updates**: Sensor entities read from coordinator's cached data
4. **Error Handling**: Graceful handling of auth failures and connection issues

### Schedule Types

The integration creates sensors for four distinct pricing schedules:

- **RTD (Real Time Dispatch)**: Current 5-minute spot price
- **Interim**: Provisional price for previous trading period  
- **PRSS (Price Responsive Schedule Short)**: 3-hour price forecast
- **PRSL (Price Responsive Schedule Long)**: 24-hour price forecast

### Key Configuration

- **Node**: The grid exit point (GXP) identifier (e.g., "TGA0331")
- **Client ID/Secret**: OAuth2 credentials from WITS developer portal
- **Update Intervals**: 5-minute coordinator updates with per-schedule toggle options

### API Integration

- **Base URL**: `https://api.electricityinfo.co.nz`
- **Authentication**: OAuth2 client credentials with automatic token refresh
- **Rate Limiting**: Built-in through coordinator update intervals
- **Error Recovery**: Automatic retry logic for token expiry and connection issues

## File Structure

```
custom_components/nz_wits/
├── __init__.py          # Integration setup/teardown
├── api.py              # WITS API client
├── coordinator.py      # Data update coordinator
├── sensor.py           # Sensor platform entities
├── config_flow.py      # Configuration flow
├── const.py            # Constants and config
├── manifest.json       # Integration metadata
└── translations/       # UI text translations
    └── en.json
```

## Important Notes

- No external dependencies beyond Home Assistant core
- OAuth2 tokens are managed automatically with refresh logic
- Price data is converted from MWh to kWh for user convenience
- Forecast data is included in sensor attributes for PRSS/PRSL schedules
- Entity availability depends on successful API data retrieval


# Using Gemini CLI for Large Codebase Analysis

When analyzing large codebases or multiple files that might exceed context limits, use the Gemini CLI with its massive
context window. Use `gemini -p` to leverage Google Gemini's large context capacity.

## File and Directory Inclusion Syntax

Use the `@` syntax to include files and directories in your Gemini prompts. The paths should be relative to WHERE you run the
  gemini command:

### Examples:

**Single file analysis:**
gemini -p "@src/main.py Explain this file's purpose and structure"

Multiple files:
gemini -p "@package.json @src/index.js Analyze the dependencies used in the code"

Entire directory:
gemini -p "@src/ Summarize the architecture of this codebase"

Multiple directories:
gemini -p "@src/ @tests/ Analyze test coverage for the source code"

Current directory and subdirectories:
gemini -p "@./ Give me an overview of this entire project"

# Or use --all_files flag:
gemini --all_files -p "Analyze the project structure and dependencies"

Implementation Verification Examples

Check if a feature is implemented:
gemini -p "@src/ @lib/ Has dark mode been implemented in this codebase? Show me the relevant files and functions"

Verify authentication implementation:
gemini -p "@src/ @middleware/ Is JWT authentication implemented? List all auth-related endpoints and middleware"

Check for specific patterns:
gemini -p "@src/ Are there any React hooks that handle WebSocket connections? List them with file paths"

Verify error handling:
gemini -p "@src/ @api/ Is proper error handling implemented for all API endpoints? Show examples of try-catch blocks"

Check for rate limiting:
gemini -p "@backend/ @middleware/ Is rate limiting implemented for the API? Show the implementation details"

Verify caching strategy:
gemini -p "@src/ @lib/ @services/ Is Redis caching implemented? List all cache-related functions and their usage"

Check for specific security measures:
gemini -p "@src/ @api/ Are SQL injection protections implemented? Show how user inputs are sanitized"

Verify test coverage for features:
gemini -p "@src/payment/ @tests/ Is the payment processing module fully tested? List all test cases"

When to Use Gemini CLI

Use gemini -p when:
- Analyzing entire codebases or large directories
- Comparing multiple large files
- Need to understand project-wide patterns or architecture
- Current context window is insufficient for the task
- Working with files totaling more than 100KB
- Verifying if specific features, patterns, or security measures are implemented
- Checking for the presence of certain coding patterns across the entire codebase

Important Notes

- Paths in @ syntax are relative to your current working directory when invoking gemini
- The CLI will include file contents directly in the context
- No need for --yolo flag for read-only analysis
- Gemini's context window can handle entire codebases that would overflow Claude's context
- When checking implementations, be specific about what you're looking for to get accurate results
