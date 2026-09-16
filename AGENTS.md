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
  4. `SIGNAL_DRIFT`: Digital Apparition — spectral humanoid preserving authentic anatomical silhouette with:
     - **Authentic Human Asset**: `human_base.blend` loaded directly (head, facial contours, neck, torso, arms, hands, legs, boots).
     - **Multi-Scale Geometry Nodes**: Poisson disk surface sampling (~45,000 micro dots + ~12,000 delicate vertical scan bars aligned strictly to Z + dynamic audio streaks).
     - **Audio Explosion & Reconstruction**: Kick drives radial displacement from subject center; fragments return seamlessly to original anatomical coordinates.
     - **Dual-Tone Spectral Shader**: Deep Violet left (-X) to Electric Cyan right (+X) with white-hot core desaturation on kick impacts.
     - **360° Orbit Camera**: Smooth circular orbit with beat-reactive zoom punch.
- **Engine Rules**: Blender 5.2 uses Compositor Fog Glow (`CompositorNodeGlare`) instead of legacy bloom.
