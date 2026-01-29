# Rumpke Waste Collection Home Assistant Integration

Home Assistant custom integration for tracking Rumpke waste collection schedules.

## Features

- Track next garbage/recycling pickup date
- Automatic holiday schedule updates by region
- Service alert notifications
- Multi-region support (Columbus, Cincinnati, Cleveland, Dayton, Louisville, Bluegrass, Greenville, Waverly)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL
6. Install "Rumpke Waste Collection"

### Manual Installation

1. Copy the `custom_components/rumpke` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services
4. Click "Add Integration"
5. Search for "Rumpke"

## Configuration

The integration requires:
- **Zip Code**: Your service address zip code
- **Service Day**: Your normal weekly pickup day (e.g., "Monday", "Tuesday")

## Development

See [docs/development.md](docs/development.md) for development setup and testing.

## License

MIT
