# GitHub Copilot Code Review mechanics

This reference is a starting point, not a source of truth. Re-verify every row marked `re-verify` against current official documentation before relying on it; if the docs differ, current docs take precedence.

## Facts

| ID  | Fact                                                                                                                                                                                               | Status    | Source |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------ |
| M1  | Code Review reads `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, root `AGENTS.md`, and `CLAUDE.md`, `GEMINI.md`, `REVIEW.md` if present                           | re-verify | S1     |
| M2  | Instructions, agent instructions, and skills are read from the PR head branch, not the base branch, so a PR can test its own customization                                                         | re-verify | S1, S2 |
| M3  | Code Review can use agent skills from `.github/skills`; a review-focused directory name such as `code-review` makes use more likely                                                                | re-verify | S1, S3 |
| M4  | Existing skills in `.github/skills` can be used by Code Review automatically when relevant to the review                                                                                           | re-verify | S3     |
| M5  | Project skills may live in `.github/skills`, `.claude/skills`, or `.agents/skills`; file must be named `SKILL.md`                                                                                  | re-verify | S3     |
| M6  | `SKILL.md` frontmatter: `name` (required, lowercase with hyphens, typically matches directory), `description` (required), `license` (optional)                                                     | re-verify | S3     |
| M7  | Files in a skill directory are discovered and made available alongside the skill instructions when the skill is invoked                                                                            | re-verify | S3     |
| M8  | Path-specific `*.instructions.md` files use `applyTo` globs; frontmatter `excludeAgent: "code-review"` or `"cloud-agent"` hides that file from that agent; documented only for path-specific files | re-verify | S4     |
| M9  | Multiple `AGENTS.md` files may exist; the nearest one in the directory tree takes precedence                                                                                                       | re-verify | S4     |
| M10 | General Copilot precedence: personal, then repository, then organization; all relevant sets are provided. Not documented as Code Review specific                                                   | re-verify | S4     |
| M20 | Organization custom instructions apply to Code Review on GitHub.com; require Copilot Business or Enterprise; not visible from the repository                                                       | re-verify | S5     |
| M21 | Code Review on GitHub.com supports repository-wide, path-specific, agent (`AGENTS.md`), and organization instructions; IDE review surfaces support fewer types                                     | re-verify | S6     |
| M11 | Repository settings can turn custom instructions off for Code Review ("Use custom instructions when reviewing pull requests")                                                                      | re-verify | S4     |
| M12 | MCP servers for review are configured in repository Copilot settings; GitHub and Playwright MCP are on by default; a setting allows MCP in review                                                  | re-verify | S1     |
| M13 | Comment attributions reference the skill or MCP server used; the review session log shows tools called                                                                                             | re-verify | S1     |
| M14 | Review environment: `copilot-code-review.yml` overrides `copilot-setup-steps.yml` for review when present                                                                                          | re-verify | S1     |
| M15 | Copilot labels comments High, Medium, or Low and leaves a "Comment" review by default; approvals are opt-in and in public preview                                                                  | re-verify | S1     |
| M16 | Replies to Copilot review comments are not visible to Copilot; re-reviews may repeat dismissed or downvoted comments                                                                               | re-verify | S1     |
| M17 | Unsupported instructions: changing comment format, changing the PR overview, blocking merges, following external links, vague "be more accurate"                                                   | re-verify | S2     |
| M18 | Very long instruction files may be partly overlooked; GitHub suggests keeping any single file under about 1,000 lines                                                                              | re-verify | S2     |
| M19 | Review effort levels exist (Lite, Balanced); defaults can be set per user, organization, or repository                                                                                             | re-verify | S1     |

## Design consequences

- Dogfooding on the customization PR itself is supported while M2 holds; M13 attributions can confirm use, but their absence does not prove non-use (a review may leave no comments).
- Because of M2, a contributor can change review guidance inside their own PR. Mention in the PR description that changes to `.github/skills/**`, `.github/instructions/**`, and agent instruction files deserve maintainer review.
- Because of M4 and M1, an existing generic skill or agent file can inject generic review advice. Audit every surface before adding a new one.
- Because of M8, a review-only path-specific file (`excludeAgent: "cloud-agent"`) is an alternative to a skill when deterministic loading for matching paths matters more than relevance-based selection.
- Because of M15, severity (High, Medium, Low) and review state (Comment, Approve) are separate. Generated guidance speaks of confirmed defects with severity by impact and does not define its own "blocking".
- Because of M17, generated rules are self-contained and never depend on following an external link (a URL may stay as provenance), and never dictate comment or overview format.
- Because of M21, skills and path-specific files target review on GitHub.com; do not claim the same effect for review in VS Code or other IDEs without checking S6.
- Because of M20, an organization instruction set may already shape reviews. Ask the user about it when review history shows behavior no repository surface explains.

## Sources

- S1: Using GitHub Copilot code review, https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/use-code-review
- S2: Using custom instructions to unlock the power of Copilot code review, https://docs.github.com/en/copilot/tutorials/customize-code-review
- S3: Adding agent skills for GitHub Copilot, https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- S4: Adding repository custom instructions for GitHub Copilot, https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions
- S5: Adding organization custom instructions for GitHub Copilot, https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-organization-instructions
- S6: Support for different types of custom instructions, https://docs.github.com/en/copilot/reference/custom-instructions-support

## Live verification table

Build this at the start of every run for each mechanism the design may rely on. A mechanism whose Code Review support is not confirmed here cannot justify a decision.

| Mechanism | Applies to Code Review on GitHub.com | Loading (automatic, relevance-based, configured) | Branch source | Limits              | Source URL | Checked (date) |
| --------- | ------------------------------------ | ------------------------------------------------ | ------------- | ------------------- | ---------- | -------------- |
| <name>    | yes, no, or unconfirmed              | <how>                                            | <head, base>  | <size, scope, plan> | <url>      | <YYYY-MM-DD>   |

## Unverified mechanisms

Exact skill-selection logic beyond the documented naming hint, any size limit specific to skills, and precedence between repository surfaces within Code Review were not verified. Treat them as unknown until checked.
