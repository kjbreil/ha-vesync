from __future__ import annotations


from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyvesync.vesyncfan import VeSyncHumid200300S

from .common import VeSyncDevice
from .const import DOMAIN, VS_DISCOVERY, VS_FANS


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
        if isinstance(dev, VeSyncHumid200300S):
            entities.append(VeSyncHumidifierBinarySensors(dev))

        else:
            _LOGGER.warning(
                "%s - Unknown device type - %s",
                dev.device_name,
                dev.device_type,
            )
            continue

    async_add_entities(entities, update_before_add=True)


# class VeSyncHumidifierBinarySensors(VeSyncDevice, BinarySensorEntity):
class VeSyncHumidifierBinarySensors(VeSyncDevice, BinarySensorEntity):
    """Representation of a VeSync Humidifier Mist Speed as Fan."""

    def __init__(self, device) -> None:
        """Initialize the VeSync device."""
        super().__init__(device)
        self._attr_unique_id = f"{super().unique_id}-waterlacks"
        self._attr_name = f"{super().name} water lacks"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.device.water_lacks
