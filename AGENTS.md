# BlenderBeat — Agent Instructions & Quick Start

Whenever this project is opened or resumed in a new session/agent, read `PROJECT_CONTEXT.md` immediately.

### Quick Summary:
- **Project**: BlenderBeat — Audio-reactive VJ & Procedural Visual Engine for Blender 5.x.
- **Architecture**: Modular presets under `blenderbeat/presets/` inheriting from `BasePreset` and registered with `@PresetRegistry.register`.
- **Active Flagship Presets**:
  1. `INFINITE_BLACK_HOLE`: Infinite Black Hole Tunnel.
  2. `COSMIC_BLOSSOM`: Cosmic Blossom sacred geometry audio flower.
  3. `INFINITE_LIGHT_GRID`: Infinite Light Grid deep square corridor with:
     - **Per-pipe stochastic beat reactivity**: Each square frame has 4 pipes. Transients and kicks trigger stochastic subsets (1, 2, 3, or all 4 pipes ignite) or occasional full-frame bursts.
     - **Counter-Clockwise (CCW) Camera Roll**: Continuous 360° rotation around Z-axis while traveling forward.
     - **Aura Sync SPECTRUM**: Multi-layer chromatic gradient with real-time EEVEE-Next Compositor Fog Glow bloom (`space.shading.use_compositor = 'ALWAYS'`).
  4. `NEON_SIGNAL_CITY`: Futuristic cyberpunk skyscraper corridor with:
     - **Zero Camera Shake**: Stable cinematic eye-level camera looking down the corridor.
     - **Vertical LED Columns**: Hundreds of vertical light strips with dark housings and emissive cores.
     - **Kick Depth Propagation**: Lighting wave travels from foreground to deep vanishing point along Y axis.
     - **Wet Reflective Street**: Concrete/asphalt ground with puddle variation reflecting the illuminated city.
  5. `PULSE_TUNNEL`: Futuristic circular LED tunnel with:
     - **Zero Camera Reactivity**: Constant-speed forward camera, NO shake/zoom/kick/pulse.
     - **Concentric Rings**: 80 rings × 32 LED segments each, instanced via Geometry Nodes.
     - **Traveling Illumination Wave**: Beat-driven shockwave races through the tunnel on each kick.
     - **Per-Segment Stochastic ON/OFF**: Hash-based probability gate determines which segments ignite per beat.
     - **Dual-Tone Gradient**: Cyan ↔ Magenta with white-hot transient peaks.
- **Engine Rules**: Blender 5.2 uses Compositor Fog Glow (`CompositorNodeGlare`) instead of legacy bloom.
