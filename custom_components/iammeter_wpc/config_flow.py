import logging
from urllib.parse import urlparse
import ipaddress
import re
from requests.exceptions import Timeout

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (CONF_NAME, CONF_HOST)
from homeassistant.core import HomeAssistant, callback

from iammeterWpc.api import IammeterWpcAPI

_LOGGER = logging.getLogger(__name__)

from .const import (
	DEFAULT_NAME,
	DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
    }
)


def host_valid(host):
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version == (4 or 6):
            return True
    except ValueError:
        disallowed = re.compile(r"[^a-zA-Z\d\-]")
        return all(x and not disallowed.search(x) for x in host.split("."))


@callback
def iammeter_wpc_entries(hass: HomeAssistant):
    """Return the hosts already configured."""
    return set(
        entry.data[CONF_NAME] for entry in hass.config_entries.async_entries(DOMAIN)
    )


class IammeterWpcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """IammeterWpc configflow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    _serial_number = ""
    _host = None

    def _host_in_configuration_exists(self, host) -> bool:
        """Return True if host exists in configuration."""
        if host in iammeter_wpc_entries(self.hass):
            return True
        return False

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._name = user_input[CONF_NAME]
            try:
                await self._get_wpc_serial_number(raise_on_progress=False)
            except (OSError, Timeout):
                errors = {CONF_HOST: "cannot_connect"}
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): str,
                            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str,
                        }
                    ),
                    errors=errors
                )
            return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        elif hasattr(self, 'discovered_conf'):
                user_input = {}
                user_input[CONF_NAME] = self.discovered_conf[CONF_NAME]
                user_input[CONF_HOST] = self.discovered_conf[CONF_HOST]
        else:
            user_input= {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): str,
                    vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): str,
                }
            ),
            errors=errors
        )
    
    async def _get_wpc_serial_number(self, raise_on_progress: bool = True) -> None:
        """Get device information from an Elgato Light device."""
        self._client = IammeterWpcAPI(self._host)
        info = await self._client.get_monitor_data()
        await self.async_set_unique_id(
            info["SN"], raise_on_progress=raise_on_progress
        )
        self._abort_if_unique_id_configured(
            updates={CONF_NAME: self._name, CONF_HOST: self._host}
        )
        self._serial_number = info["SN"]