# NIYET asset review and placement

All **29 files** from `NIYET_UI_Assets_Pack.zip` were extracted into `design/asset-pack/NIYET_UI_Assets_Pack`, enumerated, and reviewed before implementation. README and manifest were read, all SVG source was inspected, every raster was viewed on an inspection sheet, and the moodboard plus desktop/mobile composition references were inspected individually. The manifest counts match the extracted files. The moodboard depicts additional conceptual assets not present as separate files; those were not invented or downloaded.

| Supplied file | Disposition | Location and purpose |
| --- | --- | --- |
| `README.md` | Reference | Selective integration and data-readability guidance |
| `manifest.json` | Reference | Inventory/count verification |
| `backgrounds/bg-01-aurora.jpg` | Reference | Palette comparison; too broad an illumination for the narrow working hero |
| `backgrounds/bg-02-focus.jpg` | Used, optimized | `focus.webp`: introduction behind the headline and wave |
| `backgrounds/bg-03-grid.jpg` | Reference | Technical texture direction; transparent grid chosen instead for explanatory content |
| `backgrounds/bg-04-data-horizon.jpg` | Intentionally not rendered | Landscape requires too much vertical space; would push the composer away |
| `gradients/gradient-01.png` | Reference | Blue/violet balance; not stacked over another hero illumination |
| `gradients/gradient-02.png` | Reference | Alternate emphasis; unnecessary second blue texture |
| `gradients/gradient-03.png` | Reference | Violet range; strongest color would compete with status semantics |
| `gradients/gradient-04.png` | Used, optimized | `lab-glow.webp`: masked, softly bounded laboratory introduction only |
| `hero/hero-wave-01.png` | Used, responsive derivatives | `wave.webp` and `wave-small.webp`: transparent hero graphic, decorative with empty alt |
| `hero/hero-wave-02.png` | Reference | Compared wave density; one consistent wave establishes identity |
| `hero/hero-wave-03.png` | Reference | Compared wave orientation; not repeated in data screens |
| `patterns/pattern-grid.png` | Used, optimized | `grid.webp`: five-step SOURCECHAIN explanation, never evidence passages |
| `patterns/pattern-dots.png` | Used, optimized | `dots.webp`: quiet texture in empty response space |
| `patterns/pattern-lines.png` | Intentionally not rendered | Additional line texture competes with wave and source dividers |
| `icons/layers.svg` | Used in SVG sprite | SOURCECHAIN introduction, evidence stage and BOTH resolution |
| `icons/graph.svg` | Used in SVG sprite | Allocation Lab identity |
| `icons/check.svg` | Used in SVG sprite | Resolution stage and no-further-review status |
| `icons/search.svg` | Used in SVG sprite | Explore navigation and deferred context status |
| `icons/source.svg` | Used in SVG sprite | Source step, evidence summary and evidence resolution |
| `icons/shield.svg` | Used in SVG sprite | Claim-comparison explanation; not a fabricated certification seal |
| `icons/arrow-right.svg` | Used in SVG sprite | Primary start action and human routing status |
| `icons/link.svg` | Used in SVG sprite | Provenance stage and real external source links |
| `brand/niyet-wordmark.svg` | Used inline | Header on both real routes; currentColor follows the selected theme |
| `brand/niyet-mark.svg` | Used directly | Shared header, NSosyal sidebar context and favicon |
| `ui-elements/desktop-product-reference.jpg` | Reference | Conceptual grouping adapted to a working three-column interface |
| `ui-elements/mobile-product-reference.jpg` | Reference | Single-column hierarchy; density and touch controls rebuilt in HTML |
| `docs/niyet-assets-moodboard.jpg` | Reference | Restrained dark research identity and blue/violet accents |

## Delivery and optimization

`scripts/prepare_brand_assets.py` reproduces all web derivatives with Pillow. The web bundle includes only chosen assets under `web/assets/niyet`, never the ZIP, moodboard, or composition screenshots. Original files remain in the design directory for traceability and rebuilding.

Desktop wave: 70,786 bytes; mobile wave: 24,134 bytes; focus background: 3,004 bytes; laboratory glow: 1,320 bytes. `<picture>` selects the smaller mobile wave. The CSS backgrounds are scoped to their components; the laboratory glow is not used by the feed. SVG symbols preserve `currentColor`; complementary existing social icons retain a matching thin-stroke style. Dense source passages and experiment results use solid surfaces.

Dark is the NIYET brand default. An explicit light-appearance control is available on both routes and persists across navigation. The supplied mark retains its original dark tile on either surface, while the wordmark inherits text color. Neither decorative art nor a status icon implies that evidence is true or a person is verified.
