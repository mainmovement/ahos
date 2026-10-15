# تصمیم‌های سلطان برای پرسش‌های Q1 تا Q10 داشبورد
تاریخ: 2026-10-09 04:55 Asia/Tehran
نویسنده: سلطان، به نیابت از مالک. مهرداد گفته است ایجنت‌ها از او سؤال نپرسند و خود سلطان تصمیم بگیرد.
دلیل: این‌ها تصمیم‌های فنی برگشت‌پذیرند و هیچ‌کدام به قفل‌های مالک (push، .env، دیتابیس، Lane A، معامله‌ی واقعی) دست نمی‌زنند.

# Decisions binding on CLAUDE_BUILD_MISSIONS.md (override the defaults where they differ)
- Q1 Browser: Chrome first, Edge fallback, then the default browser as the last fallback. As specified.
- Q2 Second click while AHOS runs: if the AHOS app window is alive, bring it to the front and restore it if minimized (Win32 SetForegroundWindow/ShowWindow on the process found by our --user-data-dir). Do not just log. If it is not alive, mint a fresh one-time token and open the window. There must never be two windows. This overrides M-D1 step 6.
- Q3 Package installs: approved by the owner's standing instruction for safe, reversible engineering, limited to the exact packages and pinned versions named in the spec (three, @react-three/fiber, @react-three/drei, postprocessing / @react-three/postprocessing, three-globe, plus self-hosted font files). Commit the lockfile. Use no runtime CDN, and no postinstall script that fetches at runtime. If the tool's own permission system blocks an install, record it as BLOCKED_TOOL_PERMISSION with the exact command and move on to the next 2D mission. Do not route around the block.
- Q4 Geographic data: allowed later, only from a real source and under the two-source rule. Until then the geographic layer shows UNKNOWN and chains appear as conceptual rings, as specified.
- Q5 Default theme: imperial crimson, black and gold. Blue neon is the second theme.
- Q6 External links inside the locked window: open them in the user's normal default browser through the OS, never inside the app window. Copying a link is also available.
- Q7 One-time boot token on the browser command line: acceptable for a local single-user laptop, provided the token is single-use, expires within 60 seconds, never appears in a log, and the test suite proves both of those. Command lines can be seen by other local processes, so the short expiry is mandatory.
- Q8 Agent grouping: the council teams in council.ts are canonical for the visual only. Show the real maturity of the 19 canonical agents from ahos_org/registry.py (all REGISTERED at level 0 today). Never show an agent as active without evidence.
- Q9 Sound: generated Web Audio tones plus CC0 sounds (Kenney) are OK. Sound starts muted, with a visible mute and volume control.
- Q10 Emblem: draw our own vector Faravahar and an emblem based on reference image 4 (star coin). Refresh the app icon, keeping launcher\ahos.ico.old-* as a backup. AHOS.lnk itself stays unchanged; only the .ico content changes, and only in M-D10.

Additional owner rules for every mission:
- Two-source rule: every data widget shows the truth state. One source shows as UNKNOWN, disagreement shows as CONFLICT, and neither is ever styled as success.
- Target: competition-winning visual quality (Awwwards and FWA level) with honest data and smooth performance on the laptop.
- Archive: every mission receipt is also mentioned in the daily log in حافظه_ادامه.
