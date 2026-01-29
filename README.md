# Rumpke Waste Collection - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
![GitHub Release](https://img.shields.io/github/v/release/patrickjcash/rumpke-ha?style=for-the-badge)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg?style=for-the-badge)
![License](https://img.shields.io/github/license/patrickjcash/rumpke-ha?style=for-the-badge)
![IoT Class](https://img.shields.io/badge/IoT%20Class-Cloud%20Polling-blue.svg?style=for-the-badge)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=patrickjcash&repository=rumpke-ha&category=integration)

A custom Home Assistant integration for Rumpke Waste & Recycling services, providing automatic tracking of pickup schedules, holiday delays, and service alerts for your area.

> **⚠️ BETA VERSION**
> This integration is currently in **beta testing**. Features may change and bugs may exist. Please report issues on [GitHub](https://github.com/patrickjcash/rumpke-ha/issues).

## Features

### Sensors
- **Next Pickup Date** - Shows your next scheduled garbage/recycling pickup date
  - Automatically factors in your normal service day
  - Applies holiday schedule delays (11 major holidays)
  - Integrates service alert delays (weather, equipment issues)
  - Auto-detects your county for location-specific alerts
  - Updates every 12 hours

### Sensor Attributes
All sensors include detailed attributes for automations and dashboards:
- `service_day` - Your configured weekly pickup day
- `zip_code` - Service area zip code
- `county` - Auto-detected county name
- `state` - Auto-detected state
- `days_until_pickup` - Days until next pickup
- `pickup_date` - Formatted pickup date string
- `service_alert` - Active alert type (if any)
- `service_alert_text` - Full alert message
- `last_update` - Last data refresh timestamp

## Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the **three dots** (⋮) in the top right → **Custom repositories**
3. Add repository:
   - **Repository**: `https://github.com/patrickjcash/rumpke-ha`
   - **Category**: `Integration`
4. Click **Add**
5. Search for "**Rumpke**" in HACS
6. Click **Download** and select the latest version
7. **Restart Home Assistant**
8. Go to **Settings** → **Devices & Services** → **Add Integration**
9. Search for "**Rumpke**" and configure

### Manual Installation

1. Download the [latest release](https://github.com/patrickjcash/rumpke-ha/releases)
2. Copy the `custom_components/rumpke` folder to your Home Assistant `config/custom_components` directory
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services

## Configuration

The integration requires two pieces of information:

1. **Zip Code** - Your service address zip code (validates against Rumpke service area)
2. **Service Day** - Your normal weekly pickup day (Monday-Sunday)

The integration will:
- Automatically determine your region (Columbus, Cincinnati, Cleveland, etc.)
- Auto-detect your county for service alert matching
- Fetch region-specific holiday schedules
- Monitor county-specific service disruptions

## Supported Service Areas

This integration supports all Rumpke service areas across:

- **Ohio**: Columbus, Cincinnati, Cleveland, Dayton, Greenville, Waverly, and surrounding counties
- **Kentucky**: Louisville, Bluegrass region, and surrounding counties
- **Indiana**: Louisville metro area
- **West Virginia**: Select counties
- **Illinois**: Select counties

Use the zip code lookup during setup to verify your area is supported.

## How It Works

### Data Sources

The integration pulls data from official Rumpke sources:

1. **Holiday Schedule**: Region-specific pages showing 11 observed holidays and their service impacts
2. **Service Alerts**: County-level disruption notices (weather delays, equipment issues, route changes)
3. **Region API**: Zip code to region mapping for schedule routing

### Update Schedule

- Polls Rumpke every **12 hours**
- Holiday schedules are cached and updated daily
- Service alerts are checked on each update cycle
- No API rate limiting or authentication required

### Calculation Logic

The sensor calculates your next pickup date by:

1. Starting with your configured service day (e.g., Thursday)
2. Finding the next occurrence of that day (including today)
3. Applying any active service alert delays for your county
4. Applying any holiday delays for that week
5. Returning the final calculated pickup date

## Automation Examples

### Reminder Notification

Send a notification the evening before pickup:

```yaml
automation:
  - alias: "Trash Reminder"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.rumpke_next_pickup', 'days_until_pickup') == 1 }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Trash pickup tomorrow! Put bins out tonight."
```

### Service Alert Detection

Get notified when there's a service disruption:

```yaml
automation:
  - alias: "Rumpke Service Alert"
    trigger:
      - platform: state
        entity_id: sensor.rumpke_next_pickup
        attribute: service_alert
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.rumpke_next_pickup', 'service_alert') != None }}"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Rumpke Alert: {{ state_attr('sensor.rumpke_next_pickup', 'service_alert_text') }}
```

## Known Issues & Limitations

- Service alert parsing currently only detects "one-day delay" patterns
- Multi-day service disruptions may not calculate perfectly
- Holiday exceptions (e.g., "Lithopolis residents") are parsed but not applied to calculations
- Integration naming shows region instead of city
- Config flow labels show technical field names

See [Issues](https://github.com/patrickjcash/rumpke-ha/issues) for active bug reports and feature requests.

## Roadmap

See [FUTURE_ENHANCEMENTS.md](docs/FUTURE_ENHANCEMENTS.md) for planned features including:

- Binary sensors for holiday/alert detection
- Calendar integration
- Multi-waste type support (trash, recycling, yard waste)
- Historical tracking
- Enhanced alert parsing

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For bugs or feature requests, please [open an issue](https://github.com/patrickjcash/rumpke-ha/issues).

## Credits

- **Developer**: [@patrickjcash](https://github.com/patrickjcash)
- **Data Source**: [Rumpke Waste & Recycling](https://www.rumpke.com)

## Disclaimer

This is an **unofficial integration** and is not affiliated with, endorsed by, or supported by Rumpke Waste & Recycling. Use at your own risk.

The integration scrapes publicly available data from Rumpke's website. If Rumpke changes their website structure or policies, this integration may stop working without notice.

**Always verify pickup schedules** with official Rumpke communications. Do not rely solely on this integration for time-sensitive waste disposal needs.

## License

MIT License - see [LICENSE](LICENSE) file for details.
