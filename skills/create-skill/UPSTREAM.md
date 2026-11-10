# Source attribution

The evaluation helpers, reviewer, schemas, graders and packager in this skill
are adapted from the user-supplied `skill-creator.zip` (archive timestamp
2026-11-03). The supplied upstream source carries the Apache License 2.0;
its complete license is retained in `LICENSE.txt`.

Changes in this integration: a separate host-neutral `create-skill` entry point,
explicit Claude vs Codex evaluation boundaries, a cross-host functional task
runner, and integration into the shared Artur Plugins skill tree. The original
Claude-specific scripts remain available under their original filenames.
