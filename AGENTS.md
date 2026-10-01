# Agent guidance

Feature pull requests target `main`.

Keep the main checkout read-only. Work in `.claude/worktrees/<slug>` on a feature
branch. Use conventional commits and keep machine-specific configuration,
credentials, generated launch agents, and logs outside this repository.

Use Python's standard library for installers. Verify configuration and service
lifecycle changes on macOS; report any untested platform behavior.
