# NZ WITS Spot Price Integration for Home Assistant

This is a custom integration for Home Assistant that fetches electricity spot price data from New Zealand's Wholesale Information Trading System (WITS) via their official API.

It was inspired by a Node-RED flow and created to provide a more robust and native Home Assistant experience for monitoring NZ's volatile electricity market prices. This is particularly useful for users with home automation, solar, and battery systems who want to make informed decisions about energy consumption.

## Features
- OAuth2 Authentication: Securely connects to the WITS API using your client credentials.
- Four Price Sensors: Creates sensors for the four main pricing schedules:
  - Real Time Dispatch (RTD): The current 5-minute spot price. Updates every minute.
  - Interim Price: The provisional price for the previous trading period. Updates every 5 minutes.
  - Price Responsive Schedule Short (PRSS): A 3-hour price forecast. Updates hourly.
  - Price Responsive Schedule Long (PRSL): A 24-hour price forecast. Updates hourly.
- UI Configuration: Simple setup process directly within the Home Assistant UI. No YAML required.
- Forecast Attributes: The PRSS and PRSL sensors include the full price forecast in their state attributes, making it accessible for advanced automations and charts.

## Obtaining API Credentials and Node

Before you can configure this integration, you need to obtain API credentials from the WITS developer portal and identify your connection node.

1.  **Create a WITS Developer Account:**
    *   Go to [https://developer.electricityinfo.co.nz/WITS](https://developer.electricityinfo.co.nz/WITS).
    *   Click on "Sign Up" and follow the steps to create an account.
2.  **Create an Application and Generate Credentials:**
    *   Once logged in, navigate to "My Apps".
    *   Click "Create new application".
    *   Enter any name for your application (e.g., "Home Assistant").
    *   The "Redirect URI" can be any valid URL (e.g., `https://google.com`). This is not used by the integration but is required by the WITS portal.
    *   Click "Generate Credential".
3.  **Activate API Service:**
    *   For your newly created credential, find the "Services" section.
    *   Activate the **Pricing_API_Application_Registration** service. This is crucial for the integration to access pricing data.
4.  **Record Your Credentials:**
    *   Note down your **Client ID** and **Client Secret**. You will need these when configuring the integration in Home Assistant.
5.  **Find Your Connection Node:**
    *   You can look up your address to find your connection node (Grid Exit Point - GXP) here: [https://www.ea.govt.nz/your-power/your-meter/address/](https://www.ea.govt.nz/your-power/your-meter/address/)
    *   Your node is typically a 7-character string, for example, `TGA0331`.

With your Client ID, Client Secret, and Node identifier ready, you can proceed with the installation and configuration of the integration.

## Installation
### Recommended Method: HACS
1. Add this repository as a custom repository in HACS.
2. Search for "NZ WITS Spot Price" and install it.
3. Restart Home Assistant.

### Manual Method
1. Using the tool of your choice (e.g., Samba, VSCode), copy the nz_wits directory from this repository into your Home Assistant custom_components folder.
2. Restart Home Assistant.

## Configuration
1. Navigate to Settings -> Devices & Services.
2. Click + Add Integration.
3. Search for NZ WITS Spot Price and select it.
4. In the configuration dialog, enter:
  - Client ID: Your WITS API Client ID.
  - Client Secret: Your WITS API Client Secret.
  - Node: The grid exit point (GXP) you want to monitor (e.g., TGA0331 for Tauranga).
5. Click Submit. The integration will be set up, and your new sensors will appear.

## Credits
- This integration was built based on an original Node-RED flow.
- Data is sourced from the Electricity Authority's WITS API.
