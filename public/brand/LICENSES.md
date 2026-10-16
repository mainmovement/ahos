# Licences — AHOS brand & icon pack (02_icons)

## 1. Vector artwork — CC0 (public domain dedication)

Every icon, emblem, status mark, logo and lockup in this pack was drawn from
scratch for AHOS by the AHOS project (geometric construction, original paths, no
traced or copied third-party artwork, no icon-font outlines, no trademarked
marks).

To the extent possible under law, the AHOS project waives all copyright and
related or neighbouring rights to this artwork. It is dedicated to the public
domain under the **Creative Commons CC0 1.0 Universal Public Domain Dedication**.

You may copy, modify, distribute and use it, including commercially, without
permission or attribution. See <https://creativecommons.org/publicdomain/zero/1.0/>.

Applies to: `logo/*.svg`, `nav/*`, `status/*`, `agents/*`, `sprite.svg`,
`preview.html`, every PNG/ICO in `logo/png/` and `logo/favicon/`, and the
`ICON_MANIFEST.json` metadata.

## 2. Wordmark outlines — SIL Open Font License 1.1

`logo/ahos-lockup-horizontal.svg`, `logo/ahos-lockup-stacked.svg` and the
`<text>` nodes in `logo/ahos-lockup-horizontal-live-text.svg` contain outlines of
the letters **"AHOS"** and the Persian word **"اهوس"** as set in
**Vazirmatn SemiBold** by Saber Rastikerdar (and contributors), converted to SVG
paths with HarfBuzz + fontTools.

Vazirmatn is licensed under the **SIL Open Font License, Version 1.1**. The full
licence text ships with this pack at `tools/fonts/OFL.txt` and upstream at
<https://github.com/rastikerdar/vazirmatn>.

Consequences you should know about:

* The converted letter outlines remain subject to the OFL. Embedding or
  redistributing them inside documents, apps or websites is permitted,
  including for commercial work.
* The OFL does **not** permit selling the font (or its outlines) on its own, and
  does not permit using the reserved font name *Vazirmatn* for a modified
  version. Using these outlines as an AHOS logo lockup is fine — the *name* being
  reserved refers to redistributing a modified font under that name, not to
  typographic artwork.
* If you want a wordmark with no OFL obligation at all, replace the two lockups
  with your own lettering — the star mark itself is CC0 and unrestricted.

## 3. Build tooling — MIT / ISC (not part of the shipped artwork)

`tools/` depends on:
* **sharp** (Apache-2.0) — PNG/ICO rasterisation
* **svgo** (MIT) — SVG optimisation
* **fontTools** (MIT), **uharfbuzz** (MIT) — wordmark outline conversion
* **ImageMagick** (ImageMagick licence) — multi-size `.ico` assembly

These are development dependencies; they are not redistributed as part of the
pack's assets.

## 4. Trademarks

"AHOS" and the star mark in this pack are the project's own identifying marks.
No third-party trademark, brand or company logo is referenced, imitated or
redrawn anywhere in this pack. The icons follow generic visual conventions
(a magnifier for search, a shield for security) which are not protectable.
