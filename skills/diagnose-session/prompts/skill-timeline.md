Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Skill timeline

Build the per-turn record of skill and plugin use, then report gaps.

1. List the human prompts with line numbers and timestamps.
2. Using the skill-invocation meanings recorded in CASE, list every explicit skill invocation, skill body injected into context, and read of a file named `SKILL.md`, with the line, the skill name, and the human turn.
3. List every plugin, agent type, MCP server, and hook evidenced in the session, using only the meanings recorded in CASE.
4. Collect the trigger descriptions of the skills available in the session: from a skill listing captured in the transcript when one exists; otherwise from the `description` frontmatter of the installed skills named in CASE, labeled as a current snapshot that may differ from what the session saw.
5. For each human turn, compare the request with those descriptions and report:
   - each skill invoked, with the request that preceded it (group by skill when there are many);
   - a turn whose request matches a skill's description with no invocation in that turn: quote the request and the matching description text;
   - a skill invoked one or more turns after the matching request;
   - a skill invoked whose description does not match the request it followed;
   - each non-skill plugin component used, and where.

Report the match and the absence. Do not judge whether a trigger or non-trigger was wrong.
