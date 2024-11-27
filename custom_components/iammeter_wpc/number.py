"""Representation of a switchMultilevel."""
from collections.abc import Callable, Coroutine
from typing import Any
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    UpdateFailed,
)
from .const import DOMAIN, SET_POWER_NUMBER, MAX_POWER_NUMBER, MAX_POWER_LIMIT
from . import IammeterWpcHub, IamMeterWpcData
from requests.exceptions import Timeout

@dataclass(frozen=True, kw_only=True)
class WpcNumberEntityDescription(NumberEntityDescription):
    """Class to describe a SleepIQ number entity."""
    set_value_fn: Callable[[Any, int], Coroutine[None, None, None]]


async def _async_set_power_val_fn(
        hub: IammeterWpcHub, val: int
) -> None:
    try:
        await hub.async_set_power(val)
    except (OSError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
    
async def _async_set_max_val_fn(
    hub: IammeterWpcHub, val: int
) -> None:
    try:
        await hub.async_set_max_power(val)
    except (OSError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

IAMMETER_WPC_NUMBER_DESCRIPTIONS: dict[str, WpcNumberEntityDescription] = {
    SET_POWER_NUMBER: WpcNumberEntityDescription(
        key=SET_POWER_NUMBER,
        native_min_value=0,
        native_max_value=MAX_POWER_LIMIT,
        native_step=100,
        name=SET_POWER_NUMBER,
        set_value_fn=_async_set_power_val_fn,
    ),
    MAX_POWER_NUMBER: WpcNumberEntityDescription(
        key=MAX_POWER_NUMBER,
        native_min_value=0,
        native_max_value=MAX_POWER_LIMIT,
        native_step=100,
        name=MAX_POWER_NUMBER,
        set_value_fn=_async_set_max_val_fn,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    entities = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities.append(
        WpcNumberEntity(
            coordinator,
            IAMMETER_WPC_NUMBER_DESCRIPTIONS[SET_POWER_NUMBER],
        )
    )
    entities.append(
        WpcNumberEntity(
            coordinator,
            IAMMETER_WPC_NUMBER_DESCRIPTIONS[MAX_POWER_NUMBER],
        )
    )
    async_add_entities(entities)


class WpcNumberEntity(CoordinatorEntity,NumberEntity):
    entity_description: WpcNumberEntityDescription
    _attr_icon = "mdi:flash"
    def __init__(
        self,
        coordinator:IamMeterWpcData,
        description: WpcNumberEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._hub = coordinator.api
        self.entity_description = description
        self._attr_name = f"{description.key}"
        self._attr_unique_id: str = (
            f"{description.key}_{self._hub._serial_number}"
        )

    async def async_set_native_value(self, value: int) -> None:
        """Update the current value."""
        await self.entity_description.set_value_fn(self._hub, int(value))
        self._attr_native_value = value
        self.async_write_ha_state()
