# BlenderBeat — AI Assistant Onboarding & Architecture Guide

Welcome! This document provides an immediate, end-to-end understanding of **BlenderBeat**, its architectural pipeline, presets, Blender 5.x engine requirements, and conventions so any AI agent or developer can navigate, modify, or extend the codebase immediately.

---

## 1. High-Level Overview

- **Project**: BlenderBeat — Audio-Reactive Procedural VJ & Visual Engine for Blender 5.x.
- **Language & Runtime**: Python 3.11+ / Blender 5.2 LTS Python environment.
- **Core Purpose**: Loads audio (WAV, MP3, etc.), runs fast signal analysis (BPM, onset, sub-bass, bass, mid, high, spectral centroid), creates procedural 3D visual setups via **Geometry Nodes**, and drives parameters (scale, rotation, light emission, camera shake, zoom punch) dynamically synced to the beat.
- **Addon Path in Blender**: `C:\Users\itsha\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\blenderbeat` (synced via robocopy/symlink).

---

## 2. Directory Structure & Key Components

```
BLENDERBEAT PLUGIN/
├── blenderbeat/
│   ├── __init__.py           # Addon metadata (bl_info), registration entry points
│   ├── properties.py         # bpy.types.PropertyGroup definitions (preset choices, sliders, audio mappings)
│   ├── panels.py             # View3D sidebar UI panels ('PT')
│   ├── operators.py          # bpy.types.Operator actions (load audio, generate visualizer, bake animation)
│   ├── audio/                # Audio analysis subsystem
│   │   ├── analyzer.py       # Analysis orchestrator (AnalysisResult)
│   │   ├── loader.py         # Audio file loading & normalization
│   │   ├── frequency.py      # FFT frequency band extraction (sub-bass, bass, mid, high)
│   │   ├── beat_detection.py # BPM, downbeats, onset detection
│   │   └── stems.py          # Demucs / Spleeter optional stem separation
│   ├── animation/            # Mapping and baking subsystem
│   │   ├── drivers.py        # Driver helpers & expressions connecting custom props
│   │   ├── mapping.py        # Remapping curves, spring dynamics (stiffness, damping)
│   │   └── baking.py         # Keyframing animation curves onto Blender objects & F-Curves
│   ├── visual/               # Geometry & visual generation utilities
│   │   ├── generator.py      # Visualizer scene generator dispatcher
│   │   ├── geometry.py       # Mesh construction & visualizer root object setup
│   │   ├── lighting.py       # EEVEE lighting setup & Compositor Fog Glow bloom
│   │   └── camera.py         # Camera setup & audio-reactive zoom punch drivers
│   └── presets/              # Procedural visual presets (Inherit from BasePreset)
│       ├── base.py           # BasePreset abstract class & PresetRegistry
│       ├── black_hole_tunnel/# Flagship Preset 1: Infinite Black Hole Tunnel
│       ├── cosmic_blossom/   # Flagship Preset 2: Cosmic Blossom
│       ├── light_grid/       # Flagship Preset 3: Infinite Light Grid (Square LED Corridor)
│       │   ├── preset.py     # InfiniteLightGridPreset definition & lifecycle
│       │   ├── master_frame.py   # Procedural square LED frame mesh + chrome corner joints
│       │   ├── grid_nodes.py     # Geometry Nodes corridor instancer, twist & traveling wave
│       │   ├── grid_materials.py # Shader: per-pipe stochastic beat selection + Aura Sync SPECTRUM
│       │   ├── grid_camera.py    # Wide 20mm camera flythrough with CCW Z-rotation
│       │   └── grid_terminus.py  # Atmospheric horizon vanishing point glow
│       └── signal_drift/    # Flagship Preset 4: Signal Drift (Digital Apparition)
│           ├── preset.py         # SignalDriftPreset definition & lifecycle
│           ├── mannequin.py      # Authentic human mesh asset loader (Human_Base_Full)
│           ├── drift_nodes.py    # Self-contained multi-scale GN (Poisson dots, Z-aligned bars, radial streaks)
│           ├── drift_materials.py # Dual-tone Violet-Cyan shader + CRT scan-lines + white-hot kick
│           └── drift_camera.py   # 360° orbit camera with zoom punch
```

---

## 3. The Preset Architecture (`BasePreset` & `PresetRegistry`)

All visual presets subclass `blenderbeat.presets.base.BasePreset` and register via `@PresetRegistry.register`:

```python
class MyPreset(BasePreset):
    id = "MY_PRESET_ID"
    name = "My Preset Name"
    description = "..."
    category = "Sci-Fi"
    collection_name = "BB_My_Collection"

    def get_mappings(self) -> MappingPreset:
        # Define default audio -> visual bindings (e.g. kick -> camera_zoom)
        ...

    def create(self, context, analysis, settings) -> Dict[str, Any]:
        # Generates procedural meshes, Geometry Nodes, materials, lighting, camera
        ...
```

Preset choices in UI dropdowns (`blenderbeat/properties.py`) dynamically list all presets from `PresetRegistry.list_presets()`.

---

## 4. Blender 5.2 LTS Engine Quirks & Critical Rules

1. **EEVEE-Next Real-time Bloom**:
   - In Blender 5.x, `scene.eevee.use_bloom` does **not** exist.
   - Bloom is handled by the **Compositor Fog Glow** node group:
     `CompositorNodeRLayers -> CompositorNodeGlare(glare_type='FOG_GLOW') -> NodeGroupOutput`.
   - Real-time viewport display requires: `space.shading.use_compositor = 'ALWAYS'`.
   - Configured automatically in `blenderbeat.visual.lighting.setup_realtime_glow_compositor()`.

2. **Geometry Nodes Instance Attribute Preservation**:
   - Mesh face/vertex attributes on master meshes can get dropped during `GeometryNodeRealizeInstances`.
   - When per-pipe / per-quadrant variation is required on realized instances, compute the quadrant index directly inside the shader using local object space `ShaderNodeTexCoord.Object -> atan2(Y, X)`.

3. **Continuous Rotation**:
   - In Blender, positive Z rotation (`rotation_euler.z`) is counter-clockwise (CCW) when looking forward down the -Z axis.
   - For seamless looping, camera or corridor rotations are keyframed over `t = frame / total_frames` using `rot_z = t * 2.0 * math.pi`.

---

## 5. Active Presets Summary

| Preset ID | Name | Core Concept | Audio Reactivity Highlights |
| :--- | :--- | :--- | :--- |
| `INFINITE_BLACK_HOLE` | **Infinite Black Hole Tunnel** | 55 dark cylindrical hulls, 8 chrome girder rails, zero-albedo event horizon | Z-traveling shockwave wave, random white-hot accent flare, kick zoom punch |
| `COSMIC_BLOSSOM` | **Cosmic Blossom** | Tiered sacred geometry lotus petals, stamen cluster, golden spiral distribution | Bass petal expansion, mid twist, transient petal flutter |
| `INFINITE_LIGHT_GRID` | **Infinite Light Grid** | Deep square-framed LED corridor with chrome corner joints & atmospheric terminus | **Per-pipe stochastic beat ignition** (1, 2, 3, or all 4 pipes ignite randomly on kick/beat), occasional full-frame burst, CCW rotating 20mm camera flythrough |
| `NEON_SIGNAL_CITY` | **Neon Signal City** | Futuristic cyberpunk skyscraper corridor with vertical light strips, wet reflective street, depth wave propagation, and stable cinematic camera | Traveling kick wave down Y corridor, bass ambient breathing, zero camera shake, cyan/teal & magenta palette |

---

## 6. How to Test & Live-Verify with Blender

If Blender is running with an open socket server (default port `9876`), you can execute live Python commands directly:

```python
import socket, json
s = socket.socket()
s.connect(('127.0.0.1', 9876))
code = "import bpy; print('Blender version:', bpy.app.version)"
payload = json.dumps({'type': 'execute_code', 'params': {'code': code}})
s.sendall(payload.encode('utf-8'))
print(s.recv(4096).decode('utf-8'))
s.close()
```

To sync code changes into the active Blender addon folder:
```powershell
robocopy "blenderbeat" "C:\Users\itsha\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\blenderbeat" /E /NFL /NDL /NJH /NJS
```
