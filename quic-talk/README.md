# Why iroh uses QUIC

A 30 minute talk. About 10 minutes on what iroh is and how the parts fit
together (address lookup following [docs.iroh.computer], hole punching), then
about 15 on why iroh uses QUIC, both as its API and on the wire, compared with
the WireGuard-based projects. Same builder as the workshop slides: a
Markdown slide deck built into a single self-contained HTML file, with the animated SVG
diagrams from [iroh.computer][iroh-computer] inlined.

## Build

```
cargo run          # index.md -> docs/index.html
```

Open `docs/index.html` in a browser.

## Export

```
./export-pdf.sh
```

Writes `quic-talk.pdf`, one page per slide, via a headless Chromium-based browser
(Brave/Chrome/Edge — whatever is installed). Animated diagrams are frozen at
their initial frame; the HTML file stays the real presentation.

## Present

Arrow keys / space / click to navigate, `f` for fullscreen, `r` to restart
the current slide's animations (they also restart automatically on slide
entry). The slide number is in the URL hash, so reloading keeps your place.

## Editing

- `index.md` — the slides, separated by `---`. Fenced code blocks are
  syntax-highlighted at build time. Images referencing local `.svg` files
  are inlined into the output (ids get namespaced per slide so SMIL
  animations don't collide); local `.png`/`.jpg` files are embedded as
  data URIs. `![w:900](x.svg)` pins the display width;
  `<!-- center -->` centers a slide. Reference-style link definitions are
  shared across all slides.
- `scripts/*.gen.py` — the SVG generators; most are copied from the
  [iroh.computer repo][iroh-computer], `connection-streams.gen.py` is
  original. `endpoint-startup.gen.py` reads `endpoint-startup.land.txt`. Edit and run e.g. `python3 scripts/hole-punching.gen.py`; each
  writes its SVG to `public/animations/`, then rebuild with `cargo run`.

[iroh-computer]: https://github.com/n0-computer/iroh.computer
[docs.iroh.computer]: https://docs.iroh.computer/concepts/address-lookup
