# The World in One Page — Thursday 26 November 2026

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/akbare12/news-26-b22-numbers/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/akbare12/news-26-b22-numbers/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

A one-page newspaper front page summing up the world's news of
**Thursday 26 November 2026** — 50 stories across 16+ regions.

## Layout V20

Masthead plus a two-line DATE CHECK, then a three-column main area: the
left and right rails each carry five mini-cards (cards 1–5 and 6–10),
while the centre column stacks the three heroes — Macy's 100th
Thanksgiving parade postponed for the first time ever by weather,
the IRGC claim of two tankers hit by mines in Hormuz, and the global
markets rebound as Trump tariffs look milder. Below that: a world map
with numbered pins next to an ALSO column, a timeline strip, and a
sources footer.

Tags on every hero, card and ALSO item: `[C]` confirmed, `[R]`
reported, `[CL]` claim. Macy's is `[C]`, the IRGC tanker claim is
`[CL]`, tariffs are `[C]`. The Bogor mine flood (13 dead, 13 missing)
is card 3. Stories that are not 26 November are named
only in the DATE CHECK as deliberately excluded (COP31 failure 22 Nov,
Shenzhou-24 25 Nov, Cairo tanker blast 25 Nov, and more).

## Files

- `gen.py` — renders `entry.png` with Pillow at build time. Every
  string is measured with PIL font metrics against its real column
  width and asserted to fit; there is no silent truncation. Art is
  drawn on layers clamped to their own boxes, never over text. The
  ALSO-vs-hero/card duplicate scan asserts zero overlaps, and each
  hero asserts a WHY-to-stat gap of at least 6 px.
- `main.py` — the entry program. Standard library only (`os`,
  `shutil`, `hashlib`); it copies `entry.png` to
  `$MAKEFUN_OUTPUT_DIR/entry.png`.
- `entry.png` — the rendered front page, 1024×1024.

## Verification

- `entry.png`: 1024×1024, 190978 bytes (limit 1 MiB)
- sha256: `3b3925eabed050f46c24e98a727ae943d10154bfafc6d84822b73b7407446388`
- 50 stories: 3 heroes + 10 cards + 29 ALSO + 8 briefs
- `gen.py` run twice produces identical bytes (deterministic render).
- Stdlib-venv simulation: `main.py` runs with no Pillow installed,
  from a different working directory, into an empty output directory,
  and the output sha256 matches `entry.png`.

## License

MIT — see `LICENSE`.
