"""The Iammeter Wpc Integration."""
import asyncio
import logging
import async_timeout
from datetime import timedelta
from typing import Optional
from requests.exceptions import Timeout

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from iammeterWpc.api import IammeterWpcAPI


from .const import (
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

IAMMETER_PWC_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({cv.slug: IAMMETER_PWC_SCHEMA})}, extra=vol.ALLOW_EXTRA
)

PLATFORMS = [Platform.NUMBER, Platform.SENSOR,]
SCAN_INTERVAL = timedelta(seconds=4)


async def async_setup(hass, config):
    """Set up the IamMeter modbus component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("async_setup_entry")
    """Set up a IamMeter mobus."""
    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = IammeterWpcHub(hass, name, host)
    """Register the hub."""
    hass.data[DOMAIN][name] = {"hub": hub}
    
    coordinator = IamMeterWpcData(hass, hub)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True

async def async_unload_entry(hass, entry):
    """Unload IamMeterWpc entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    hass.data[DOMAIN].pop(entry.data[CONF_NAME])
    return True


class IammeterWpcHub:
    def __init__(
        self,
        hass,
        name,
        host,
    ):
        """Initialize the hub."""
        self._hass = hass
        self._client = IammeterWpcAPI(host)
        self._name = name
        self._serial_number = None
        self._unsub_interval_method = None
        self._sensors = []
        self.data = {}

    async def async_refresh_wpc_data(self, _now: Optional[int] = None):
        """Time to update."""
        try:
            async with async_timeout.timeout(2):
                update_result =await self.read_monitor_data()
                self._serial_number = update_result["SN"]
                self.data["maxPower"] = update_result["maxPower"]
                self.data["setPower"] = update_result["setPower"]
                return self.data
        except (OSError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name
    
    def read_monitor_data(self):
        """Read monitor data."""
        try:
            return self._client.get_monitor_data()
        except (OSError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API")

    def async_set_max_power(self, value:int):
        try:
            return self._client.set_wpc_adv(max_power=value)
        except (OSError, TimeoutError) as err:
            # _LOGGER.error("Reading data failed! IamMeter is offline.")
            raise UpdateFailed(f"Error communicating with API")
        
    def async_set_power(self, value:int):
        try:
            return self._client.set_power(value)
        except (OSError, TimeoutError) as err:
            # _LOGGER.error("Reading data failed! IamMeter is offline.")
            raise UpdateFailed(f"Error communicating with API")


class IamMeterWpcData(DataUpdateCoordinator):
    """My custom coordinator."""
    def __init__(self, hass, my_api:IammeterWpcHub):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="IamMeterWpc Data",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.api = my_api

    async def _async_update_data(self):
        #Fetch data from API endpoint.
        return await self.api.async_refresh_wpc_data()