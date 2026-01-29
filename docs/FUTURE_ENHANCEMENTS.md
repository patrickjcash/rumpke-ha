# Future Enhancements

This document tracks potential improvements and features for the Rumpke Home Assistant integration.

## High Priority

### 1. Additional Sensors

**Binary Sensors for Alerts:**
- `binary_sensor.rumpke_holiday_delay` - Indicates if upcoming pickup is affected by a holiday
- `binary_sensor.rumpke_service_alert` - Indicates if there's an active service alert for your area
- `binary_sensor.rumpke_pickup_today` - Indicates if pickup is scheduled for today

**Attributes to Add:**
- Next 3-4 pickup dates (not just the next one)
- Affected holiday name (if applicable)
- Days since last update
- Alert severity/type

### 2. Calendar Integration

**Home Assistant Calendar Entity:**
- Create a calendar entity that shows all upcoming pickup dates
- Include holiday delays in calendar
- Mark affected dates with service alert icons
- Allow users to view pickup schedule in HA Calendar view
- Reference: Look at how [Waste Collection Schedule](https://github.com/mampfes/hacs_waste_collection_schedule) implements calendar

**Implementation Notes:**
- Use `homeassistant.components.calendar` platform
- Generate events for next 6-12 months of pickups
- Update calendar when delays occur

### 3. Notifications/Automations Support

**Attributes for Automation:**
- `pickup_tomorrow` boolean attribute
- `pickup_in_hours` (time until pickup)
- `alert_active` boolean

**Example Use Cases:**
- Send notification evening before pickup
- Turn on porch light on pickup morning
- Reminder if bins not placed out (with door sensor)

## Medium Priority

### 4. Multi-Waste Type Support

Some Rumpke customers may have:
- Regular trash pickup
- Recycling pickup (different day)
- Yard waste pickup (seasonal)

**Implementation:**
- Allow configuring multiple pickup types
- Separate sensors for each type
- Handle different schedules per type

### 5. Enhanced Service Alert Parsing

**Current Limitations:**
- Only detects "one-day delay" pattern
- Doesn't parse specific affected days (e.g., "No service Mon-Wed")
- Doesn't extract makeup day information

**Improvements:**
- Parse "no service on [specific days]" patterns
- Extract makeup collection day info
- Handle "weather permitting" / "attempting service" alerts
- Parse date ranges more intelligently

### 6. Historical Data Tracking

- Track actual pickup dates (vs scheduled)
- Missed pickup tracking
- Statistics on delays by month/season
- Integration with HA's built-in statistics platform

## Low Priority

### 7. Recycling Week Indicator

Some areas have bi-weekly recycling:
- Track recycling weeks
- Add recycling_week boolean attribute
- Allow manual week override

### 8. Service Area Map

- Show Rumpke service area on map
- Indicate user's location
- Show regional boundaries

### 9. Advanced Configuration

- Custom delay rules (beyond Rumpke's defaults)
- Manual override for specific dates
- Integration with personal calendar for vacation holds
- Custom notification preferences

### 10. Multi-Language Support

- Spanish translations (common in service areas)
- Localization for date formats

## Technical Improvements

### Code Quality
- Add comprehensive unit tests
- Add integration tests
- Improve error handling for edge cases
- Add retry logic for API failures
- Implement caching for rarely-changing data (holidays)

### Performance
- Cache zip-to-county lookups
- Reduce redundant API calls
- Optimize HTML parsing

### Documentation
- Add troubleshooting guide
- Create wiki with examples
- Document common automations
- Add screenshots for README

## Community Requests

_This section will be populated based on user feedback and GitHub issues._

---

**Contributing:** If you'd like to implement any of these features, please open an issue first to discuss the approach!

**Last Updated:** January 29, 2026
