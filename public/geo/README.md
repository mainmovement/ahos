# `public/geo/` — geography data served locally

Everything here is served from the app's own origin (`/geo/…`), so the stage's
"zero external requests at runtime" (spec §0.5) holds: nothing in this directory
is fetched from the internet at build or at runtime.

## `earth_specular_1k.png` — NASA Black Marble water mask (public domain)

2048 × 1024 equirectangular, 111 KB. **White = water, black = land**, with the
shorelines and the inland water rendered as a grey ramp rather than a binary
edge — that ramp is what the globe's land layer samples.

Source: NASA Visible Earth (Blue Marble / Black Marble), public domain per
NASA's media guidelines. This file is a downsampled (Lanczos) copy of the
specular map shipped in `three-globe@2.45.4`'s `example/img` (the repo is MIT;
the imagery is NASA public domain). 1k is the ceiling on the owner's 8 GB box —
do not pull the 2k/4k variants into the running build.

Provenance chain and licence text: `vendor_assets/globe/licenses/` (the vendor
kit is a local, gitignored source kit — nothing there is committed).

### Sampling convention

The mask is sampled as

```
u = (lon + π) / 2π        // column 0 is longitude −180°
v = (90° − lat) / 180°    // row 0 is north
```

i.e. plain equirectangular, north up, with `three`'s default `flipY` left on.
`scripts/land_mask_selftest.ts` pins this against named geography (Tehran and
Madagascar are land; the mid-Atlantic and the Caspian are water) so a flipped
axis breaks a test instead of silently putting the continents in the wrong
place.
