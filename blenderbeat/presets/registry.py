"""
BlenderBeat — Preset Registry.

Maintains all available visual presets and provides factory methods
to retrieve, list, and register presets dynamically.
"""

from typing import Dict, List, Optional, Type
from .base import BasePreset


class PresetRegistry:
    """Registry maintaining all available visualizer presets."""
    _presets: Dict[str, Type[BasePreset]] = {}

    @classmethod
    def register(cls, preset_cls: Type[BasePreset]):
        """Register a new visualizer preset class."""
        cls._presets[preset_cls.id] = preset_cls
        print(f"[BlenderBeat] Registered visual preset: {preset_cls.name} ({preset_cls.id})")

    @classmethod
    def get(cls, preset_id: str) -> Optional[BasePreset]:
        """Instantiate and return a preset by its identifier."""
        preset_cls = cls._presets.get(preset_id)
        if preset_cls:
            return preset_cls()
        return None

    @classmethod
    def get_by_name(cls, name: str) -> Optional[BasePreset]:
        """Find preset by user-facing name."""
        for p_cls in cls._presets.values():
            if p_cls.name == name:
                return p_cls()
        return None

    @classmethod
    def list_all(cls) -> List[Type[BasePreset]]:
        """List all registered preset classes."""
        return list(cls._presets.values())

    @classmethod
    def get_enum_items(cls) -> List[tuple]:
        """Generate items list for bpy.props.EnumProperty."""
        items = []
        for p_id, p_cls in cls._presets.items():
            items.append((p_id, p_cls.name, p_cls.description))
        return items
