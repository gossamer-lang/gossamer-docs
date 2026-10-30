# Rendering

The Rust toolkit records each window's paint into a primitive scene. Geometry,
coverage masks, colors, images, clip and opacity are data; painting no longer
requires allocating and copying a full canvas through `PaintCx` on every frame.
The session retains one pixel buffer per window. Scene comparison damages both
old and new bounds for changed, inserted, removed and reordered operations.
Damage is clipped, merged and capped at 32 regions. Unchanged scenes perform
no rasterization or presentation. Resize invalidates the entire window.

The software reference replays intersecting commands into 128-pixel raster tiles
and copies only damaged rows into the persistent canvas and SDL window surface.
Tile keys include paint content, clip, opacity, position and ordered revisions.
Layer reuse uses LRU eviction; old revisions at a tile position are replaced.
Transformed custom-widget layers also cache their isolated raster by recorded
subtree revision, transform, clip and opacity before compositing. Cache entries
verify content equality as well as the revision hash. This per-window subtree
cache may use up to half the software-layer budget; tiles use the remainder,
including unused subtree space. Source descriptions and isolated pixels are
accounted together, and unchanged subtrees reuse their raster.
Low-memory events purge scenes, raster layers and GPU resources. Occluded windows
skip painting and pause caret/animation-frame timers until exposure or restore.
Application timers retain their own semantics.

## GPU backend decision

The first GPU backend is SDL's accelerated 2D renderer. It shares the pinned SDL
build already required for windows, avoiding another graphics dependency or a
second platform connection. SDL selects D3D12/D3D11, Metal, OpenGL/GLES or Vulkan
from the compiled drivers available on the platform; software SDL renderers are
excluded. Linux verification exercises OpenGL on X11 and Wayland.

The GPU replays the recorded scene into a persistent target texture. Rectangles
use native GPU draws; paths, rounded shapes, images and glyph coverage use
revision-keyed texture layers, generated lazily in tiles of at most 64 KiB.
The GPU performs clipping, opacity and source-over composition. A window's swap
backbuffer is reconstructed from the target because its contents do not survive
a swap. Only damaged target regions are repainted. CPU reference pixels remain
available for fallback and validation.

Software rendering is the default on every display, without initializing a GPU.
`GUI_RENDERER=software` explicitly selects the same reference path.
`GUI_RENDERER=auto` opts into acceleration on real displays and software on the
headless offscreen driver; `gpu` requests acceleration but still falls back if initialization or drawing
fails. SDL's offscreen driver creates an EGL pbuffer without resizing it when
window dimensions change, so this compositor reports that driver unsupported
and uses software; GPU validation uses actual X11/Wayland display servers. A failed draw releases GPU objects and presents the complete reference
frame through the software surface. A later changed frame retries after a bounded
60-update cooldown; this does not add idle polling. `RenderReset` first presents a software frame and uses the same bounded retry;
application resume permits immediate recreation. Exposure repaints without
unnecessarily destroying the device.

Software comparisons against the existing screenshot goldens are exact. GPU
readbacks allow an absolute difference of at most 8 per 8-bit channel to cover
integer blend rounding and isolated-mask reconstruction across drivers. Readback
occurs before presentation, as [SDL requires](https://wiki.libsdl.org/SDL3/SDL_RenderReadPixels).
Tests require an actual accelerated backend rather than accepting fallback as a
GPU pass. GPU cache reuse, partial updates and reset/recreation are exercised.

## Subtrees and budgets

Custom widgets may return `DrawOp::Layer { ops, transform }`. `Transform` carries
translation and independent X/Y scales; negative scales reflect about the local
origin. Subtrees preserve nested clipping and opacity. Isolated layers use
premultiplied-color sampling to avoid dark transparent edges. Invalid transforms
or oversized isolated rasters return an explicit paint error.

Defaults per window are 32 MiB for retained scenes, 16 MiB for raster layers and
16 MiB for GPU primitive layers. Scene accounting includes command capacity and
owned payload bytes. Each layer cache accounts its pixel storage; GPU driver and
allocator overhead are outside these logical budgets. Persistent window pixels
and a GPU target are mandatory surfaces, each four bytes per pixel, rather than
cache entries. They resize with the window and are released on window close.

`Session::set_render_budgets(window, scene_bytes, layer_bytes)` changes the scene
and each layer-cache budget; zero disables the relevant retention. Oversized
scenes use immediate software paint into the persistent buffer, with a complete
frame upload/presentation, rather than retaining an unbounded scene or omitting
content. `Session::rendering_stats(window)` exposes damage/raster pixel counts,
cache hits and retained scene/raster/GPU byte accounting. These budgets apply to
rendering; the broader document/task/model memory audit is separate work.

## Validation

From gui-gos:

```sh
tests/screenshots/run.sh
tests/wrap/run.sh
tests/rendering/run.sh
```

The rendering runner builds the Rust `render-check` example, starts a private
headless Weston with Xwayland, and checks software, unavailable-acceleration
fallback, X11 GPU and Wayland GPU paths. It measures 30 samples of committed
text-scene changes, clipped scrolling, resize, caret-only damage and unchanged
scenes at 640x480, 1920x1080 and 3840x2160. Each workload is warmed independently.
It compares actual GPU readbacks after initial and incremental frames, tests
resource recreation, and enforces cache and no-work invariants. This renderer
fixture is separate from application input-to-present and 60-second idle budgets
in `tests/perf`; native Windows and macOS execution belongs to CI.

Software is the permanent default on every driver, including a GPU-capable one.
Only recognized explicit `GUI_RENDERER=gpu` or `GUI_RENDERER=auto` overrides can
request acceleration. Unset, empty and unknown values use software. Clearing an
opt-in also discards an existing GPU presenter at the next presentation. The
native rendering gate runs with the override unset and with an unknown value on
both X11 and Wayland and requires software, separately from explicit GPU tests.
