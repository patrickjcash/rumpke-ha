"""Constants for the Rumpke Waste Collection integration."""

DOMAIN = "rumpke"

# Configuration keys
CONF_ZIP_CODE = "zip_code"
CONF_SERVICE_DAY = "service_day"

# API endpoints
API_BASE_URL = "https://www.rumpke.com"
API_GET_REGION = "/holiday-schedule/get-region"

# Region to schedule page mapping
REGION_SCHEDULE_MAP = {
    "Bluegrass": "/schedule/wbl",
    "Cincinnati": "/schedule/wci",
    "Cleveland": "/schedule/ecl",
    "Columbus": "/schedule/eco",
    "Dayton": "/schedule/eda",
    "Greenville": "/schedule/wgr",
    "Louisville": "/schedule/wlo",
    "Waverly": "/schedule/ewa",
}

# Service alerts URL
SERVICE_ALERTS_URL = "https://www.rumpke.com/service-alerts"

# Update intervals (in minutes)
SCAN_INTERVAL_HOURS = 12
