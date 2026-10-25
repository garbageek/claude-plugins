Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Repeated work

Find work the session did more than once.

1. Extract every tool call as `(line, turn, tool, key)`, where `key` is the file path for reads, edits, and writes; the whole command text for shell calls, with trailing whitespace stripped; the description plus the first 80 characters of the prompt for subagent dispatches; the query for searches.
2. Group by `(tool, key)` and report groups at or above the threshold:

   | Category            | Threshold                   | Exempt                                                                                                              |
   | ------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------- |
   | Reads, searches     | 3                           |                                                                                                                     |
   | Edits               | 2                           |                                                                                                                     |
   | Shell commands      | 2                           | Status checks such as `git status`, `ls`, `pwd`, and repeated runs of the same build or check command between edits |
   | Subagent dispatches | 2 with the same description |                                                                                                                     |

3. For each group, check what happened between repetitions: a write to that file, a compaction, a human correction. A re-read after an edit is not a finding; a re-read after a compaction is a finding attributed to the compaction; a repetition with nothing in between is a finding on its own.
4. Find re-derived decisions: assistant text reaching a conclusion already stated earlier (the same file, design choice, or command). Quote both places.
5. One finding per group, with the first and last line and the count.
