from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import (
    UnitOfPower,
)

DOMAIN = "iammeter_wpc"
DEFAULT_NAME = "IamMeterWpc"
DEFAULT_SCAN_INTERVAL = 2
CONF_IamMeter_HUB = "iammeter_hub"
ATTR_MANUFACTURER = "IamMeter"
SET_POWER_NUMBER = "SetPower"
MAX_POWER_NUMBER = "MaxPower"
MAX_POWER_LIMIT = 4000

@dataclass
class IamMeterWpcSensorEntityDescription(SensorEntityDescription):
    """A class that describes IamMeter WPC sensor entities."""

SENSOR_TYPES: dict[str, list[IamMeterWpcSensorEntityDescription]] = {
	"max_power": IamMeterWpcSensorEntityDescription(
    	name="maxPower",
    	key="maxPower",
    	native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
	"set_power": IamMeterWpcSensorEntityDescription(
    	name="setPower",
    	key="setPower",
    	native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}
