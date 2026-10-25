Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Request conflicts

1. List every human prompt with its line and turn. Extract the instructions it contains: imperatives, constraints, scope statements, and "don't", "always", "never", "only".
2. Report:
   - two human instructions that cannot both be followed: quote both, with lines, and what the assistant did;
   - a human instruction that conflicts with an instruction file or skill loaded in the session (paths in CASE): quote both;
   - a human instruction the assistant did not follow, with the line where it was given and the line where it was not followed;
   - a human instruction to skip, ignore, or override a step, skill, or rule, and what happened afterwards;
   - a clarification the assistant asked for, and the answer, when the answer changed scope.
3. Do not judge whether the user was right. Report the conflict and how the assistant resolved it.
