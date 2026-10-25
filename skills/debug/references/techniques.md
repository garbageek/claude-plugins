# Debugging techniques

Supporting techniques for [debug](../SKILL.md). Load the section the current step needs. Authority limits in the skill apply to every technique here.

## Contents

- [Root-cause tracing](#root-cause-tracing)
- [Boundary evidence](#boundary-evidence)
- [Working-versus-broken comparison](#working-versus-broken-comparison)
- [Regression bisection](#regression-bisection)
- [Timing-dependent failures](#timing-dependent-failures)

## Root-cause tracing

A failure often surfaces deep in a call chain, far from the value that caused it. Fixing where it surfaces treats the symptom.

1. Name the immediate cause: the operation that failed and the value it received.
2. Find the caller and the value it passed. Repeat for each caller.
3. Stop at the frame where a correct input first becomes incorrect, or where a required value is first missing. That frame's owner is the producer.
4. Check sibling callers of the producer: they may receive the same bad value through other paths.

Example: a tool writes files into the source tree instead of a temporary directory.

```text
write(path)                      path = "./out"         <- symptom
  <- Workspace.init(dir)         dir  = ""              empty string resolves to cwd
  <- Session.create(dir)         dir  = ""
  <- setup()                     dir read before it was assigned   <- producer
```

The fix belongs in `setup()`, which reads the value before it is initialized. A check in `write()` would only move the failure.

When the chain cannot be followed by reading, capture it at runtime (fix mode only): log immediately **before** the failing operation, including the inputs, the working directory, relevant environment values, and a stack trace, to a stream that is not suppressed. Remove the instrumentation before delivery.

## Boundary evidence

For a multi-component flow, one run that records each boundary is usually cheaper than several guesses.

For each boundary in order, record:

- what entered: the request, message, arguments, or file;
- the configuration and environment that component actually saw, not what the operator expected it to see;
- what left, or the error it raised.

The first boundary whose output is wrong while its input is correct contains the defect. Report secret values as `SET` or `UNSET`; never print them.

## Working-versus-broken comparison

Use when a similar path works, or a reference implementation exists.

- Read the working path or reference completely before comparing.
- List every difference: inputs, call order, configuration, versions, permissions, data shape, environment.
- Eliminate differences one at a time with evidence. Do not discard a difference because it "cannot matter" until it has been checked.

## Regression bisection

Use when a known-good revision exists and the failure reproduces deterministically.

`git bisect` checks out other revisions and changes the working tree, so it needs explicit authorization and a clean tree, or a separate clone the user agreed to. Record the good and bad revisions, the exact reproduction command, and its pass/fail criterion. Run `git bisect reset` afterwards, and confirm the original branch and HEAD are restored. The first bad commit locates the change; the root cause still needs to be read from that change.

## Timing-dependent failures

Intermittent failures that depend on speed, load, or ordering usually come from waiting for a fixed time instead of for a condition.

- Identify the condition the code actually needs: a file exists, a port accepts connections, an event has fired, a counter reached a value.
- Replace an arbitrary sleep or delay with waiting for that condition, with a timeout that produces a clear error naming the condition.
- A longer fixed delay is a mitigation, not a fix. Label it as one when nothing else is possible.
