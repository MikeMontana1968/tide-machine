A copy of the flatpack-guide kit (~/.claude/skills/flatpack-guide), taken
2026-10-17, so this repo can rebuild the assembly guide without the kit installed.
Same layout as the kit: scripts/ (build, Fritzing and KiCad readers) and
assets/ (the page's drawing code). Build with `python build.py` in the folder
above. gen_fritzing.py uses scripts/ here first, the installed kit only if
these are missing. To pick up later kit improvements, copy the files over again.
