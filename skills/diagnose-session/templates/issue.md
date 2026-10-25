Title: <skill or symptom>: <one-line observable> (<host>)

Use the target repository's own issue template when it has one, and map these sections into it. Leave any field the template requires about the reporter for the user to fill.

## Duplicate check

Searched: <query terms>. Closest existing issues: <#n title, state>, or "none".

## Summary

<The user's own words on what went wrong and what should have happened. Ask for them; a placeholder means the issue is not ready.>

## Environment

| Field                         | Value                 | Provenance and supporting evidence |
| ----------------------------- | --------------------- | ---------------------------------- |
| Skill or plugin version       | <version>             | <label>; <location>                |
| Host                          | <name>                | <label>; <location>                |
| Host version                  | <version>             | <label>; <location>                |
| Models                        | <model ids seen>      | <label>; <location>                |
| Other plugins and MCP servers | <list>                | <label>; <location>                |
| OS and shell                  | <os version>, <shell> | <label>; <location>                |

## Isolation

Reproduced without the skill or plugin of interest: <"not tried", or what was run and what happened, with the transcript path>. The evidence below shows involvement; it does not establish cause.

## What happened

<Problem statement and verdict, with citations rewritten as `transcript line <n>`.>

## Steps to reproduce

1. <first human prompt, scrubbed>
2. <the turns leading to the problem, one line each>
3. <the observable>

## Expected behavior

<From the problem statement.>

## Actual behavior

<From the verdict.>

## Evidence

Session id(s): <ids>. Local bundle: <path and redaction level, or "none built">. Involvement per the diagnosis report: <possible | likely>, at <transcript lines>.
