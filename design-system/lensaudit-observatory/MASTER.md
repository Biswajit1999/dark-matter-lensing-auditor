# LensAudit Observatory design system

This is the visual source of truth for the scientist-facing web instrument. It refines the generated high-variance, high-density recommendation around the product’s actual scientific and accessibility constraints.

## Product character

- **Category:** spatial research workbench, not marketing dashboard.
- **Audience:** astronomers, lens-model users, students, and technically literate reviewers.
- **Visual idea:** a dark optical bench crossed with a paper methods figure.
- **Density:** high around parameters and evidence; generous around the research thesis.
- **Shape language:** square, registered, bounded, measurable. Avoid decorative rounded cards.
- **Motion:** only state continuity and mode transitions. Never animate scientific values merely for spectacle.

## Epistemic hierarchy

The most important design rule is not aesthetic:

1. Synthetic injection–recovery and observational audit are separate top-level modes.
2. Known truth is coral and may appear only in simulation mode.
3. Luminous centroid is mint cross; inferred mass centroid is amber circle.
4. Observational mode always states that truth is unknown and the single model does not measure between-team systematics.
5. Every graphical metric has a visible numeric or tabular equivalent.

## Semantic tokens

| Role | Token | Value | Use |
|---|---|---:|---|
| Void | `--void` | `#050b0b` | page and canvas surround |
| Surface | `--surface` | `#091211` | controls and evidence rails |
| Raised surface | `--surface-raised` | `#0d1917` | active mode and buttons |
| Strong surface | `--surface-strong` | `#13231f` | hover / nested content |
| Primary ink | `--ink` | `#f2f5e9` | headings and primary values |
| Muted ink | `--muted` | `#9dad9f` | supporting prose |
| Faint ink | `--faint` | `#718078` | units, axis extents, tertiary labels |
| Boundary | `--line` | `#263b35` | grid and panel rules |
| Strong boundary | `--line-strong` | `#456057` | controls and map frame |
| Light proxy | `--mint` | `#a7edca` | luminous centroid and active state |
| Simulation | `--acid` | `#d8f66c` | known-truth experiment values |
| Inferred mass | `--amber` | `#ffd166` | mass centroid and κ probe |
| Truth / warning | `--coral` | `#ff7d67` | injected truth and validity warnings |
| Observational | `--blue` | `#6cc6e2` | observational-only verdict |

Color never carries status alone. Every semantic state includes a label, geometry, or icon.

## Typography

- **Interface / thesis:** Manrope, weights 400–800.
- **Measurements / metadata:** DM Mono, weights 300–500, tabular figures.
- **Minimum body size:** 16 px on narrow screens; compact metadata may be 9–11 px only when it is supplementary and not the sole carrier of a control label.
- **Heading measure:** balanced on large screens, normal wrapping on narrow screens.
- **Numerical precision:** match the underlying estimator; never imply more than two decimal places for browser audit metrics.

## Layout

Desktop is an asymmetric three-rail instrument:

```text
parameter rail (260–330) | square evidence plane (flex) | diagnostic rail (270–340)
```

At 1180 px the diagnostic rail becomes a full-width evidence strip. At 840 px the map is first, followed by controls and evidence. At 540 px every element is single-column and no item may create horizontal overflow. Validate at 375, 768, 1024, and 1440 px.

Spacing follows 4/8 px rhythm with dense control increments: 4, 8, 12, 16, 24, 32, 48, 68.

## Spatial evidence

- Use Canvas for dense raster layers and contours.
- Always retain a nearby legend and an accessible numerical probe.
- Overlay mode combines grayscale/asinh light morphology with sequential κ color and four contour levels.
- Residual mode uses a centered diverging palette.
- Uncertainty uses a sequential palette distinct from κ.
- Pointer movement probes exact cell values; arrow keys provide the same operation.
- Markers have both color and geometry: cross, circle, diamond.
- The full-resolution data product must never be inferred from the browser derivative.

## Components

- Interactive targets are at least 44 CSS px tall.
- Buttons have visible borders and stable bounds; hover changes surface or border, not layout.
- Range inputs retain a large interactive track and explicit numeric output.
- Details/summary is used for receipts and evidence tables so complexity is progressively disclosed.
- Export actions name the format and produce self-describing files.
- Active states use `aria-pressed`; icon-only meanings always have visible text or an accessible name.

## Motion

- Mode replacement: opacity plus ≤8 px vertical continuity, 240 ms.
- Controls respond immediately; the scientific result must not wait for animation.
- No parallax, background particles, auto-rotation, or decorative orbit animation.
- `prefers-reduced-motion: reduce` collapses all motion to an effectively immediate final state.

## Accessibility and QA

- Primary and body text maintain WCAG AA contrast against their surfaces.
- Focus uses a 3 px white outline with 3 px offset.
- A skip link targets the main workbench.
- Canvas carries a descriptive label and keyboard-operable probe.
- Evidence has a native table alternative.
- Never rely on hover, color, dragging, or animation alone.
- Viewport zoom remains enabled.
- Verify no horizontal scroll and no obscured focus at 375 px.
- Verify the app with reduced motion and a keyboard-only path.

## Avoid

- generic glass cards, pill-shaped controls, dashboard gauges, ornamental 3D, star-field wallpaper, neon overload;
- calling a model residual a dark-matter detection or a Gaussian sigma;
- mixing source FITS values and display-normalized values without a label;
- exposing injected truth in observational mode;
- hiding uncertainty to make a map appear cleaner;
- unexplained acronyms or icon-only navigation; and
- animations that suggest confidence, convergence, or physical evolution.
