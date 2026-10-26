# Backlog

Ideas and follow-ups not yet scheduled. Newest first.

- **Bolder README hero accent.** The deep teal band is a placeholder. Render about three treatments side by side and pick one: the accent carried through the connector lines, arrowheads and skill bars so it ties the image together; the same with a solid "SHARED INSTALL" chip and a 2 px band border; and a hand-tuned, more saturated color chosen for this slate palette instead of a preset (no Tailwind or diagram-design defaults, nothing muted or cartoonish). Change `agents/hero.py`, then follow [Keeping the README image and agent map current](agents/README.md#keeping-the-readme-image-and-agent-map-current).
- **Real-model check of each specialist.** The runtime check uses a stand-in model. After a live install, give each specialist one real task and confirm its instructions and skill limits hold.
- **Codex skill filtering.** rulesync 41 writes Codex `skills.config` before `developer_instructions`, which breaks the TOML, so Codex agents don't filter skills. Revisit when rulesync fixes it.
