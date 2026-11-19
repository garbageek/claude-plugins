#!/usr/bin/env python3
"""Find prose-editing candidates and check preservation against a source.

Usage:
  python3 ai_tells.py DRAFT [--source ORIGINAL] [--lang auto|en|ru|uk]
                            [--allow PHRASE ...] [--allow-category CAT ...]
                            [--allow-lines START:END ...] [--protect LITERAL ...]
                            [--json] [--fail-on high|medium]
  cat draft.md | python3 ai_tells.py -

Standard library only (Python 3.10+). Hits are candidates, not demonstrated defects or
authorship evidence. Their severity measures heuristic signal strength, not harm.
Review the context before editing; a clean scan cannot establish meaning or voice.
Accept a legitimate phrase with --allow "primary key"; see references/patterns.md.
With --source, the bundled preservation checker compares exact recognized-token
counts, protected blocks, line endings, and optional original-line boundaries.
Style allowlists never suppress preservation checks. Neither checker proves meaning.
Inputs are UTF-8 text, at most 8 MiB each. No file is modified.

Exit 0: advisory scan completed (findings may remain). Exit 1: --fail-on was requested
and its style threshold or a source-comparison warning matched. Exit 2: invalid input.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

if __name__ == "__main__":
    # Running the checker must not create a cache in the installed plugin.
    sys.dont_write_bytecode = True

from preservation_check import (
    MAX_BYTES,
    PATTERNS as PRESERVATION_PATTERNS,
    block_spans,
    compare,
    decode_utf8,
    parse_ranges,
    read_utf8,
)

SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Hit:
    severity: str
    category: str
    line: int
    excerpt: str
    note: str


# --------------------------------------------------------------------------------------
# Text preparation
# --------------------------------------------------------------------------------------

INLINE_CODE_RE = dict(PRESERVATION_PATTERNS)["inline_code"]
URL_RE = re.compile(r"https?://\S+")


def prepare_lines(text: str):
    """Return list of (lineno, raw, scan_text, kind).

    kind: 'code' (fence or frontmatter), 'quote', 'heading', 'bullet', 'table',
    'blank', 'prose'. Preserve line positions while masking inline code and URLs.
    """
    out = []
    protected = block_spans(text)
    spans = iter(protected)
    span = next(spans, None)
    offset = 0
    # Mask inline code separately between protected blocks. Delimiters inside
    # a fence, or on opposite sides of it, must not hide unrelated prose.
    masked_parts = []
    cursor = 0
    for start, end, _kind in protected:
        masked_parts.append(INLINE_CODE_RE.sub(
            lambda m: re.sub(r"[^\r\n]", " ", m.group()), text[cursor:start]))
        masked_parts.append(re.sub(r"[^\r\n]", " ", text[start:end]))
        cursor = end
    masked_parts.append(INLINE_CODE_RE.sub(
        lambda m: re.sub(r"[^\r\n]", " ", m.group()), text[cursor:]))
    masked = "".join(masked_parts)
    masked = URL_RE.sub(lambda m: " " * len(m.group()), masked)
    for i, line in enumerate(text.splitlines(keepends=True), start=1):
        raw = line.rstrip("\r\n")
        start, offset = offset, offset + len(line)
        scan = masked[start:offset]
        while span is not None and start >= span[1]:
            span = next(spans, None)
        if span is not None and span[0] <= start < span[1]:
            kind = "quote" if span[2] == "blockquote_line" else "code"
            out.append((i, raw, "", kind))
            continue
        s = raw.strip()
        scan = scan.rstrip("\r\n").replace("’", "'").replace("‘", "'")
        if not s:
            kind = "blank"
        elif s.startswith(">"):
            kind = "quote"
        elif re.match(r"^#{1,6}\s", s):
            kind = "heading"
        elif re.match(r"^([-*+•]|\d+[.)])\s+", s):
            kind = "bullet"
        elif s.startswith("|"):
            kind = "table"
        else:
            kind = "prose"
        out.append((i, raw, scan, kind))
    return out


def detect_lang(text: str) -> str:
    cyr = len(re.findall(r"[А-Яа-яЁёІіЇїЄєҐґ]", text))
    lat = len(re.findall(r"[A-Za-z]", text))
    if cyr > lat:
        if re.search(r"[ІіЇїЄєҐґ]", text):
            return "uk"
        return "ru"
    return "en"


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'’-]+\b", text, flags=re.UNICODE))


def excerpt_around(s: str, m: re.Match, width: int = 60) -> str:
    a = max(0, m.start() - width // 2)
    b = min(len(s), m.end() + width // 2)
    frag = s[a:b].strip()
    return ("…" if a > 0 else "") + frag + ("…" if b < len(s) else "")


# --------------------------------------------------------------------------------------
# Pattern tables
# Each entry: (regex, severity, category, note). Regexes are case-insensitive.
# Notes describe inspectable patterns and editorial decisions, not authorship.
# --------------------------------------------------------------------------------------

EN_PATTERNS = [
    # Chatbot leakage and placeholders: almost never legitimate in a finished document.
    (r"\bI hope (this|my) (message|email|note) finds you\b", "high", "chatbot-leakage", "Canned opener"),
    (r"\b(here'?s|here is|below is) (a|an|the|your|my) (revised|updated|draft|polished|rewritten|cleaner|refined|concise|summary|breakdown|overview|version)\b", "high", "chatbot-leakage", "Assistant framing left in the text"),
    (r"\b(let me know if you('d| would)? (like|want|need)|feel free to (reach out|let me know|ask)|i'?d be happy to|i hope this helps|would you like me to|happy to (help|adjust|refine))\b", "high", "chatbot-leakage", "Assistant sign-off"),
    (r"\b(great question|certainly!|absolutely!|as an ai|as a language model)\b", "high", "chatbot-leakage", "Chatbot register"),
    (r"\[(your|insert|name|date|company|manager|team|link|tbd|add)[^\]]{0,40}\]", "high", "placeholder", "Unfilled template slot"),
    (r"\b(INSERT_[A-Z_]+|PASTE_[A-Z_]+|20\d\d-XX-XX)\b|utm_source=|oaicite|contentReference|↩", "high", "placeholder", "Tool or placeholder residue"),

    # Significance puffery and superficial analysis.
    (r"\bplays? an? (crucial|key|vital|pivotal|significant|critical|central|important) role\b", "medium", "puffery", "Significance claim instead of the fact"),
    (r"\b(is|serves as|stands as) a (testament|reminder)\b", "medium", "puffery", "Puffery"),
    (r"\b(marks?|marking|represents?|representing) a (significant |major |key |pivotal |important )?(shift|turning point|milestone|step forward)\b", "medium", "puffery", "Significance framing"),
    (r"\b(setting the stage|paving the way|laying the groundwork) for\b", "medium", "puffery", "Significance framing"),
    (r"\b(underscores?|highlights?|emphasizes?|reflects?) (the |its |our )?(importance|significance|need|value|broader|commitment)\b", "medium", "puffery", "Commentary on significance"),
    (r"\b(evolving|ever-evolving|rapidly changing|dynamic) landscape\b", "medium", "puffery", "Stock phrase"),
    (r"\b(valuable|actionable|key) insights?\b", "medium", "puffery", "Stock phrase"),
    (r"\b(it'?s|it is) (worth noting|important to note|worth mentioning|important to remember)\b", "medium", "signposting", "Didactic aside"),
    (r"\b(notably|importantly|crucially|interestingly),", "low", "signposting", "Sentence-opening intensifier"),

    (r"\b(this|that|it|which|here'?s why (this|it)|why (this|it)) (really |also |still )?matters\b", "medium", "puffery", "'This matters' framing; check whether it adds information"),
    (r"^\s*#*\s*why (this|it) matters\b", "medium", "puffery", "'Why it matters' section"),

    # Participle tails that append a comment on significance.
    (r",\s+(ensuring|highlighting|underscoring|emphasizing|reflecting|showcasing|fostering|enabling|empowering|reinforcing|solidifying|cementing|paving|contributing to|positioning|driving|unlocking|demonstrating)\b", "medium", "participle-tail", "Trailing -ing clause that comments instead of informing"),

    # Copula avoidance.
    (r"\b(serves|stands|functions|acts) as (a|an|the|our)\b", "medium", "copula-avoidance", "Check whether is/are preserves the intended relationship"),
    (r"\b(boasts|boasting)\b", "medium", "copula-avoidance", "Check for unsupported promotion; preserve the substantive claim"),

    # Negative parallelism and corrective framing.
    (r"(\bnot|n't) (just|only|merely|simply) [^.;:!?\n]{1,80}?[,;]?\s*(but|it'?s|it is|they'?re|we'?re|this is)\b", "medium", "negative-parallelism", "'Not just X but Y'"),
    (r"\b(isn'?t|is not|wasn'?t|was not|aren'?t|are not) (just |only |really |simply )?about [^.;!?\n]{1,80}?[,;:—–-]\s*(it'?s|it is|they'?re|this is) (about )?", "medium", "negative-parallelism", "'This isn't about X, it's about Y'"),
    (r"(^|[.!?]\s+)(it'?s|this is|that'?s) not [^.;!?\n]{1,50}?[,;—–]\s*(it'?s|this is|that'?s) ", "medium", "negative-parallelism", "'It's not X, it's Y'"),
    (r"\bless about [^.;!?\n]{1,60}? (and|but) more about\b", "medium", "negative-parallelism", "Contrast framing"),
    (r"\brather than\b", "low", "negative-parallelism", "'Y rather than X'; check whether a real contrast is being made"),
    (r"\b(does not|doesn'?t|did not|didn'?t) (by itself |on its own |necessarily )?(establish|prove|guarantee|imply)\b", "medium", "corrective-disclaimer", "Possible evidence boundary; preserve uncertainty and causal limits"),
    (r"\bshould (be (treated|read|understood|seen|viewed) as|not be confused with)\b", "medium", "corrective-disclaimer", "Check whether the distinction carries necessary meaning"),
    (r"\b(based on|given) (the )?(available|provided|current) (information|data|evidence|sources)\b", "medium", "corrective-disclaimer", "Check source scope; preserve evidence-bearing qualifications"),
    (r"\bnot (widely|publicly|extensively) (available|documented|disclosed)\b", "medium", "corrective-disclaimer", "Check whether limited availability is the substantive claim"),

    # Reveal colons and rhetorical questions.
    (r"(^|[.!?]\s+)(the|here'?s the|and the) (result|answer|catch|fix|problem|kicker|twist|bottom line|takeaway|short version|reality|upshot|good news|bad news|key finding|main finding|key takeaway|key insight|big picture)\s*[:?]", "medium", "reveal-framing", "Setup-reveal construction"),
    (r"(^|[.!?]\s+)(why|how|what)\?\s+(because|simple|it)\b", "medium", "reveal-framing", "Rhetorical Q&A"),
    (r"\bhere'?s (why|how|what|the thing)\b", "medium", "reveal-framing", "Setup phrase"),

    # Signposting, purpose statements, wrap-ups.
    (r"(^|[.!?]\s+)(in (summary|conclusion|short)|to (summarize|sum up|conclude)|overall|ultimately|all in all),", "medium", "wrap-up", "Summary opener"),
    (r"\b(key takeaways?|tl;?dr)\b", "low", "wrap-up", "Recap block; keep only if the genre needs it"),
    (r"\bthis (document|doc|note|memo|section|update|report|proposal) (outlines|describes|provides|aims to|summarizes|presents|covers|details)\b", "medium", "purpose-statement", "Purpose statement instead of the point"),
    (r"\bthe (purpose|goal|aim|objective) of this (document|doc|note|memo|section|meeting|update)\b", "medium", "purpose-statement", "Purpose statement instead of the point"),
    (r"\blet'?s (dive|take a (closer )?look|explore|break (it|this) down|unpack|walk through)\b", "medium", "signposting", "Tour-guide signposting"),
    (r"\b(moving|going) forward,", "low", "signposting", "Corporate filler"),

    # Customer-service and consultant register.
    (r"\b(please )?don'?t hesitate to\b", "medium", "service-register", "Customer-service register"),
    (r"\bi wanted to (reach out|follow up|touch base|circle back)\b", "medium", "service-register", "Stock opener"),
    (r"\bthank you for your (patience|understanding)\b", "low", "service-register", "Customer-service register"),
    (r"\b(circle back|touch base|move the needle|low-hanging fruit|deep dive|double[- ]click on|level[- ]set|north star|game[- ]changer|best-in-class|world-class)\b", "medium", "idiom", "Corporate idiom; reads as inserted polish"),
    (r"\b(nail down|lean (in|into|toward)|weigh in|dial in|lands? (in|on|with))\b", "low", "idiom", "Native idiom; check it fits the author"),

    # Hedge stacking.
    (r"\b(may|might|could) (potentially|possibly|perhaps)\b", "medium", "hedge-stacking", "Possible stacked softeners; retain the original degree of uncertainty"),
    (r"\b(potentially|possibly) (could|may|might)\b", "medium", "hedge-stacking", "Possible stacked softeners; retain the original degree of uncertainty"),

    # Procedural self-report.
    (r"\bwhile (preserving|maintaining|retaining|keeping|ensuring)\b", "medium", "procedural-self-report", "AI change-summary formula"),
    (r"\b(ensured|ensuring|ensures|ensure) that\b", "low", "procedural-self-report", "'ensure that' clusters in AI summaries"),

    # Role drift in workplace documents (from the user's materials).
    (r"\b(accountable|responsible) owners?\b|\bowner matrix\b|\bdeliverables?\b", "low", "role-drift", "Management vocabulary; check the author has that authority"),
    (r"\b\d{1,2}\s*[–-]\s*\d{1,2}\s*min(ute)?s?\b", "low", "role-drift", "Timeboxed agenda; only if a timed agenda was requested"),
    (r"^\s*\**(purpose|duration|prepared( by)?|attendees|objective|owner|decision owner)\**\s*:", "low", "role-drift", "Ceremonial metadata field"),
]

# AI vocabulary. Strong: rare in plain workplace prose. Weak: common words that become a
# useful only as contextual cluster prompts. These are not authorship indicators.
EN_VOCAB_STRONG = [
    "delve", "delves", "delving", "tapestry", "testament", "pivotal", "vibrant", "intricate",
    "intricacies", "interplay", "underscore", "underscores", "underscored", "underscoring",
    "showcase", "showcases", "showcased", "showcasing", "foster", "fosters", "fostered",
    "fostering", "garner", "garnered", "bolster", "bolstered", "meticulous", "meticulously",
    "seamless", "seamlessly", "holistic", "synergy", "synergies", "multifaceted", "realm",
    "embark", "embarking", "harness", "harnessing", "cutting-edge", "ever-evolving",
    "paradigm", "quietly", "universally", "commendable", "invaluable", "nuanced",
    "transformative", "unwavering", "groundbreaking", "noteworthy", "elevate", "elevates",
    "empower", "empowers", "empowering", "spearheaded", "streamlined", "streamlining",
    "facilitate", "facilitates", "facilitating", "utilize", "utilizes", "utilizing",
    "utilization", "leveraging", "leveraged",
]
# Selected subset for additional co-occurrence review; not an era or authorship test.
EN_VOCAB_2026 = {"challenge", "challenges", "clearer", "dependable", "echoed", "foster", "leverage",
                 "matters", "multifaceted", "practical", "prioritize", "quietly", "steady", "universally"}
EN_VOCAB_WEAK = [
    "leverage", "leverages", "robust", "streamline", "enhance", "enhances", "enhanced",
    "enhancing", "align", "aligns", "aligned", "alignment", "comprehensive", "crucial",
    "actionable", "prioritize", "prioritizing", "dependable", "steady", "clearer", "echoed",
    "landscape", "navigate", "navigating", "optimize", "optimizing", "proactive",
    "proactively", "stakeholders", "scalable", "impactful", "key", "vital", "critical",
    "significant", "significantly", "essential", "ensure", "ensures", "ensuring", "matters",
    "practical", "challenges", "valuable", "effectively", "efficiently",
]

RU_PATTERNS = [
    (r"\bне (просто|только|столько) [^.;!?\n]{1,80}?,?\s*(а|но и|но)\b", "medium", "negative-parallelism", "«Не просто X, а Y»"),
    (r"\bэто не [^.;!?\n]{1,50}?[,—–-]\s*это\b", "medium", "negative-parallelism", "«Это не X, это Y»"),
    (r"\bиграет (важную|ключевую|решающую|значительную|центральную) роль\b", "medium", "puffery", "Шаблон значимости"),
    (r"\b(важно|стоит|следует|необходимо) (отметить|подчеркнуть|учитывать|понимать)\b", "medium", "signposting", "Дидактическая вставка"),
    (r"(^|[.!?]\s+)(в заключение|подводя итог|таким образом|в целом|итак|резюмируя),", "medium", "wrap-up", "Итоговая формула"),
    (r"\bв (современном|сегодняшнем) (мире|контексте)\b|\bна сегодняшний день\b", "medium", "puffery", "Пустая рамка"),
    (r"\b(данный|данная|данное|данные) (документ|подход|процесс|решение|отчёт|отчет|раздел|вопрос)\b", "medium", "officialese", "Возможный канцелярит; проверить регистр и значение"),
    (r"\b(является|являются|являлся|являлась)\b", "low", "copula-avoidance", "«является» вместо тире или «это»"),
    (r"\b(осуществля\w*|в рамках|в целях|с целью обеспечения|на постоянной основе)\b", "low", "officialese", "Канцелярит"),
    (r"\b(обеспечива\w+|позволяет|позволит)\b", "low", "participle-tail", "Комментарий о пользе вместо факта; проверить кластер"),
    (r",\s+(что позволяет|обеспечивая|подчёркивая|подчеркивая|демонстрируя|способствуя|позволяя)\b", "medium", "participle-tail", "Хвост-комментарий"),
    (r"\b(давайте (рассмотрим|разберём|разберем|посмотрим)|ниже (представлен|приведен|приведён))\w*\b", "medium", "signposting", "Экскурсоводская рамка"),
    (r"\b(надеюсь, это (поможет|было полезно)|если (нужно|хотите|потребуется),? (могу|я могу))\b", "high", "chatbot-leakage", "Реплика ассистента"),
    (r"\b(может|могут|могло) (потенциально|возможно)\b", "medium", "hedge-stacking", "Двойная оговорка"),
    (r"\b(ключев\w+|комплексн\w+|уникальн\w+|широк\w+ спектр\w*|максимально)\b", "low", "vocabulary", "Частое AI-слово; проверить кластер"),
]

UK_PATTERNS = [
    (r"\bне (просто|лише|тільки) [^.;!?\n]{1,80}?,?\s*(а|але й|а й)\b", "medium", "negative-parallelism", "«Не просто X, а Y»"),
    (r"\bце не [^.;!?\n]{1,50}?[,—–-]\s*це\b", "medium", "negative-parallelism", "«Це не X, це Y»"),
    (r"\bвідіграє (важливу|ключову|вирішальну|значну|центральну) роль\b", "medium", "puffery", "Шаблон значущості"),
    (r"\b(важливо|варто|слід|необхідно) (зазначити|відзначити|підкреслити|враховувати|розуміти)\b", "medium", "signposting", "Дидактична вставка"),
    (r"(^|[.!?]\s+)(на завершення|підсумовуючи|отже|загалом|таким чином),", "medium", "wrap-up", "Підсумкова формула"),
    (r"\bу (сучасному|сьогоднішньому) (світі|контексті)\b|\bна сьогоднішній день\b", "medium", "puffery", "Порожня рамка"),
    (r"\b(даний|дана|дане|дані) (документ|підхід|процес|рішення|звіт|розділ|питання)\b", "medium", "officialese", "Можливий канцелярит; перевірити регістр і значення"),
    (r"\b(здійсню\w*|у рамках|в рамках|з метою забезпечення|на постійній основі)\b", "low", "officialese", "Канцелярит"),
    (r",\s+(що дозволяє|забезпечуючи|підкреслюючи|демонструючи|сприяючи|дозволяючи)\b", "medium", "participle-tail", "Хвіст-коментар"),
    (r"\b(давайте (розглянемо|розберемо|подивимось)|нижче (наведено|представлено))\b", "medium", "signposting", "Екскурсоводська рамка"),
    (r"\b(сподіваюся, це (допоможе|було корисно)|якщо (потрібно|хочете),? (можу|я можу))\b", "high", "chatbot-leakage", "Репліка асистента"),
    (r"\b(ключов\w+|комплексн\w+|унікальн\w+|широк\w+ спектр\w*|максимально)\b", "low", "vocabulary", "Часте AI-слово; перевірити кластер"),
]

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U00002B50\U00002705\U0000274C]"
)
BOLD_LEAD_BULLET_RE = re.compile(r"^\s*([-*+•]|\d+[.)])\s+\*\*[^*]{1,60}\*\*\s*[:—–-]?")
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
TRIPLET_RE = re.compile(r"\b[\w-]+(?: [\w-]+){0,2}, [\w-]+(?: [\w-]+){0,2},? (and|or|и|та|і) [\w-]+", re.UNICODE)
SMALL_WORDS = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by", "at", "vs", "via", "from", "as", "is"}


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------

def scan_patterns(lines, patterns, hits):
    compiled = [(re.compile(p, re.IGNORECASE | re.MULTILINE | re.UNICODE), sev, cat, note) for p, sev, cat, note in patterns if not p.startswith("^")]
    line_anchored = [(re.compile(p, re.IGNORECASE | re.UNICODE), sev, cat, note) for p, sev, cat, note in patterns if p.startswith("^")]
    for lineno, _raw, scan, kind in lines:
        if kind in ("code", "quote", "blank"):
            continue
        for rx, sev, cat, note in line_anchored:
            for m in rx.finditer(scan):
                hits.append(Hit(sev, cat, lineno, excerpt_around(scan, m), note))
    # Join wrapped prose lines into paragraphs so phrases split across lines are found.
    blocks = []  # (text, [(offset, lineno), ...])
    cur_text, cur_map = "", []
    for lineno, _raw, scan, kind in lines:
        if kind == "prose":
            if cur_text:
                cur_text += " "
            cur_map.append((len(cur_text), lineno))
            cur_text += scan.strip()
            continue
        if cur_text:
            blocks.append((cur_text, cur_map))
            cur_text, cur_map = "", []
        if kind in ("heading", "bullet", "table"):
            blocks.append((scan, [(0, lineno)]))
    if cur_text:
        blocks.append((cur_text, cur_map))

    def line_of(mapping, pos):
        ln = mapping[0][1]
        for off, n in mapping:
            if off <= pos:
                ln = n
        return ln

    seen = set()
    for text, mapping in blocks:
        for rx, sev, cat, note in compiled:
            for m in rx.finditer(text):
                ln = line_of(mapping, m.start())
                key = (cat, ln, m.start())
                if key in seen:
                    continue
                seen.add(key)
                hits.append(Hit(sev, cat, ln, excerpt_around(text, m), note))


def scan_vocab(lines, total_words, hits, summary):
    prose = [(n, s) for n, _r, s, k in lines if k not in ("code", "quote", "blank")]
    strong_found = {}
    weak_found = {}
    for n, s in prose:
        for w in re.findall(r"[A-Za-z][A-Za-z-]+", s):
            lw = w.lower()
            if lw in EN_VOCAB_STRONG:
                strong_found.setdefault(lw, []).append(n)
            elif lw in EN_VOCAB_WEAK:
                weak_found.setdefault(lw, []).append(n)
    for w, ns in sorted(strong_found.items()):
        hits.append(Hit("medium", "ai-vocabulary", ns[0], w + (f" (x{len(ns)}, lines {', '.join(map(str, ns[:6]))})" if len(ns) > 1 else ""),
                        "Vocabulary candidate; check meaning, domain use and author voice before editing"))
    weak_total = sum(len(v) for v in weak_found.values())
    per_k = 1000 * weak_total / max(total_words, 1)
    summary["weak_vocab_per_1000_words"] = round(per_k, 1)
    if weak_found:
        listing = ", ".join(f"{w} x{len(v)}" for w, v in sorted(weak_found.items(), key=lambda kv: -len(kv[1])))
        era = sorted(set(weak_found) & EN_VOCAB_2026 | set(strong_found) & EN_VOCAB_2026)
        summary["vocab_2026_set"] = era
        if (per_k >= 20 and weak_total >= 4) or len(weak_found) >= 6 or len(era) >= 3:
            sev = "medium"
        else:
            sev = "low"
        hits.append(Hit(sev, "ai-vocabulary-cluster", min(v[0] for v in weak_found.values()), listing,
                        f"Vocabulary cluster candidate ({per_k:.0f} per 1000 words; medium at 20+ per 1000, 6+ distinct, or 3+ from the tracked-word subset)"))


def split_sentences(text: str):
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'“‘(\[]?[A-ZА-ЯЁІЇЄҐ0-9])", text)
    return [p.strip() for p in parts if word_count(p) >= 3]


def scan_rhythm(lines, lang, hits, summary):
    paragraphs, cur = [], []
    for n, _raw, scan, kind in lines:
        if kind == "prose":
            cur.append(scan)
        else:
            if cur:
                paragraphs.append(" ".join(cur))
                cur = []
    if cur:
        paragraphs.append(" ".join(cur))
    sentences = [s for p in paragraphs for s in split_sentences(p)]
    lengths = [word_count(s) for s in sentences]
    summary["prose_sentences"] = len(lengths)
    if len(lengths) < 8:
        return sentences
    mean = statistics.mean(lengths)
    sd = statistics.pstdev(lengths)
    cv = sd / mean if mean else 0
    band = sum(1 for x in lengths if 8 <= x <= 20) / len(lengths)
    summary["sentence_length_mean"] = round(mean, 1)
    summary["sentence_length_cv"] = round(cv, 2)
    summary["share_in_8_20_band"] = round(band, 2)
    if cv < 0.35:
        hits.append(Hit("medium", "uniform-rhythm", 0, f"mean {mean:.1f} words, CV {cv:.2f}",
                        "Even sentence lengths; check readability and genre before changing rhythm"))
    short_share = sum(1 for x in lengths if x <= 10) / len(lengths)
    summary["share_sentences_10_words_or_less"] = round(short_share, 2)
    if mean < 11 or short_share >= 0.6:
        hits.append(Hit("medium", "staccato", 0, f"mean {mean:.1f} words, {short_share:.0%} of sentences are 10 words or fewer",
                        "Short-sentence cluster; combine only when it improves the actual reasoning"))
    starts = [re.match(r"[\"'“(]*([A-Za-zА-Яа-яЁёІіЇїЄєҐґ]+)", s) for s in sentences]
    demo = sum(1 for m in starts if m and m.group(1).lower() in ("this", "these", "it", "that", "это", "этот", "эта", "це", "цей", "ця"))
    if demo / len(sentences) >= 0.3:
        hits.append(Hit("low", "demonstrative-chain", 0, f"{demo}/{len(sentences)} sentences start with This/It/That",
                        "Repeated demonstratives; check whether references are clear"))
    if band >= 0.8 and lang == "en":
        hits.append(Hit("medium", "uniform-rhythm", 0, f"{band:.0%} of sentences are 8-20 words",
                        "Concentrated sentence-length band; check whether the genre benefits from consistency"))
    # Paragraphs that all have the same number of sentences.
    counts = [len(split_sentences(p)) for p in paragraphs if word_count(p) >= 25]
    if len(counts) >= 4 and max(counts) - min(counts) <= 1:
        hits.append(Hit("low", "uniform-paragraphs", 0, f"sentences per paragraph: {counts}",
                        "Paragraphs have the same shape"))
    return sentences


def scan_format(lines, text, lang, total_words, hits, summary):
    # Em dashes (not flagged for ru/uk, where the dash is standard punctuation).
    em = [(n, s) for n, _r, s, k in lines if k not in ("code", "quote") for _ in range(s.count("—"))]
    spaced_en = [(n, s) for n, _r, s, k in lines if k not in ("code", "quote") and re.search(r"\w – \w", s)]
    summary["em_dashes"] = len(em)
    if lang == "en":
        if em:
            per = 300 * len(em) / max(total_words, 1)
            sev = "medium" if per >= 1 or len(em) >= 3 else "low"
            lines_list = sorted({n for n, _ in em})
            hits.append(Hit(sev, "em-dash", lines_list[0], f"{len(em)} em dash(es), lines {', '.join(map(str, lines_list[:10]))}",
                            "Dash frequency candidate; keep useful punctuation and the author's demonstrated habits"))
        if spaced_en:
            hits.append(Hit("low", "em-dash", spaced_en[0][0], f"{len(spaced_en)} spaced en dash(es) used as em dash",
                            "Spaced en dash; judge the target language and established style"))
        # Punctuation monotony: no ; ( : in a longer prose text.
        prose_text = " ".join(s for _n, _r, s, k in lines if k == "prose")
        if word_count(prose_text) >= 250 and not re.search(r"[;()]", prose_text) and not em:
            hits.append(Hit("low", "punctuation-monotony", 0, "only commas and periods in 250+ words of prose",
                            "Limited punctuation variety; do not introduce variety without a readability benefit"))

    # Bold lead-in bullets ("- **Performance:** ...").
    blb = [n for n, _raw, s, k in lines if k == "bullet" and BOLD_LEAD_BULLET_RE.match(s)]
    if len(blb) >= 2:
        hits.append(Hit("medium" if len(blb) >= 3 else "low", "inline-header-list", blb[0], f"{len(blb)} bullets start with a bold label",
                        "Inline-header vertical list"))
    bold_prose = sum(len(BOLD_RE.findall(s)) for n, _raw, s, k in lines if k == "prose")
    if bold_prose >= 3:
        hits.append(Hit("medium", "bold-overuse", 0, f"{bold_prose} bold spans in prose", "Boldface in running text"))

    # Emoji.
    em_lines = [n for n, _raw, s, k in lines if k not in ("code", "quote") and EMOJI_RE.search(s)]
    if em_lines:
        hits.append(Hit("medium", "emoji", em_lines[0], f"emoji on {len(em_lines)} line(s)", "Emoji; check the channel and author's demonstrated voice"))

    # Headings.
    heads = [(n, re.sub(r"^#+\s*", "", raw.strip())) for n, raw, _s, k in lines if k == "heading"]
    title_case = []
    for n, h in heads:
        words = [w for w in re.findall(r"[A-Za-z][\w'-]*", h)]
        content = [w for w in words if w.lower() not in SMALL_WORDS]
        if len(content) >= 3 and sum(1 for w in content[1:] if w[0].isupper() and not w.isupper()) >= len(content[1:]) * 0.8:
            title_case.append(n)
    if title_case:
        hits.append(Hit("low", "title-case-headings", title_case[0], f"{len(title_case)} heading(s) in Title Case",
                        "Check heading case against the requested style"))
    if heads and total_words < 400 and len(heads) >= 3:
        hits.append(Hit("medium", "formatting-overuse", heads[0][0], f"{len(heads)} headings in {total_words} words",
                        "Several headings in a short text; check navigation needs and required structure"))
    if lang == "en":
        h1 = [n for n, raw, _s, k in lines if k == "heading" and raw.strip().startswith("# ")]
        if len(h1) > 1:
            hits.append(Hit("low", "formatting-overuse", h1[1], f"{len(h1)} level-1 headings", "Multiple top-level headings; check the document structure"))

    # Curly quotes (Word autocorrect also produces these, so low).
    visible_prose = "\n".join(s for _n, _raw, s, k in lines if k not in ("code", "quote"))
    if lang == "en" and re.search(r"[“”‘’]", visible_prose):
        hits.append(Hit("low", "curly-quotes", 0, "curly quotes present",
                        "Curly quotation marks; check typographic consistency without changing quoted content"))

    # Horizontal rules as section dividers in short docs.
    hr = [n for n, raw, _s, k in lines if k != "code" and re.match(r"^\s*(---|\*\*\*|___)\s*$", raw)]
    if len(hr) >= 2 and total_words < 800:
        hits.append(Hit("low", "formatting-overuse", hr[0], f"{len(hr)} horizontal rules", "Section dividers; check whether they aid navigation"))


def scan_triplets(sentences, hits, summary):
    if len(sentences) < 6:
        return
    with_triplet = [s for s in sentences if TRIPLET_RE.search(s)]
    share = len(with_triplet) / len(sentences)
    summary["share_sentences_with_3_item_list"] = round(share, 2)
    if share >= 0.25 and len(with_triplet) >= 3:
        ex = TRIPLET_RE.search(with_triplet[0]).group(0)
        hits.append(Hit("medium", "rule-of-three", 0, f"{len(with_triplet)}/{len(sentences)} sentences contain an 'X, Y, and Z' list, e.g. \"{ex}\"",
                        "Three-item list pattern; preserve distinct items and intentional parallelism"))


def scan_repetition_openers(lines, hits):
    openers = {}
    for n, raw, s, k in lines:
        if k not in ("prose", "bullet"):
            continue
        body = re.sub(r"^\s*([-*+•]|\d+[.)])\s+", "", s).strip()
        body = re.sub(r"^\**[^*]{0,40}\**\s*:\s*", "", body)
        m = re.match(r"([A-Za-zА-Яа-яЁёІіЇїЄєҐґ']+\s+[A-Za-zА-Яа-яЁёІіЇїЄєҐґ']+)", body)
        if m:
            openers.setdefault(m.group(1).lower(), []).append(n)
    for op, ns in openers.items():
        if len(ns) >= 3 and op.split()[0] not in ("the", "a", "i", "we", "it", "this", "in"):
            hits.append(Hit("low", "repeated-opener", ns[0], f"'{op} …' starts {len(ns)} lines ({', '.join(map(str, ns[:6]))})",
                            "Repeated opener; check whether parallelism serves the content"))


# --------------------------------------------------------------------------------------
# Legacy token-presence view retained for CLI compatibility.
# Compares concrete tokens (numbers, dates, identifiers, code spans, URLs) between the
# source and the draft. It sees presence only: it does not understand meaning, cannot tell
# that a claim was reversed, and does not count repeats. The integrated preservation
# result below is the authoritative mechanical comparison for counts and protected blocks.
# --------------------------------------------------------------------------------------

TOKEN_RES = [
    ("number", re.compile(r"(?<![\w.])[-+]?\d(?:[\d,.:  ]*\d)?(?:\s?(?:%|ms|s|sec|min|h|hrs?|days?|GB|MB|TB|KB|k|K|M|x|×|USD|EUR|\$|credits?))?(?![\w])")),
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}\b", re.I)),
    ("code", re.compile(r"`[^`\n]+`")),
    ("url", URL_RE),
    ("identifier", re.compile(r"\b[A-Za-z]+(?:_[A-Za-z0-9]+)+\b|\b[A-Z]{2,}[A-Z0-9_-]*\d*\b|\b[a-z]+[A-Z][A-Za-z0-9]+\b|\b[A-Z][a-z]+[A-Z][A-Za-z0-9]+\b")),
]
LIST_MARKER_RE = re.compile(r"^\s*\d+[.)]\s+", re.MULTILINE)
COMMON_CAPS = {"OK", "FYI", "ASAP", "AM", "PM", "TLDR", "PS"}
NEGATION_RE = re.compile(r"\b(not|no|never|none|without|cannot)\b|n't\b|\b(не|нет|ни|никогда|без|ні|ніколи)\b", re.I)


def norm_num(s: str) -> str:
    # Whitespace may group digits, but commas can be decimal separators (e.g. 1,5%).
    # Preserve ambiguous punctuation and report it for review instead of losing precision.
    return re.sub(r"\s", "", s).rstrip(".:").lower()


def extract_tokens(text: str):
    text = LIST_MARKER_RE.sub("", text)  # list numbering is not a fact
    found = {}
    for kind, rx in TOKEN_RES:
        items = set()
        for m in rx.finditer(text):
            v = m.group(0)
            if kind == "number":
                v = norm_num(v)
            elif kind == "code":
                v = v.strip("`").strip()
            elif kind == "url":
                v = v.strip()
            else:
                v = v.strip().rstrip(".,)")
            if v and not (kind == "identifier" and v in COMMON_CAPS):
                items.add(v)
        found[kind] = items
    return found


def token_present(kind: str, item: str, text: str, nums: set) -> bool:
    if kind == "number":
        return item in nums
    # Exact token match: "acct_id" must not be satisfied by "old_acct_id".
    rx = re.compile(r"(?<![\w])" + re.escape(item) + r"(?![\w])")
    return rx.search(text) is not None


def token_diff(src: str, out: str):
    src_t, out_t = extract_tokens(src), extract_tokens(out)
    out_clean = LIST_MARKER_RE.sub("", out)
    src_clean = LIST_MARKER_RE.sub("", src)
    missing = [(k, v) for k in src_t for v in sorted(src_t[k]) if not token_present(k, v, out_clean, out_t["number"])]
    added = [(k, v) for k in out_t for v in sorted(out_t[k]) if not token_present(k, v, src_clean, src_t["number"])]
    neg = (len(NEGATION_RE.findall(src.replace("’", "'"))),
           len(NEGATION_RE.findall(out.replace("’", "'"))))
    return missing, added, neg


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

# Technical compounds that contain listed words but are normal terms. Masked by default.
DEFAULT_ALLOW = [
    "primary key", "foreign key", "sort key", "clustering key", "cluster key", "partition key",
    "surrogate key", "natural key", "composite key", "unique key", "hash key", "api key",
    "key-value", "key value", "key pair", "keyboard", "key column", "key columns",
    "critical section", "critical path", "landscape mode", "landscape orientation",
    "underscore character", "robust regression", "robust statistics", "significant digits",
    "statistically significant", "streamlit",
]

# Categories describing whole-text shape. Their combination suggests contextual
# structure review; it never establishes a defect or requires rebuilding.
STRUCTURAL = {"inline-header-list", "formatting-overuse", "purpose-statement", "wrap-up",
              "uniform-rhythm", "staccato", "rule-of-three", "bold-overuse", "uniform-paragraphs"}


def mask_allowed(text: str, phrases):
    """Mask accepted phrases while retaining word counts and original line breaks."""
    # Match horizontal whitespace or a single soft line wrap, never a blank paragraph.
    whitespace = r"(?:[^\S\r\n]+|[^\S\r\n]*\r?\n[^\S\r\n]*)"
    for ph in phrases:
        words = ph.split()
        if not words:
            continue
        pattern = whitespace.join(map(re.escape, words))
        rx = re.compile(r"(?<![\w])" + pattern + r"(?![\w])", re.I)
        text = rx.sub(lambda m: re.sub(r"\S+", "ok", m.group(0)), text)
    return text


def run(text: str, lang: str, source, allow=(), allow_categories=()):
    original = text
    text = mask_allowed(text, list(DEFAULT_ALLOW) + list(allow))
    lines = prepare_lines(text)
    if lang == "auto":
        lang = detect_lang(text)
    total_words = word_count(" ".join(s for _n, _r, s, k in lines if k not in ("code",)))
    hits: list[Hit] = []
    summary = {"language": lang, "words": total_words,
               "interpretation": "Heuristic candidates only; severity is signal strength, not harm or authorship confidence."}

    patterns = {"en": EN_PATTERNS, "ru": RU_PATTERNS, "uk": UK_PATTERNS}[lang]
    scan_patterns(lines, patterns, hits)
    if lang != "en":
        # Mixed documents: English tells inside a Russian/Ukrainian doc still count.
        scan_patterns(lines, [p for p in EN_PATTERNS if p[1] == "high"], hits)
    scan_vocab(lines, total_words, hits, summary)
    sentences = scan_rhythm(lines, lang, hits, summary)
    scan_format(lines, text, lang, total_words, hits, summary)
    scan_triplets(sentences, hits, summary)
    scan_repetition_openers(lines, hits)

    if allow_categories:
        hits = [h for h in hits if h.category not in set(allow_categories)]

    # Category-level escalation: the same medium tell 3+ times becomes high.
    by_cat = {}
    for h in hits:
        if h.severity == "medium":
            by_cat.setdefault(h.category, []).append(h)
    for cat, hs in by_cat.items():
        if len(hs) >= 3 and cat not in ("ai-vocabulary",):
            for h in hs:
                h.severity = "high"
                h.note += " (repeated 3+ times: escalated)"
    rather = [h for h in hits if "'Y rather than X'" in h.note]
    if len(rather) >= 2:
        for h in rather:
            h.severity = "medium"
            h.note += f" ({len(rather)} in this text: escalated)"
    strong_vocab = [h for h in hits if h.category == "ai-vocabulary"]
    if len(strong_vocab) >= 4:
        for h in strong_vocab:
            h.severity = "high"
            h.note += " (4+ distinct AI words: escalated)"

    diff = token_diff(source, original) if source is not None else None
    hits.sort(key=lambda h: (-SEVERITY_ORDER[h.severity], h.line, h.category))
    summary["counts"] = {s: sum(1 for h in hits if h.severity == s) for s in ("high", "medium", "low")}

    # Advisory suggestion only. The editor decides patch vs rebuild from role, genre and
    # structure (SKILL.md step 3); this line just reports what the patterns point to.
    weight = 3 * summary["counts"]["high"] + summary["counts"]["medium"]
    structural = sorted({h.category for h in hits if h.severity != "low" and h.category in STRUCTURAL})
    density = 100 * weight / max(total_words, 1)
    if total_words >= 80 and (len(structural) >= 2 or (weight >= 6 and density >= 8)):
        why = ", ".join(structural) if structural else f"{weight} weighted hits in {total_words} words"
        summary["suggestion"] = f"structure-review candidate ({why}); rebuild only for a confirmed role, genre or organization problem"
    elif weight:
        summary["suggestion"] = "review candidates in context; edit only confirmed defects"
    elif hits:
        summary["suggestion"] = "only low hits; look at them, no rewrite needed on their account"
    else:
        summary["suggestion"] = "no pattern hits; do the manual read"
    return hits, summary, diff


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="draft file, or - for stdin")
    ap.add_argument("--source", help="original UTF-8 text; run token and exact-count preservation checks")
    ap.add_argument("--lang", default="auto", choices=["auto", "en", "ru", "uk"])
    ap.add_argument("--allow", action="append", default=[], metavar="PHRASE",
                    help="phrase accepted in this text (term of art, quotation, required wording); repeatable")
    ap.add_argument("--allow-category", action="append", default=[], metavar="CATEGORY",
                    help="drop a whole category for this text, e.g. em-dash when the author uses them; repeatable")
    ap.add_argument("--allow-lines", action="append", default=None, metavar="START:END",
                    help="permitted inclusive ORIGINAL line range; requires --source; repeatable")
    ap.add_argument("--protect", action="append", default=[], metavar="LITERAL",
                    help="exact source text whose occurrence count must remain; requires --source; repeatable")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["high", "medium"], help=(
        "exit 1 on style candidates at this level or above, any preservation issue, "
        "missing/added tokens, or a changed negation count; advisory exit 0 without this flag"))
    args = ap.parse_args(argv)
    if (args.allow_lines is not None or args.protect) and args.source is None:
        ap.error("--allow-lines and --protect require --source")

    try:
        text = (decode_utf8(sys.stdin.buffer.read(MAX_BYTES + 1), "<stdin>")
                if args.path == "-" else read_utf8(Path(args.path)))
        source = read_utf8(Path(args.source)) if args.source is not None else None
        ranges = (parse_ranges(args.allow_lines, len(source.splitlines()))
                  if args.allow_lines is not None else None)
        preservation = (compare(source, text, literals=args.protect, ranges=ranges)
                        if source is not None else None)
        hits, summary, diff = run(text, args.lang, source, args.allow, args.allow_category)
        missing, added, neg = diff if diff else (None, None, None)
    except (OSError, ValueError) as exc:
        error = {"status": "error", "message": str(exc)}
        print(json.dumps(error, ensure_ascii=False) if args.json else f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        out = {"summary": summary, "hits": [asdict(h) for h in hits]}
        if diff:
            out["tokens_missing"] = [{"kind": k, "value": v} for k, v in missing]
            out["tokens_added"] = [{"kind": k, "value": v} for k, v in added]
            out["negations"] = {"source": neg[0], "draft": neg[1]}
            out["preservation"] = preservation
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        c = summary["counts"]
        print(f"language={summary['language']} words={summary['words']} high={c['high']} medium={c['medium']} low={c['low']}")
        print(f"suggestion: {summary['suggestion']}")
        print(summary["interpretation"])
        extra = {k: v for k, v in summary.items() if k not in ("language", "words", "counts", "suggestion", "interpretation")}
        if extra:
            print("stats: " + ", ".join(f"{k}={v}" for k, v in extra.items()))
        for h in hits:
            loc = f"L{h.line}" if h.line else "doc"
            print(f"[{h.severity.upper():6}] {h.category:24} {loc:6} {h.excerpt}\n         -> {h.note}")
        if not hits:
            print("no pattern hits (this does not prove the text reads well; do the manual read)")
        if diff:
            print("\nTOKEN CHECK (legacy presence view; exact counts and blocks are checked below)")
            if missing:
                print(f"  missing from draft ({len(missing)}):")
                for k, v in missing:
                    print(f"    {k:10} {v}")
            else:
                print("  missing from draft: none")
            if added:
                print(f"  new in draft, not in source ({len(added)}); each needs support from the user or the conversation:")
                for k, v in added:
                    print(f"    {k:10} {v}")
            else:
                print("  new in draft: none")
            if neg[0] != neg[1]:
                print(f"  negations: source {neg[0]}, draft {neg[1]}; re-read every negated claim against the source")
            print(f"\nPRESERVATION: {preservation['status']} ({preservation['issue_count']} issue(s))")
            for issue in preservation["issues"]:
                print(json.dumps(issue, ensure_ascii=False))
            print(preservation["limitations"])

    if args.fail_on:
        threshold = SEVERITY_ORDER[args.fail_on]
        if (any(SEVERITY_ORDER[h.severity] >= threshold for h in hits)
                or missing or added
                or (neg is not None and neg[0] != neg[1])
                or (preservation is not None and preservation["issues"])):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
