from homeassistant.const import CONF_NAME
from homeassistant.components.sensor import SensorEntity
import logging
from typing import Optional, Dict, Any

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
import homeassistant.util.dt as dt_util
from . import IamMeterWpcData

from .const import ATTR_MANUFACTURER, DOMAIN,  IamMeterWpcSensorEntityDescription,SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)



async def async_setup_entry(hass, entry, async_add_entities):
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_info = {
        "identifiers": {(DOMAIN, hub_name)},
        "name": hub_name,
        "manufacturer": ATTR_MANUFACTURER,
    }

    entities = []
    for sensor_description in SENSOR_TYPES.values():
            sensor = IamMeterWpcSensor(
                coordinator,
                hub_name,
                hub,
                device_info,
                sensor_description,
            )
            entities.append(sensor)
    
    async_add_entities(entities)
    return True


class IamMeterWpcSensor(CoordinatorEntity, SensorEntity):
    """Representation of an IamMeter Wpc sensor."""
    def __init__(
        self,
        coordinator:IamMeterWpcData,
        platform_name,
        hub,
        device_info,
        description: IamMeterWpcSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._platform_name = platform_name
        self._attr_device_info = device_info
        self._hub = hub
        self.entity_description: IamMeterWpcSensorEntityDescription = description

    @property
    def name(self):
        """Return the name."""
        return f"{self._platform_name} {self.entity_description.name}"

    @property
    def unique_id(self) -> Optional[str]:
        return f"{self._platform_name}_{self.entity_description.key}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if(self.coordinator.data):
            return (
                self.coordinator.data.get(
                    self.entity_description.key, None
                )
            )
