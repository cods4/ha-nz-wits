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