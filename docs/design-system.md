# Design System (Phase 1)

Technical editorial, not neon-hacker. Dark ink primary; light paper secondary (toggle in nav).

## Type
- UI: Space Grotesk (600/700 headings, 400/500 body). Mono: IBM Plex Mono (evidence, requests, terminal).
- Scale: 36 / 24 / 18 / 15 / 13 px. Body line-height 1.6.

## Color pairs (AA)
| Use | Pair | Ratio |
|---|---|---|
| Body dark | `#ede9df` on `#0b0d12` | ~14.5:1 |
| Secondary dark | `#bdb7a9` on `#0b0d12` | ~8:1 |
| Signal green dark | `#4bcc8d` on `#0b0d12` | ~9:1 |
| Body light | `#1c1a15` on `#f4efe4` | ~14:1 |
| Signal green light | `#0e7a4c` on `#f4efe4` | ~5.2:1 |
| Danger light | `#b3261e` on `#f4efe4` | ~6.5:1 |

## Construction
Nested machined panels (1px `--line-1`, 6px radius, uppercase micro-heads). Motion: translate/opacity ≤180ms; honours `prefers-reduced-motion`. Focus: 2px `--info` outline everywhere. Thin-line icons (1.5px stroke).
