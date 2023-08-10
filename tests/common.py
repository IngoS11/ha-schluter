"""Test the helper method for writing tests."""

from homeassistant import config_entries

import homeassistant.util.uuid as uuid_util


class MockConfigEntry(config_entries.ConfigEntry):
    """Helper for creating config entries that adds some defaults."""

    def __init__(
        self,
        *,
        domain="test",
        data=None,
        version=1,
        entry_id=None,
        source=config_entries.SOURCE_USER,
        title="Mock Title",
        state=None,
        options={},
        pref_disable_new_entities=None,
        pref_disable_polling=None,
        unique_id=None,
        disabled_by=None,
        reason=None,
    ):
        """Initialize a mock config entry."""
        kwargs = {
            "entry_id": entry_id or uuid_util.random_uuid_hex(),
            "domain": domain,
            "data": data or {},
            "pref_disable_new_entities": pref_disable_new_entities,
            "pref_disable_polling": pref_disable_polling,
            "options": options,
            "version": version,
            "title": title,
            "unique_id": unique_id,
            "disabled_by": disabled_by,
        }
        if source is not None:
            kwargs["source"] = source
        if state is not None:
            kwargs["state"] = state
        super().__init__(**kwargs)
        if reason is not None:
            self.reason = reason

    def add_to_hass(self, hass):
        """Test helper to add entry to hass."""
        hass.config_entries._entries[self.entry_id] = self
        hass.config_entries._domain_index.setdefault(self.domain, []).append(
            self.entry_id
        )

    def add_to_manager(self, manager):
        """Test helper to add entry to entry manager."""
        manager._entries[self.entry_id] = self
        manager._domain_index.setdefault(self.domain, []).append(self.entry_id)
