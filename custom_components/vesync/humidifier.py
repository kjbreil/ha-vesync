"""Support for VeSync fans."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.humidifier import (
    HumidifierEntity,
    HumidifierEntityFeature,
    MODE_AUTO,
    MODE_NORMAL,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyvesync.vesyncfan import VeSyncHumid200300S

from .common import VeSyncDevice
from .const import (
    DOMAIN,
    SKU_TO_BASE_DEVICE,
    VS_DISCOVERY,
    VS_FANS,
)


_LOGGER = logging.getLogger(__name__)

DEV_TYPE_TO_HA = {
    "LV600S": "humidifier",
}

FAN_MODE_AUTO = "auto"
FAN_MODE_SLEEP = "sleep"

PRESET_MODES = {
    "LV-PUR131S": [FAN_MODE_AUTO, FAN_MODE_SLEEP],
    "Core200S": [FAN_MODE_SLEEP],
    "Core300S": [FAN_MODE_AUTO, FAN_MODE_SLEEP],
    "Core400S": [FAN_MODE_AUTO, FAN_MODE_SLEEP],
    "Core600S": [FAN_MODE_AUTO, FAN_MODE_SLEEP],
}
SPEED_RANGE = {  # off is not included
    "LV-PUR131S": (1, 3),
    "Core200S": (1, 3),
    "Core300S": (1, 3),
    "Core400S": (1, 4),
    "Core600S": (1, 4),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the VeSync fan platform."""

    @callback
    def discover(devices):
        """Add new devices to platform."""
        _setup_entities(devices, async_add_entities)

    config_entry.async_on_unload(
        async_dispatcher_connect(hass, VS_DISCOVERY.format(VS_FANS), discover)
    )

    _setup_entities(hass.data[DOMAIN][VS_FANS], async_add_entities)


@callback
def _setup_entities(devices, async_add_entities):
    """Check if device is online and add entity."""
    entities = []
    for dev in devices:
        # if (
        #     DEV_TYPE_TO_HA.get(SKU_TO_BASE_DEVICE.get(dev.device_type))
        #     == "humidifier"
        # ):
        #     entities.append(VeSyncHumidifierHA(dev))
        if isinstance(dev, VeSyncHumid200300S):
            entities.append(VeSyncHumidifierHA(dev))

    async_add_entities(entities, update_before_add=True)


class VeSyncHumidifierHA(VeSyncDevice, HumidifierEntity):
    """Representation of a VeSync humidifier."""

    _attr_supported_features = HumidifierEntityFeature.MODES

    def __init__(self, humidifier):
        """Initialize the VeSync humidifier device."""
        super().__init__(humidifier)
        self._attr_target_humidity = self.device.auto_humidity
        self._attr_max_humidity = 80
        self._attr_min_humidity = 40

    @property
    def available_modes(self) -> list[str] | None:
        """Return a list of available modes.

        Requires HumidifierEntityFeature.MODES.
        """
        available_modes = [
            MODE_AUTO,
            MODE_NORMAL,
        ]

        return available_modes

    @property
    def mode(self) -> str | None:
        """Return the current mode, e.g., home, auto, baby.

        Requires HumidifierEntityFeature.MODES.
        """
        if self.device.auto_enabled:
            return MODE_AUTO
        return MODE_NORMAL

    def set_mode(self, mode: str) -> None:
        """Set new mode."""
        if mode == MODE_AUTO:
            self.device.set_auto_mode()
        else:
            self.device.set_manual_mode()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the humidifier."""
        attr = {}

        if hasattr(self.device, "night_light"):
            attr["night_light"] = self.device.night_light

        if hasattr(self.device, "mist_mode"):
            attr["mode"] = self.device.mist_mode

        if hasattr(self.device, "warm_mist_enabled"):
            attr["warm_mist_enabled"] = self.device.warm_mist_enabled

        if hasattr(self.device, "auto_humidity"):
            attr["target_humidity"] = self.device.auto_humidity

        return attr

    @property
    def unique_info(self):
        """Return the ID of this fan."""
        return self.device.uuid

    @property
    def target_humidity(self) -> int | None:
        """Return the humidity we try to reach."""
        return self.device.auto_humidity

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self.device.enabled

    def set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        self.device.set_humidity(humidity)

    def turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        self.device.turn_on()

    def turn_off(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn the device off."""
        self.device.turn_off()
