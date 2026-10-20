from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NOTATION = ROOT / "frontend" / "src" / "components" / "music" / "NotationStaff.tsx"


def test_notation_staff_uses_vexflow_soft_voice_helper():
    source = NOTATION.read_text(encoding="utf-8")
    assert "Formatter.FormatAndDraw(context, stave, [staveNote])" in source
    assert "new Voice(" not in source
    assert "joinVoices([voice])" not in source


def test_notation_staff_contains_runtime_fallback():
    source = NOTATION.read_text(encoding="utf-8")
    assert "try {" in source
    assert "catch (error)" in source
    assert "notation-fallback" in source
    assert "VexFlow render failed" in source


def test_learn_page_wraps_lesson_in_error_boundary():
    learn = (ROOT / "frontend" / "src" / "pages" / "Learn.tsx").read_text(encoding="utf-8")
    boundary = (ROOT / "frontend" / "src" / "components" / "learning" / "LessonErrorBoundary.tsx").read_text(encoding="utf-8")
    assert "<LessonErrorBoundary" in learn
    assert "getDerivedStateFromError" in boundary
    assert "Quay lại danh sách bài học" in boundary


def test_notation_labels_are_bound_to_each_example_card():
    source = NOTATION.read_text(encoding="utf-8")
    assert "notation-examples" in source
    assert "notation-example-label" in source
    assert "notation-labels" not in source
