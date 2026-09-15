"""
BlenderBeat — Abstract Base Preset.

Defines the contract that every procedural visual preset must fulfill.
Enables modular, self-contained presets that can be registered,
instantiated, configured, and cleaned up independently.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import bpy

from ..audio.analyzer import AnalysisResult
from ..animation.mapping import MappingPreset


class BasePreset(ABC):
    """Abstract base class for all BlenderBeat visualizer presets."""

    # Unique identifier (e.g. 'INFINITE_BLACK_HOLE_TUNNEL')
    id: str = "BASE"
    # User-facing name
    name: str = "Base Preset"
    description: str = ""
    category: str = "Abstract"
    # Dedicated collection name to quarantine all generated objects
    collection_name: str = "BB_Visualizer_Collection"

    @abstractmethod
    def get_mappings(self) -> MappingPreset:
        """Return default audio-to-visual mappings for this preset."""
        pass

    @abstractmethod
    def create(
        self,
        context: bpy.types.Context,
        analysis: AnalysisResult,
        settings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate the complete visual scene.
        Must create its objects inside self.collection_name.
        Returns dictionary of created objects, materials, and metadata.
        """
        pass

    def cleanup(self, context: bpy.types.Context):
        """
        Safely remove only objects and collections belonging to this preset.
        Never touches user objects outside its dedicated collection.
        """
        col = bpy.data.collections.get(self.collection_name)
        if col:
            # Remove all objects in collection
            for obj in list(col.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            # Remove collection
            bpy.data.collections.remove(col)

        # Remove objects with BB_ prefix
        for obj in list(bpy.data.objects):
            if obj.name.startswith("BB_"):
                bpy.data.objects.remove(obj, do_unlink=True)

    def get_collection(self) -> bpy.types.Collection:
        """Get or create the dedicated collection for this preset."""
        col = bpy.data.collections.get(self.collection_name)
        if col is None:
            col = bpy.data.collections.new(self.collection_name)
            bpy.context.scene.collection.children.link(col)
        return col
