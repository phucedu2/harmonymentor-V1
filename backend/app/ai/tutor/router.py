"""Bộ định tuyến 4 luồng của AI Tutor (ADR-017, góp ý thầy G1/G3, 06/11/2026).

  A "trong bài học"     câu nhạc lý mà kho có đoạn đủ điểm → RAG (+ Gemini nếu có) + trích dẫn + guardrail.
  B "ngoài bài học"     câu nhạc lý bài chưa dạy → Music Engine tính được thì trả lời bằng dữ kiện Engine, nhãn
                        "Ngoài bài học, theo Music Engine"; không tính được thì "không biết" + gợi ý bài. KHÔNG gọi LLM.
  C "không liên quan"   từ chối lịch sự. KHÔNG gọi LLM.
  D "hướng dẫn sử dụng" tra kho hướng dẫn (app/content/help), trả lời bằng mục hướng dẫn, trích trang.
  G "chào hỏi"          trả lời ngắn.

Hai tầng:
  Tầng 1 (route_classifier): đoán loại câu theo câu chữ, cục bộ, miễn phí.
  Tầng 2: điểm truy xuất trên kho bài (và kho hướng dẫn) + Music Engine. Ngưỡng đọc từ router_thresholds.json,
          do scripts/ai/gop_y/hieu_chinh_nguong.py chọn trên tập dev, không chọn tay.
Vùng xám (điểm giữa ngưỡng xám và ngưỡng nhận): luật bảo thủ, nghiêng về "không biết" (quyết định GĐ1).

Thêm một luật tất định "phủ kiến thức": câu hỏi về loại hợp âm / âm giai mà KHÔNG bài nào trong kho nhắc tới
(ví dụ sus4, thứ hòa âm) thì là luồng B dù điểm truy xuất cao, vì đoạn tìm được chỉ "giống chữ", không dạy điều đó.
Ví dụ GĐ0: "Csus4 gồm nốt gì" lấy về đoạn hợp âm ba L01-B08 với điểm cao.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from ...music_engine.chord import parse_chord_symbol
from ..embedder import Embedder
from .engine_query import EngineAnswer, engine_answer
from .retriever import Hit, Retrieval, help_base, knowledge_base, retrieve
from .route_classifier import RouteLabel, classify_route

THRESHOLDS_PATH = Path(__file__).with_name("router_thresholds.json")
_SCALE_WORDS = {"major": ("trưởng", "major"), "natural_minor": ("thứ tự nhiên", "natural minor", "giọng thứ"),
                "harmonic_minor": ("thứ hòa âm", "harmonic minor"), "melodic_minor": ("thứ giai điệu", "melodic minor"),
                "dorian": ("dorian",)}
# Kho thường gọi loại hợp âm bằng chữ ("hợp âm thứ", "nửa giảm") chứ không chỉ bằng ký hiệu.
_CHORD_WORDS = {"maj": ("hợp âm trưởng", "triad trưởng", "major"), "min": ("hợp âm thứ", "triad thứ", "minor"),
                "dim": ("hợp âm giảm", "triad giảm", "diminished", "dim"), "aug": ("hợp âm tăng", "triad tăng", "augmented", "aug"),
                "m7b5": ("nửa giảm", "half-diminished", "ø7", "m7b5"), "dim7": ("dim7", "bảy giảm", "°7"),
                "7": ("bảy át", "dominant seventh"), "maj7": ("maj7",), "m7": ("m7",)}
# Khái niệm của bài chưa có trong kho (quyết định 8A: trả lời "bạn sẽ học sau ở bài …"). Luật tự tắt khi bài vào kho,
# nên không phải sửa tay lúc mở L05–L08. Từ khóa lấy từ tiêu đề và mục tiêu bài trong curriculum_specs.
_LATER_CONCEPTS = {
    # So trên chữ thường (later_lesson hạ chữ), nên mẫu số La Mã viết thường: "V7/V" → "v7/v".
    "L05": r"secondary dominant|át phụ|\bv7?/[iv]+\b",
    "L06": r"modal interchange|mượn (?:hợp âm|từ|nốt)|hợp âm mượn|borrowed chord|giọng song song|\bb(?:vii|vi|iii)\b",
    # Hợp âm 9/11/13 bằng chữ hoặc ký hiệu gõ thường ("fmaj9", "hop am 9 khac hop am 7"): L07 dạy tension.
    "L07": r"\btensions?\b|#(?:9|11)\b|(?<![a-z])b(?:9|13)\b|maj9|chord[- ]scale|điệu thức|\bmodes?\b|lydian|mixolydian|phrygian|locrian|aeolian|ionian"
           r"|\b[a-g][#b]?(?:maj|m|add)?(?:9|11|13)\b|hợp âm (?:9|11|13)\b",
    "L08": r"voicing|thế bấm",
}
# Khái niệm KHÔNG bài nào trong lộ trình hiện tại dạy (chưa có bài để chỉ "bạn sẽ học sau ở bài …"): câu hỏi nhắc tới
# thì là luồng B ("chưa dạy"), dù truy xuất vớt được đoạn bài chỉ "giống chữ". Luật tự tắt nếu kho bài có đoạn nhắc
# tới khái niệm (`marker`, so không dấu), nên khi bài mới vào kho không phải sửa tay. Thêm 09/11/2026 sau khi đo
# phiếu: "quãng 9 là gì", "đảo hợp âm C lần 1", "vòng quãng 5" bị trả lời như bài đã dạy (lỗi nặng nhất).
_UNTAUGHT = {
    "inversion": dict(pattern=r"\bdao hop am\b|\bthe dao\b|\bhop am dao\b|\binversions?\b|\bslash chord", marker=r"\bthe dao\b|\bdao hop am\b"),
    "compound_interval": dict(pattern=r"\bquang (?:kep|9|1[0-5])\b|\bcompound interval|\b(?:9|10|11|13)th\b", marker=r"\bquang kep\b|\bquang 9\b|\bcompound\b"),
    # Thêm 09/11 sau khi kiểm kho: L01–L05 không có "gam thứ tự nhiên/hòa âm/giai điệu", "relative minor", hợp âm 6, bảy giảm.
    "minor_scales": dict(pattern=r"\bgam thu (?:tu nhien|hoa am|giai dieu)\b|\b(?:am giai|gam) thu (?:tu nhien|hoa am|giai dieu)\b|\b(?:natural|harmonic|melodic) minor\b|\bthu (?:hoa am|giai dieu)\b",
                         marker=r"\bgam thu\b|\b(?:natural|harmonic|melodic) minor\b|\bthu hoa am\b"),
    "relative_minor": dict(pattern=r"\brelative (?:minor|major)\b|\bgiong thu (?:tuong ung|song hanh|ke can)\b|\bla thu\b.*\bdo truong\b|\bdo truong\b.*\bla thu\b",
                           marker=r"\brelative\b|\bgiong thu tuong ung\b"),
    "sixth_chord": dict(pattern=r"\bhop am 6\b|\bhop am sau\b|\b[a-g][#b]?6\b(?!\d)", marker=r"\bhop am 6\b|\b[a-g][#b]?6\b"),
    "dim7_chord": dict(pattern=r"\bhop am bay (?:giam|gim)\b|\bdim7\b|\b[a-g][#b]?dim7\b", marker=r"\bbay giam\b|\bdim7\b"),
    "circle_of_fifths": dict(pattern=r"\bvong (?:tron )?quang (?:5|nam)\b|\bcircle of fifths\b", marker=r"\bvong (?:tron )?quang\b|\bcircle of fifths\b"),
    # Thêm 09/11 từ tập dev router_dev/gd2 (không từ tập test): kho L01–L05 không có các mẫu dưới.
    "time_signature": dict(pattern=r"\bnhip \d+ ?/ ?\d+\b|\bso chi nhip\b|\btime signatures?\b", marker=r"\bnhip \d+ ?/ ?\d+\b|\bso chi nhip\b"),
    "note_value": dict(pattern=r"\bnot moc\b|\bmoc (?:don|kep)\b|\bnot (?:den|trang|tron)\b|\bcham doi\b",
                       marker=r"\bnot moc\b|\bmoc (?:don|kep)\b|\bnot (?:den|trang|tron)\b"),
    "clef": dict(pattern=r"\bkhoa (?:fa|sol|son|do)\b|\bclefs?\b", marker=r"\bkhoa (?:fa|sol|son)\b|\bclef\b"),
    "bass_note": dict(pattern=r"\bnot bass\b", marker=r"\bnot bass\b"),
    # L05 nói "voice leading" nhưng không dạy luật cấm quãng 5/8 song song.
    "parallel_fifths": dict(pattern=r"\bquang (?:nam|5|tam|8) song song\b|\bparallel (?:fifths|octaves)\b|\bhoa am bon be\b",
                            marker=r"\bquang (?:nam|5|tam|8) song song\b|\bparallel (?:fifths|octaves)\b"),
    "sus_chord": dict(pattern=r"\bhop am sus\d?\b|\bsus[24]?\b|\bsuspended\b|\bhop am treo\b", marker=r"\bsus[24]?\b|\bsuspended\b"),
}
_SYM_IN_KB = re.compile(r"(?<![A-Za-z0-9#])([A-G](?:#|b)?(?:maj7|M7|m7b5|ø7|dim7|°7|dim|°|aug|\+|m7|m|7|sus2|sus4|6|9)?)"
                        r"(?![A-Za-z0-9#])")


@dataclass
class Decision:
    flow: str                      # A | B | C | D | G
    kind: str                      # lesson | engine | unknown | refuse | help | help_unknown | greeting
    label: RouteLabel
    lesson: Retrieval
    help: Retrieval | None
    engine: EngineAnswer
    reason: str
    hits: list[Hit] = field(default_factory=list)          # đoạn bài được dùng (chỉ luồng A)
    help_hits: list[Hit] = field(default_factory=list)     # mục hướng dẫn được dùng (chỉ luồng D)
    nearest_lesson: str | None = None                      # bài gần nhất để gợi ý khi "không biết"
    later_lesson: str | None = None                        # bài chưa mở dạy khái niệm này (luồng B)

    def log(self) -> dict[str, Any]:
        return {"flow": self.flow, "kind": self.kind, "reason": self.reason,
                "label": {"label": self.label.label, "confidence": self.label.confidence},
                "lesson_best": self.lesson.best_score, "method": self.lesson.method,
                "help_best": self.help.best_score if self.help else None,
                "engine_unknown": self.engine.unknown, "nearest_lesson": self.nearest_lesson,
                "later_lesson": self.later_lesson}


@lru_cache(maxsize=1)
def thresholds() -> dict[str, dict[str, float]]:
    return json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))["thresholds"]


def method_key(embedder: Embedder | None) -> str:
    return f"embedding:{embedder.model}" if embedder is not None else "bm25"


def _th(embedder: Embedder | None) -> dict[str, float]:
    table = thresholds()
    return table.get(method_key(embedder)) or table["bm25"]


@lru_cache(maxsize=1)
def kb_coverage() -> tuple[frozenset[str], frozenset[str]]:
    """(loại hợp âm, loại âm giai) mà ít nhất một đoạn bài nhắc tới. Tính từ chính kho, không ghi tay."""
    chords, scales = set(), set()
    for c in knowledge_base():
        text = f"{c.title} {c.text}"
        for m in _SYM_IN_KB.finditer(text):
            try:
                chords.add(parse_chord_symbol(m[1]).type.id)
            except Exception:
                continue
        low = text.lower()
        for kind, words in _CHORD_WORDS.items():
            if any(w.lower() in low for w in words):
                chords.add(kind)
        for kind, words in _SCALE_WORDS.items():
            if any(w in low for w in words):
                scales.add(kind)
    return frozenset(chords), frozenset(scales)


def _words(text: str) -> list[str]:
    """Chữ thường, bỏ dấu (để câu gõ không dấu vẫn so được), tách theo chữ và số."""
    t = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    return re.findall(r"[a-z0-9#]+", "".join(ch for ch in t if unicodedata.category(ch) != "Mn"))


@lru_cache(maxsize=1)
def known_words() -> frozenset[str]:
    """Từ "đã biết": có trong kho bài, kho hướng dẫn, hoặc câu train KHÔNG phải nhạc lý (từ hỏi thường ngày).
    Lấy từ dữ liệu, không lập danh sách tay. Câu train nhạc lý không được tính vì chứa thuật ngữ kho chưa dạy."""
    from .route_classifier import load_data

    words: set[str] = set()
    for c in [*knowledge_base(), *help_base()]:
        words.update(_words(f"{c.title} {c.text}"))
    data = load_data()
    for label, rows in data["train"].items():
        if label != "nhac_ly":
            for r in rows:
                words.update(_words(r))
    # Câu train GĐ2 luồng A (kho CÓ dạy): từ trong đó là từ "đã biết", kể cả cách gõ tắt của người học ("ko", "fai",
    # "vs"). Câu B không được tính vì chứa đúng thuật ngữ kho chưa dạy.
    for r in data.get("a_rows", []):
        words.update(_words(r))
    return frozenset(words)


@lru_cache(maxsize=1)
def _kb_words() -> frozenset[str]:
    return frozenset(w for c in knowledge_base() for w in _words(f"{c.title} {c.text}"))


def _all_terms_in_kb(question: str) -> bool:
    """Mọi chữ của câu đều "đã biết" (kho bài, kho hướng dẫn, câu thường ngày; cho phép lỗi gõ) và có chữ của kho bài."""
    import difflib

    words = _words(question)
    in_kb = [w for w in words if w in _kb_words()
             or (len(w) >= 4 and difflib.get_close_matches(w, _kb_words(), n=1, cutoff=0.8))]
    # Thuật ngữ = chữ của kho không phải âm tiết tiếng Việt ("triad", "tonic", "perfetc") hoặc con số ("quang 8").
    # Âm tiết tiếng Việt bỏ dấu dễ trùng ("hoa tri" ~ "hòa", "trí") nên không tính là thuật ngữ.
    terms = [w for w in in_kb if w.isdigit() or _foreign(w, w)]
    return bool(terms) and all(w.isdigit() or w in known_words() or w in in_kb for w in words)


_INTERVAL_TOKEN = re.compile(r"[pmad]\d{1,2}")   # m3, P5, d5, A4: ký hiệu quãng L01 đã dạy


@lru_cache(maxsize=4096)
def _near_known(word: str) -> bool:
    """Lỗi gõ của một từ đã biết ("enharmonci", "cug"): không coi là thuật ngữ lạ. Chỉ xét từ ≥ 3 chữ để từ ngắn
    lạ thật ("fa") không bị nuốt."""
    import difflib

    return len(word) >= 3 and bool(difflib.get_close_matches(word, known_words(), n=1, cutoff=0.8))


_VI_SYLLABLE = re.compile(r"(ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnprstvx])?[aeiouy]{1,3}(ch|ng|nh|[cmnptiyou])?")


def _foreign(word: str, original: str) -> bool:
    """Từ không thể là một âm tiết tiếng Việt: "pentatonic", "fugue", "blues", "fa". Từ tiếng Việt lạ ("cuối",
    "buồn") KHÔNG tính, vì danh sách từ thường ngày lấy từ dữ liệu train còn nhỏ, tính vào thì chặn nhầm câu A."""
    return not any(ord(ch) > 127 for ch in original) and not _VI_SYLLABLE.fullmatch(word)


def unknown_terms(question: str) -> list[str]:
    """Thuật ngữ ngoại trong câu hỏi mà kho bài, kho hướng dẫn và câu thường ngày đều không có, ví dụ "pentatonic",
    "fugue". Ký hiệu hợp âm bỏ qua vì đã có luật phủ kiến thức theo Engine. Có thuật ngữ lạ = kho chưa dạy chủ đề đó."""
    out = []
    originals = re.findall(r"[^\W_]+|#", unicodedata.normalize("NFC", question.lower()))
    for raw in originals:
        for w in _words(raw):
            if (w in known_words() or len(w) < 2 or w.isdigit() or re.fullmatch(r"l\d\d", w)
                    or _INTERVAL_TOKEN.fullmatch(w)):
                continue
            if not _foreign(w, raw) or _near_known(w):
                continue
            if not any(_parses(sym) for sym in (w[0].upper() + w[1:], "C" + w)):   # "Bm7b5", hoặc hậu tố "m7b5"
                out.append(w)
    return out


def _parses(symbol: str) -> bool:
    try:
        parse_chord_symbol(symbol)
        return True
    except Exception:
        return False


def _fold(text: str) -> str:
    """Chữ thường, bỏ dấu tiếng Việt (đ → d): người học hay gõ không dấu ("muon hop am" thay "mượn hợp âm")."""
    t = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    return "".join(ch for ch in t if unicodedata.category(ch) != "Mn")


def later_lesson(question: str) -> str | None:
    """Bài CHƯA có trong kho mà dạy khái niệm câu hỏi nhắc tới; None nếu không có."""
    in_kb = {c.lesson_id for c in knowledge_base()}
    low, folded = question.lower(), _fold(question)
    for lesson_id, pattern in _LATER_CONCEPTS.items():
        # Khớp cả bản có dấu (mẫu viết có dấu) lẫn bản bỏ dấu (câu gõ không dấu); mẫu bỏ dấu cũng bỏ dấu cho mẫu.
        if lesson_id not in in_kb and (re.search(pattern, low) or re.search(_fold(pattern), folded)):
            return lesson_id
    return None


def untaught_concept(question: str) -> str | None:
    """Khái niệm chưa bài nào dạy (và kho bài không nhắc tới) mà câu hỏi nhắc tới; None nếu không có."""
    folded = _fold(question)
    kb_text = " ".join(_fold(c.text) for c in knowledge_base())
    for name, rule in _UNTAUGHT.items():
        if re.search(rule["pattern"], folded) and not re.search(rule["marker"], kb_text):
            return name
    return None


def _scale_typo(unknown: str) -> bool:
    """"âm giai trởưng", "âm giai tưởng": gõ sai chữ "trưởng/thứ", không phải loại âm giai lạ (tập dev gd2)."""
    import difflib

    if not unknown.startswith("âm giai "):
        return False
    kind = " ".join(_words(unknown[len("âm giai "):]))
    return bool(difflib.get_close_matches(kind, ["truong", "thu"], n=1, cutoff=0.6))


def outside_kb(eng: EngineAnswer) -> bool:
    """Câu hỏi về thứ kho chưa dạy: loại hợp âm/âm giai không đoạn nào nhắc, hoặc ký hiệu Engine không hiểu."""
    if any(not _scale_typo(u) for u in eng.unknown):
        return True
    chords, scales = kb_coverage()
    for f in eng.facts:
        if f["tool"] == "get_chord_tones":
            try:
                if parse_chord_symbol(f["args"]["symbol"]).type.id not in chords:
                    return True
            except Exception:
                return True
        if f["tool"] == "get_scale" and f["args"]["scale_type"] not in scales:
            return True
    return False


@dataclass
class Signals:
    """Mọi tín hiệu của một câu hỏi, tính một lần. route() chỉ so với ngưỡng nên dò lưới ngưỡng chạy nhanh."""
    question: str
    label: RouteLabel
    engine: EngineAnswer
    lesson: Retrieval
    help: Retrieval
    later_lesson: str | None
    outside_kb: bool
    unknown_terms: list[str]
    untaught: str | None = None


def gather(question: str, embedder: Embedder | None, *, top_k: int = 4) -> Signals:
    eng = engine_answer(question)
    return Signals(question, classify_route(question), eng,
                   retrieve(question, embedder, top_k=top_k, min_score=-1.0, bm25_min_score=-1.0),
                   retrieve(question, embedder, top_k=2, min_score=-1.0, bm25_min_score=-1.0, chunks=list(help_base())),
                   later_lesson(question), outside_kb(eng), unknown_terms(question), untaught_concept(question))


def route(sig: Signals, th: dict[str, float]) -> Decision:
    label, eng, lesson, question = sig.label, sig.engine, sig.lesson, sig.question
    nearest = lesson.hits[0].chunk.lesson_id if lesson.hits else None
    gray, accept = th["lesson_gray"], th["lesson_accept"]
    keep = [h for h in lesson.hits if h.score >= gray]

    def d(flow, kind, reason, **kw):
        near = kw.get("later_lesson") or nearest
        return Decision(flow, kind, label, lesson, kw.pop("help", None), eng, reason, nearest_lesson=near, **kw)

    probs = label.probs
    music_like = label.label == "nhac_ly" or probs.get("nhac_ly", 0) >= th["music_min"] or eng.facts or eng.unknown
    if label.label == "chao_hoi" and label.confidence >= th["greet_conf"] and len(question.split()) <= 8:
        return d("G", "greeting", "label_greeting")

    if label.label == "huong_dan" and label.confidence >= th["help_conf"]:
        hits = [h for h in sig.help.hits if h.score >= th["help_accept"]]
        # Câu nhạc lý hỏi kiểu "… làm thế nào" hay bị tầng 1 đoán là hướng dẫn. Kho bài trả lời được (điểm đạt ngưỡng
        # nhận) và xác suất nhạc lý không thấp thì ưu tiên bài học.
        # Với nhúng, điểm hai kho cùng thang (cosine) nên so trực tiếp: đoạn bài hơn mục hướng dẫn một khoảng thì là bài.
        same_scale = lesson.method == "embedding" and sig.help.method == "embedding"
        lesson_wins = ((lesson.best_score >= accept and probs.get("nhac_ly", 0) >= th["music_min"]) or
                       (same_scale and lesson.best_score >= sig.help.best_score + th.get("help_margin", 1.0)))
        if hits and not lesson_wins:
            return d("D", "help", "label_help+help_hit", help=sig.help, help_hits=hits[:1])
        # Tầng 1 hay nhầm câu nhạc lý kiểu "… đếm thế nào" thành hướng dẫn; kho hướng dẫn không có mục nào thì
        # xét tiếp như câu nhạc lý thay vì trả "chưa có hướng dẫn".
        if not hits and not (music_like and probs.get("nhac_ly", 0) >= th["music_min"]):
            return d("D", "help_unknown", "label_help_no_hit", help=sig.help)

    if label.label == "ngoai_pham_vi" and label.confidence >= th["oos_conf"] and not eng.facts:
        return d("C", "refuse", "label_out_of_scope")

    # Từ đây: câu nhạc lý (hoặc tầng 1 không chắc). A hay B do kho + Engine quyết.
    if not music_like:
        return d("C", "refuse", "not_music_low_score")
    if sig.later_lesson:
        kind = "engine" if eng.facts and not eng.unknown else "unknown"
        return d("B", kind, "later_lesson", later_lesson=sig.later_lesson)
    if sig.untaught:
        return d("B", "engine" if eng.facts and not eng.unknown else "unknown", "untaught_concept")
    if sig.outside_kb:
        if eng.facts:
            return d("B", "engine", "outside_kb_engine")
        return d("B", "unknown", "outside_kb_unknown")
    if sig.unknown_terms:
        # Từ lạ trong câu tầng 1 không chắc là nhạc lý (dưới đa số): "cho minh link tai nhac lau free" có "link",
        # "free" nhưng không hỏi nhạc lý. Ngưỡng 0,5 là "đa số", không dò; câu B thật trên tập dev đều ≥ 0,62.
        if not eng.facts and (label.label != "nhac_ly" or probs.get("nhac_ly", 0) < 0.5):
            return d("C", "refuse", "unknown_terms_not_music")
        return d("B", "engine" if eng.facts else "unknown", "unknown_terms")
    # Tầng 1 nghiêng ngoài phạm vi mà nhạc lý không chiếm đa số, không có ký hiệu nào: không trả lời như bài học dù
    # điểm truy xuất cao ("Gợi ý phim hay cuối tuần" 0,49 nhạc lý / 0,36 ngoài phạm vi, BM25 9,9).
    if not eng.facts and probs.get("nhac_ly", 0) < 0.5 and probs.get("ngoai_pham_vi", 0) >= th["music_min"]:
        return d("C", "refuse", "weak_music_oos")
    if lesson.best_score >= accept:
        return d("A", "lesson", "lesson_hit", hits=keep or lesson.hits[:1])
    # Dữ kiện Engine thuộc loại kho đã dạy và có đoạn bài ở vùng xám: trả lời từ bài kèm dữ kiện Engine.
    if eng.facts and keep:
        return d("A", "lesson", "engine_in_kb", hits=keep)
    if eng.facts:
        return d("B", "engine", "below_threshold_engine")
    if lesson.best_score >= gray:
        # Câu định nghĩa ngắn ("triad la gi", "tonic va dominant la gi") có ít chữ nên điểm truy xuất thấp, rơi vào
        # vùng xám. Mọi chữ đều là chữ kho bài hoặc chữ hỏi thường ngày (cho phép lỗi gõ "perfetc") và có ít nhất một
        # chữ của kho bài: kho có dạy, trả lời từ bài. Chỉ với câu ngắn (≤ 8 chữ) mà tầng 1 chắc là nhạc lý (≥ 0,5),
        # vì văn bài có nhiều chữ thường ("giảm", "hóa") nên câu ngoài lề cũng "toàn chữ của kho". Đặt SAU mọi luật
        # "chưa dạy" ở trên nên không mở cửa cho câu B.
        if probs.get("nhac_ly", 0) >= 0.5 and len(_words(question)) <= 8 and _all_terms_in_kb(question):
            return d("A", "lesson", "gray_zone_kb_terms", hits=keep or lesson.hits[:1])
        return d("B", "unknown", "gray_zone_conservative")
    return d("B", "unknown", "no_lesson_hit")


def decide(question: str, embedder: Embedder | None, *, top_k: int = 4) -> Decision:
    return route(gather(question, embedder, top_k=top_k), _th(embedder))
