# Runtime Diagnosis Patterns

Pattern catalog for runtime diagnosis audits. Read this when analyzing runtime logs to find substrate problems.

## Diagnostic Frame

**Start with substrate evidence before blaming the model. If substrate evidence is clean, document model limitation, prompt ambiguity, data quality, or expected nondeterminism explicitly.**

"Substrate" = everything between user message and model response:
- System prompt assembly (what instructions the model sees)
- History/tail construction (what conversation the model sees)
- Memory injection (what "facts" get recalled into prompt)
- Tool catalog (what tools are attached and how they're described)
- Response parsing (how we interpret model output)
- Error handling (how we relay failures back)

This principle applies to any LLM-based system. The specific code paths below are examples — adapt them to the project you're auditing.

---

## Log Discovery

Before applying patterns, find the actual log files:

```bash
# Discover log locations
find . -name "*.log" -o -name "*.jsonl" | grep -v node_modules | grep -v .git | head -20
ls var/log/ logs/ 2>/dev/null
```

Map each log to what it contains. Typical structure:

| Log type | What to look for |
|----------|-----------------|
| Application log | Errors, warnings, timeouts, stack traces |
| Request/response trace | Full payloads sent to/from the model |
| Agent/memory log | Memory operations, tool execution |
| Flow lifecycle log | Message timestamps, routing, state transitions |
| Metrics log | Token usage, background task timing |

---

## Pattern Catalog

### 1. Context Surface Pollution

**Symptom**: Model responds to operational context instead of the human's message.
**Evidence**: Request `messages[]` contains tool transcripts, corrective system notes, or internal ops mixed with user dialogue.
**Root cause**: History projection includes data that should be system-only (tool transcripts, internal state notes).
**What to trace**: History/context builder, message projection logic.

### 2. Memory Injection Noise

**Symptom**: Model references technical or meta context unprompted, gives operator-style answers to casual questions.
**Evidence**: System prompt contains internal docs, architecture notes, audit findings, or operator artifacts in the "known facts" section.
**Root cause**: Indexer indexes internal documents as recallable memory without filtering for context-appropriateness.
**What to trace**: Memory indexer, memory search, memory-to-prompt injection layer.

### 3. Ballast on Short Turns

**Symptom**: Casual one-word message gets the same heavy prompt as a complex task.
**Evidence**: System prompt >10K chars and >10 tools on a turn where user message is <20 chars.
**Root cause**: No turn-type classification → no prompt profiling. Every turn gets the full payload regardless of complexity.
**What to trace**: Context builder, tool selection logic, turn entry point.

### 4. Streaming Parse Failures

**Symptom**: Repeated `malformed tool args` warnings, eventual timeout.
**Evidence**: Logs show pattern of empty fragments + truncated JSON for the same tool call across streaming deltas.
**Root cause**: Streaming delta merging doesn't correctly handle the provider's chunk format (especially non-OpenAI providers).
**What to trace**: Stream delta merging, tool call parsing.

### 5. Death Loops (No Circuit Breaker)

**Symptom**: Same error repeated dozens or hundreds of times until timeout.
**Evidence**: >5 consecutive identical warnings within seconds.
**Root cause**: Agent/reasoning loop has no counter for consecutive failures of the same type.
**What to trace**: Main agent loop, turn orchestration, error retry logic.

### 6. Tool Protocol Drift

**Symptom**: Model writes tool invocation as plain text instead of structured tool_call.
**Evidence**: Corrective system note about text-as-tool-call appears in request messages.
**Root cause**: Tool call contract isn't strict enough, or model sees confusing examples in history that teach wrong format.
**What to trace**: Phantom continuation detection, tool call parsing.

### 7. Error Explanation Gaps

**Symptom**: Model invents plausible but wrong explanation for an error.
**Evidence**: Response contains specific technical claims (e.g., "database timeout") that don't match any factual data in the request context.
**Root cause**: On error/timeout, model receives the conversation tail but no structured incident block with actual error details.
**What to trace**: Error relay logic, error-to-prompt formatting.

### 8. Token Usage Blindness

**Symptom**: All responses show 0 tokens in usage reporting.
**Evidence**: Usage field shows `{input_tokens: 0, output_tokens: 0}` on non-empty responses.
**Root cause**: Provider doesn't return usage in streaming mode, or the client library doesn't parse it from the response format.
**What to trace**: LLM client usage extraction, streaming response handling.

### 9. Model Switching Side Effects

**Symptom**: Behavior degrades immediately after a model switch event.
**Evidence**: Logs show model switch, then errors begin in subsequent turns.
**Root cause**: New model has different streaming format, tool call format, or context length limits that aren't accounted for.
**What to trace**: Model selection logic, provider-specific response handling.

### 10. Background Process Interference

**Symptom**: User-facing turn is slow or degraded while background tasks run.
**Evidence**: Background task timestamps overlap with user turn processing.
**Root cause**: Background tasks compete for the same LLM endpoint or consume shared resources (DB connections, memory).
**What to trace**: Background task scheduling, resource isolation, shared service access.

---

## Applying Patterns

For each pattern found:
1. **Confirm with evidence** — find the specific log lines or trace entries
2. **Trace to the responsible code path** — use the "What to trace" hints to locate the source
3. **Write the ticket** — include the pattern name, the evidence, and the code path
4. **Move to the next pattern** — don't fix during audit, just record

The patterns are ordered by diagnostic frequency in typical LLM agent systems, not by severity. Check all of them — they frequently co-occur.
