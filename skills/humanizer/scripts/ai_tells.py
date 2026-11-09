#!/usr/bin/env python3
"""Scan prose for common AI-writing tells and check that concrete tokens survived a rewrite.

Usage:
  python3 ai_tells.py DRAFT [--source ORIGINAL] [--lang auto|en|ru|uk]
                            [--allow PHRASE ...] [--allow-category CAT ...]
                            [--json] [--fail-on high|medium]
  cat draft.md | python3 ai_tells.py -

Standard library only (Python 3.8+). The scanner finds surface patterns and is advisory:
it does not judge authorship, a clean scan does not prove the text reads well, and its
suggestion line never overrides the editor's judgment of role, genre and structure.
Accept a legitimate phrase with --allow "primary key"; see references/patterns.md.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, asdict

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

FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
URL_RE = re.compile(r"https?://\S+")


def prepare_lines(text: str):
    """Return list of (lineno, raw, scan_text, kind).

    kind: 'code' (inside fence), 'quote', 'heading', 'bullet', 'table', 'blank', 'prose'.
    scan_text has inline code and URLs blanked so they are never flagged.
    """
    out = []
    in_fence = False
    for i, raw in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            out.append((i, raw, "", "code"))
            continue
        if in_fence:
            out.append((i, raw, "", "code"))
            continue
        s = raw.strip()
        scan = URL_RE.sub(" ", INLINE_CODE_RE.sub(" ", raw)).replace("’", "'").replace("‘", "'")
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
# Source tags in notes: [WP] Wikipedia "Signs of AI writing"; [M] user's research
# materials; [D] design choice of this skill.
# --------------------------------------------------------------------------------------

EN_PATTERNS = [
    # Chatbot leakage and placeholders: almost never legitimate in a finished document.
    (r"\bI hope (this|my) (message|email|note) finds you\b", "high", "chatbot-leakage", "Canned opener [WP]"),
    (r"\b(here'?s|here is|below is) (a|an|the|your|my) (revised|updated|draft|polished|rewritten|cleaner|refined|concise|summary|breakdown|overview|version)\b", "high", "chatbot-leakage", "Assistant framing left in the text [WP]"),
    (r"\b(let me know if you('d| would)? (like|want|need)|feel free to (reach out|let me know|ask)|i'?d be happy to|i hope this helps|would you like me to|happy to (help|adjust|refine))\b", "high", "chatbot-leakage", "Assistant sign-off [WP]"),
    (r"\b(great question|certainly!|absolutely!|as an ai|as a language model)\b", "high", "chatbot-leakage", "Chatbot register [WP]"),
    (r"\[(your|insert|name|date|company|manager|team|link|tbd|add)[^\]]{0,40}\]", "high", "placeholder", "Unfilled template slot [WP]"),
    (r"\b(INSERT_[A-Z_]+|PASTE_[A-Z_]+|20\d\d-XX-XX)\b|utm_source=|oaicite|contentReference|↩", "high", "placeholder", "Tool or placeholder residue [WP]"),

    # Significance puffery and superficial analysis.
    (r"\bplays? an? (crucial|key|vital|pivotal|significant|critical|central|important) role\b", "medium", "puffery", "Significance claim instead of the fact [WP]"),
    (r"\b(is|serves as|stands as) a (testament|reminder)\b", "medium", "puffery", "Puffery [WP]"),
    (r"\b(marks?|marking|represents?|representing) a (significant |major |key |pivotal |important )?(shift|turning point|milestone|step forward)\b", "medium", "puffery", "Significance framing [WP]"),
    (r"\b(setting the stage|paving the way|laying the groundwork) for\b", "medium", "puffery", "Significance framing [WP]"),
    (r"\b(underscores?|highlights?|emphasizes?|reflects?) (the |its |our )?(importance|significance|need|value|broader|commitment)\b", "medium", "puffery", "Commentary on significance [WP]"),
    (r"\b(evolving|ever-evolving|rapidly changing|dynamic) landscape\b", "medium", "puffery", "Stock phrase [WP]"),
    (r"\b(valuable|actionable|key) insights?\b", "medium", "puffery", "Stock phrase [WP]"),
    (r"\b(it'?s|it is) (worth noting|important to note|worth mentioning|important to remember)\b", "medium", "signposting", "Didactic aside [WP]"),
    (r"\b(notably|importantly|crucially|interestingly),", "low", "signposting", "Sentence-opening intensifier [WP]"),

    (r"\b(this|that|it|which|here'?s why (this|it)|why (this|it)) (really |also |still )?matters\b", "medium", "puffery", "'This matters' framing; 2026-era tell [WP]"),
    (r"^\s*#*\s*why (this|it) matters\b", "medium", "puffery", "'Why it matters' section [WP][D]"),

    # Participle tails that append a comment on significance.
    (r",\s+(ensuring|highlighting|underscoring|emphasizing|reflecting|showcasing|fostering|enabling|empowering|reinforcing|solidifying|cementing|paving|contributing to|positioning|driving|unlocking|demonstrating)\b", "medium", "participle-tail", "Trailing -ing clause that comments instead of informing [WP]"),

    # Copula avoidance.
    (r"\b(serves|stands|functions|acts) as (a|an|the|our)\b", "medium", "copula-avoidance", "Use is/are [WP]"),
    (r"\b(boasts|boasting)\b", "medium", "copula-avoidance", "Use has [WP]"),

    # Negative parallelism and corrective framing.
    (r"(\bnot|n't) (just|only|merely|simply) [^.;:!?\n]{1,80}?[,;]?\s*(but|it'?s|it is|they'?re|we'?re|this is)\b", "medium", "negative-parallelism", "'Not just X but Y' [WP]"),
    (r"\b(isn'?t|is not|wasn'?t|was not|aren'?t|are not) (just |only |really |simply )?about [^.;!?\n]{1,80}?[,;:—–-]\s*(it'?s|it is|they'?re|this is) (about )?", "medium", "negative-parallelism", "'This isn't about X, it's about Y' [WP]"),
    (r"(^|[.!?]\s+)(it'?s|this is|that'?s) not [^.;!?\n]{1,50}?[,;—–]\s*(it'?s|this is|that'?s) ", "medium", "negative-parallelism", "'It's not X, it's Y' [WP]"),
    (r"\bless about [^.;!?\n]{1,60}? (and|but) more about\b", "medium", "negative-parallelism", "Contrast framing [D]"),
    (r"\brather than\b", "low", "negative-parallelism", "'Y rather than X'; fine once, a tell when repeated [WP]"),
    (r"\b(does not|doesn'?t|did not|didn'?t) (by itself |on its own |necessarily )?(establish|prove|guarantee|imply)\b", "medium", "corrective-disclaimer", "Mid-2026 corrective disclaimer [WP]"),
    (r"\bshould (be (treated|read|understood|seen|viewed) as|not be confused with)\b", "medium", "corrective-disclaimer", "Corrective framing [WP]"),
    (r"\b(based on|given) (the )?(available|provided|current) (information|data|evidence|sources)\b", "medium", "corrective-disclaimer", "Hedging disclaimer about sources [WP]"),
    (r"\bnot (widely|publicly|extensively) (available|documented|disclosed)\b", "medium", "corrective-disclaimer", "Hedging disclaimer [WP]"),

    # Reveal colons and rhetorical questions.
    (r"(^|[.!?]\s+)(the|here'?s the|and the) (result|answer|catch|fix|problem|kicker|twist|bottom line|takeaway|short version|reality|upshot|good news|bad news|key finding|main finding|key takeaway|key insight|big picture)\s*[:?]", "medium", "reveal-framing", "Setup-reveal construction [D]"),
    (r"(^|[.!?]\s+)(why|how|what)\?\s+(because|simple|it)\b", "medium", "reveal-framing", "Rhetorical Q&A [D]"),
    (r"\bhere'?s (why|how|what|the thing)\b", "medium", "reveal-framing", "Setup phrase [D]"),

    # Signposting, purpose statements, wrap-ups.
    (r"(^|[.!?]\s+)(in (summary|conclusion|short)|to (summarize|sum up|conclude)|overall|ultimately|all in all),", "medium", "wrap-up", "Summary opener [WP]"),
    (r"\b(key takeaways?|tl;?dr)\b", "low", "wrap-up", "Recap block; keep only if the genre needs it [WP]"),
    (r"\bthis (document|doc|note|memo|section|update|report|proposal) (outlines|describes|provides|aims to|summarizes|presents|covers|details)\b", "medium", "purpose-statement", "Purpose statement instead of the point [M]"),
    (r"\bthe (purpose|goal|aim|objective) of this (document|doc|note|memo|section|meeting|update)\b", "medium", "purpose-statement", "Purpose statement instead of the point [M]"),
    (r"\blet'?s (dive|take a (closer )?look|explore|break (it|this) down|unpack|walk through)\b", "medium", "signposting", "Tour-guide signposting [WP]"),
    (r"\b(moving|going) forward,", "low", "signposting", "Corporate filler [D]"),

    # Customer-service and consultant register.
    (r"\b(please )?don'?t hesitate to\b", "medium", "service-register", "Customer-service register [WP]"),
    (r"\bi wanted to (reach out|follow up|touch base|circle back)\b", "medium", "service-register", "Stock opener [D]"),
    (r"\bthank you for your (patience|understanding)\b", "low", "service-register", "Customer-service register [WP]"),
    (r"\b(circle back|touch base|move the needle|low-hanging fruit|deep dive|double[- ]click on|level[- ]set|north star|game[- ]changer|best-in-class|world-class)\b", "medium", "idiom", "Corporate idiom; reads as inserted polish [D]"),
    (r"\b(nail down|lean (in|into|toward)|weigh in|dial in|lands? (in|on|with))\b", "low", "idiom", "Native idiom; check it fits the author [M]"),

    # Hedge stacking.
    (r"\b(may|might|could) (potentially|possibly|perhaps)\b", "medium", "hedge-stacking", "Two hedges where one will do [M]"),
    (r"\b(potentially|possibly) (could|may|might)\b", "medium", "hedge-stacking", "Two hedges where one will do [M]"),

    # Procedural self-report.
    (r"\bwhile (preserving|maintaining|retaining|keeping|ensuring)\b", "medium", "procedural-self-report", "AI change-summary formula [WP]"),
    (r"\b(ensured|ensuring|ensures|ensure) that\b", "low", "procedural-self-report", "'ensure that' clusters in AI summaries [WP]"),

    # Role drift in workplace documents (from the user's materials).
    (r"\b(accountable|responsible) owners?\b|\bowner matrix\b|\bdeliverables?\b", "low", "role-drift", "Management vocabulary; check the author has that authority [M]"),
    (r"\b\d{1,2}\s*[–-]\s*\d{1,2}\s*min(ute)?s?\b", "low", "role-drift", "Timeboxed agenda; only if a timed agenda was requested [M]"),
    (r"^\s*\**(purpose|duration|prepared( by)?|attendees|objective|owner|decision owner)\**\s*:", "low", "role-drift", "Ceremonial metadata field [M]"),
]

# AI vocabulary. Strong: rare in plain workplace prose. Weak: common words that become a
# tell only in clusters. Lists combine the era lists in [WP] and common corporate-AI words [D].
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
# Words listed by [WP] for "mid-2026 and on" output; three or more distinct ones together is a tell.
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
    (r"\bне (просто|только|столько) [^.;!?\n]{1,80}?,?\s*(а|но и|но)\b", "medium", "negative-parallelism", "«Не просто X, а Y» [D]"),
    (r"\bэто не [^.;!?\n]{1,50}?[,—–-]\s*это\b", "medium", "negative-parallelism", "«Это не X, это Y» [D]"),
    (r"\bиграет (важную|ключевую|решающую|значительную|центральную) роль\b", "medium", "puffery", "Шаблон значимости [D]"),
    (r"\b(важно|стоит|следует|необходимо) (отметить|подчеркнуть|учитывать|понимать)\b", "medium", "signposting", "Дидактическая вставка [D]"),
    (r"(^|[.!?]\s+)(в заключение|подводя итог|таким образом|в целом|итак|резюмируя),", "medium", "wrap-up", "Итоговая формула [D]"),
    (r"\bв (современном|сегодняшнем) (мире|контексте)\b|\bна сегодняшний день\b", "medium", "puffery", "Пустая рамка [D]"),
    (r"\b(данный|данная|данное|данные) (документ|подход|процесс|решение|отчёт|отчет|раздел|вопрос)\b", "medium", "officialese", "Канцелярит: «данный» → «этот» [D]"),
    (r"\b(является|являются|являлся|являлась)\b", "low", "copula-avoidance", "«является» вместо тире или «это» [D]"),
    (r"\b(осуществля\w*|в рамках|в целях|с целью обеспечения|на постоянной основе)\b", "low", "officialese", "Канцелярит [D]"),
    (r"\b(обеспечива\w+|позволяет|позволит)\b", "low", "participle-tail", "Комментарий о пользе вместо факта; проверить кластер [D]"),
    (r",\s+(что позволяет|обеспечивая|подчёркивая|подчеркивая|демонстрируя|способствуя|позволяя)\b", "medium", "participle-tail", "Хвост-комментарий [D]"),
    (r"\b(давайте (рассмотрим|разберём|разберем|посмотрим)|ниже (представлен|приведен|приведён))\w*\b", "medium", "signposting", "Экскурсоводская рамка [D]"),
    (r"\b(надеюсь, это (поможет|было полезно)|если (нужно|хотите|потребуется),? (могу|я могу))\b", "high", "chatbot-leakage", "Реплика ассистента [D]"),
    (r"\b(может|могут|могло) (потенциально|возможно)\b", "medium", "hedge-stacking", "Двойная оговорка [D]"),
    (r"\b(ключев\w+|комплексн\w+|уникальн\w+|широк\w+ спектр\w*|максимально)\b", "low", "vocabulary", "Частое AI-слово; проверить кластер [D]"),
]

UK_PATTERNS = [
    (r"\bне (просто|лише|тільки) [^.;!?\n]{1,80}?,?\s*(а|але й|а й)\b", "medium", "negative-parallelism", "«Не просто X, а Y» [D]"),
    (r"\bце не [^.;!?\n]{1,50}?[,—–-]\s*це\b", "medium", "negative-parallelism", "«Це не X, це Y» [D]"),
    (r"\bвідіграє (важливу|ключову|вирішальну|значну|центральну) роль\b", "medium", "puffery", "Шаблон значущості [D]"),
    (r"\b(важливо|варто|слід|необхідно) (зазначити|відзначити|підкреслити|враховувати|розуміти)\b", "medium", "signposting", "Дидактична вставка [D]"),
    (r"(^|[.!?]\s+)(на завершення|підсумовуючи|отже|загалом|таким чином),", "medium", "wrap-up", "Підсумкова формула [D]"),
    (r"\bу (сучасному|сьогоднішньому) (світі|контексті)\b|\bна сьогоднішній день\b", "medium", "puffery", "Порожня рамка [D]"),
    (r"\b(даний|дана|дане|дані) (документ|підхід|процес|рішення|звіт|розділ|питання)\b", "medium", "officialese", "Канцелярит: «даний» → «цей» [D]"),
    (r"\b(здійсню\w*|у рамках|в рамках|з метою забезпечення|на постійній основі)\b", "low", "officialese", "Канцелярит [D]"),
    (r",\s+(що дозволяє|забезпечуючи|підкреслюючи|демонструючи|сприяючи|дозволяючи)\b", "medium", "participle-tail", "Хвіст-коментар [D]"),
    (r"\b(давайте (розглянемо|розберемо|подивимось)|нижче (наведено|представлено))\b", "medium", "signposting", "Екскурсоводська рамка [D]"),
    (r"\b(сподіваюся, це (допоможе|було корисно)|якщо (потрібно|хочете),? (можу|я можу))\b", "high", "chatbot-leakage", "Репліка асистента [D]"),
    (r"\b(ключов\w+|комплексн\w+|унікальн\w+|широк\w+ спектр\w*|максимально)\b", "low", "vocabulary", "Часте AI-слово; перевірити кластер [D]"),
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
                        "High-frequency AI word; rewrite the sentence, do not swap in a synonym [WP]"))
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
                        f"Common words that read as AI in clusters ({per_k:.0f} per 1000 words; medium at 20+ per 1000, 6+ distinct, or 3+ from the 2026 list) [WP][D]"))


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
                        "Sentence lengths are too even. Combine related short sentences, let one run long where the logic needs it [WP][D]"))
    short_share = sum(1 for x in lengths if x <= 10) / len(lengths)
    summary["share_sentences_10_words_or_less"] = round(short_share, 2)
    if mean < 11 or short_share >= 0.6:
        hits.append(Hit("medium", "staccato", 0, f"mean {mean:.1f} words, {short_share:.0%} of sentences are 10 words or fewer",
                        "Chain of short declaratives; join the ones that belong to one thought [WP][D]"))
    starts = [re.match(r"[\"'“(]*([A-Za-zА-Яа-яЁёІіЇїЄєҐґ]+)", s) for s in sentences]
    demo = sum(1 for m in starts if m and m.group(1).lower() in ("this", "these", "it", "that", "это", "этот", "эта", "це", "цей", "ця"))
    if demo / len(sentences) >= 0.3:
        hits.append(Hit("low", "demonstrative-chain", 0, f"{demo}/{len(sentences)} sentences start with This/It/That",
                        "Each sentence leans on the previous one; merge or name the subject [D]"))
    if band >= 0.8 and lang == "en":
        hits.append(Hit("medium", "uniform-rhythm", 0, f"{band:.0%} of sentences are 8-20 words",
                        "Matches the 2026 'strict 8-20 word' AI pattern [WP]"))
    # Paragraphs that all have the same number of sentences.
    counts = [len(split_sentences(p)) for p in paragraphs if word_count(p) >= 25]
    if len(counts) >= 4 and max(counts) - min(counts) <= 1:
        hits.append(Hit("low", "uniform-paragraphs", 0, f"sentences per paragraph: {counts}",
                        "Paragraphs have the same shape [M]"))
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
                            "Readers treat em dashes as an AI signature; use comma, colon, parentheses or a period unless the author uses them [WP][M]"))
        if spaced_en:
            hits.append(Hit("low", "em-dash", spaced_en[0][0], f"{len(spaced_en)} spaced en dash(es) used as em dash",
                            "Same tell with a different character [D]"))
        # Punctuation monotony: no ; ( : in a longer prose text.
        prose_text = " ".join(s for _n, _r, s, k in lines if k == "prose")
        if word_count(prose_text) >= 250 and not re.search(r"[;()]", prose_text) and not em:
            hits.append(Hit("low", "punctuation-monotony", 0, "only commas and periods in 250+ words of prose",
                            "Newer models avoid all other punctuation; parentheses or a semicolon are normal [WP]"))

    # Bold lead-in bullets ("- **Performance:** ...").
    blb = [n for n, raw, _s, k in lines if k == "bullet" and BOLD_LEAD_BULLET_RE.match(raw)]
    if len(blb) >= 2:
        hits.append(Hit("medium" if len(blb) >= 3 else "low", "inline-header-list", blb[0], f"{len(blb)} bullets start with a bold label",
                        "Inline-header vertical list [WP]"))
    bold_prose = sum(len(BOLD_RE.findall(raw)) for n, raw, _s, k in lines if k == "prose")
    if bold_prose >= 3:
        hits.append(Hit("medium", "bold-overuse", 0, f"{bold_prose} bold spans in prose", "Boldface in running text [WP]"))

    # Emoji.
    em_lines = [n for n, raw, _s, k in lines if k != "code" and EMOJI_RE.search(raw)]
    if em_lines:
        hits.append(Hit("medium", "emoji", em_lines[0], f"emoji on {len(em_lines)} line(s)", "Emoji in a work document [WP]"))

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
                        "Use sentence case unless the house style says otherwise [WP]"))
    if heads and total_words < 400 and len(heads) >= 3:
        hits.append(Hit("medium", "formatting-overuse", heads[0][0], f"{len(heads)} headings in {total_words} words",
                        "Short text chopped into sections [M]"))
    if lang == "en":
        h1 = [n for n, raw, _s, k in lines if k == "heading" and raw.strip().startswith("# ")]
        if len(h1) > 1:
            hits.append(Hit("low", "formatting-overuse", h1[1], f"{len(h1)} level-1 headings", "Wrong heading levels [WP]"))

    # Curly quotes (Word autocorrect also produces these, so low).
    if lang == "en" and re.search(r"[“”‘’]", text):
        hits.append(Hit("low", "curly-quotes", 0, "curly quotes present",
                        "Mixed with straight quotes in a chat/markdown doc this is a tell; harmless in Word documents [WP]"))

    # Horizontal rules as section dividers in short docs.
    hr = [n for n, raw, _s, k in lines if k != "code" and re.match(r"^\s*(---|\*\*\*|___)\s*$", raw)]
    if len(hr) >= 2 and total_words < 800:
        hits.append(Hit("low", "formatting-overuse", hr[0], f"{len(hr)} horizontal rules", "Decorative dividers [WP]"))


def scan_triplets(sentences, hits, summary):
    if len(sentences) < 6:
        return
    with_triplet = [s for s in sentences if TRIPLET_RE.search(s)]
    share = len(with_triplet) / len(sentences)
    summary["share_sentences_with_3_item_list"] = round(share, 2)
    if share >= 0.25 and len(with_triplet) >= 3:
        ex = TRIPLET_RE.search(with_triplet[0]).group(0)
        hits.append(Hit("medium", "rule-of-three", 0, f"{len(with_triplet)}/{len(sentences)} sentences contain an 'X, Y, and Z' list, e.g. \"{ex}\"",
                        "Lists of three used as rhythm, not content [WP]"))


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
                            "Mechanically repeated sentence shape [M]"))


# --------------------------------------------------------------------------------------
# Token preservation check
# Compares concrete tokens (numbers, dates, identifiers, code spans, URLs) between the
# source and the draft. It sees presence only: it does not understand meaning, cannot tell
# that a claim was reversed, and does not count repeats.
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
    return re.sub(r"[\s,  ]", "", s).rstrip(".:").lower()


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
    neg = (len(NEGATION_RE.findall(src)), len(NEGATION_RE.findall(out)))
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

# Categories that describe the shape of the whole text. Two or more of them is what makes
# patching weak; vocabulary and single phrases can be patched in place.
STRUCTURAL = {"inline-header-list", "formatting-overuse", "purpose-statement", "wrap-up",
              "uniform-rhythm", "staccato", "rule-of-three", "bold-overuse", "uniform-paragraphs"}


def mask_allowed(text: str, phrases):
    """Replace allowed phrases with neutral words so they are not flagged but word counts hold."""
    for ph in phrases:
        ph = ph.strip()
        if not ph:
            continue
        rx = re.compile(r"(?<![\w])" + re.escape(ph) + r"(?![\w])", re.I)
        text = rx.sub(lambda m: " ".join("ok" for _ in m.group(0).split()), text)
    return text


def run(text: str, lang: str, source, allow=(), allow_categories=()):
    original = text
    text = mask_allowed(text, list(DEFAULT_ALLOW) + list(allow))
    lines = prepare_lines(text)
    if lang == "auto":
        lang = detect_lang(text)
    total_words = word_count(" ".join(s for _n, _r, s, k in lines if k not in ("code",)))
    hits: list[Hit] = []
    summary = {"language": lang, "words": total_words}

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
        summary["suggestion"] = f"rebuild-candidate ({why}); confirm against role, genre and structure before rebuilding"
    elif weight:
        summary["suggestion"] = "patch the flagged spots"
    elif hits:
        summary["suggestion"] = "only low hits; look at them, no rewrite needed on their account"
    else:
        summary["suggestion"] = "no pattern hits; do the manual read"
    return hits, summary, diff


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="draft file, or - for stdin")
    ap.add_argument("--source", help="original text; list tokens (numbers, dates, identifiers, code, URLs) lost or added in the draft")
    ap.add_argument("--lang", default="auto", choices=["auto", "en", "ru", "uk"])
    ap.add_argument("--allow", action="append", default=[], metavar="PHRASE",
                    help="phrase accepted in this text (term of art, quotation, required wording); repeatable")
    ap.add_argument("--allow-category", action="append", default=[], metavar="CATEGORY",
                    help="drop a whole category for this text, e.g. em-dash when the author uses them; repeatable")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["high", "medium"], help="exit 1 if hits at this severity or above remain, or tokens are missing")
    args = ap.parse_args()

    text = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
    source = open(args.source, encoding="utf-8").read() if args.source else None
    hits, summary, diff = run(text, args.lang, source, args.allow, args.allow_category)
    missing, added, neg = diff if diff else (None, None, None)

    if args.json:
        out = {"summary": summary, "hits": [asdict(h) for h in hits]}
        if diff:
            out["tokens_missing"] = [{"kind": k, "value": v} for k, v in missing]
            out["tokens_added"] = [{"kind": k, "value": v} for k, v in added]
            out["negations"] = {"source": neg[0], "draft": neg[1]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        c = summary["counts"]
        print(f"language={summary['language']} words={summary['words']} high={c['high']} medium={c['medium']} low={c['low']}")
        print(f"suggestion: {summary['suggestion']}")
        extra = {k: v for k, v in summary.items() if k not in ("language", "words", "counts", "suggestion")}
        if extra:
            print("stats: " + ", ".join(f"{k}={v}" for k, v in extra.items()))
        for h in hits:
            loc = f"L{h.line}" if h.line else "doc"
            print(f"[{h.severity.upper():6}] {h.category:24} {loc:6} {h.excerpt}\n         -> {h.note}")
        if not hits:
            print("no pattern hits (this does not prove the text reads well; do the manual read)")
        if diff:
            print("\nTOKEN CHECK (presence only; it does not detect reversed claims or changed meaning)")
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

    if args.fail_on:
        threshold = SEVERITY_ORDER[args.fail_on]
        if any(SEVERITY_ORDER[h.severity] >= threshold for h in hits) or missing:
            sys.exit(1)


if __name__ == "__main__":
    main()
