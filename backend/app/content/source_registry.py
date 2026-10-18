"""Canonical source registry for curriculum provenance (Phase 0.4B).

The registry intentionally distinguishes *available/verified access* from *permission to reproduce*.
HarmonyMentor paraphrases concepts and writes original exercises; it does not copy proprietary
workbook pages, scores, or answer keys.
"""

SOURCE_REGISTRY = {
    "OMT_V2": {
        "title": "Open Music Theory — Version 2",
        "author": "Open Music Theory contributors",
        "url": "https://viva.pressbooks.pub/openmusictheory/",
        "access": "official_web_verified",
        "license": "CC BY-SA 4.0 except where a chapter/media item states otherwise",
        "role": "Primary source for fundamentals, tonicization, modal mixture, jazz basics, and popular-music concepts.",
    },
    "FANK_WIH": {
        "title": "Working in Harmony",
        "author": "Gabriel Fankhauser",
        "url": "https://faculty.ung.edu/gfankhauser/",
        "access": "official_site_verified; current PDFs are large and exact current PDF page locators are not locked in this phase",
        "license": "Reference use. Do not reproduce current PDF text/notation unless the current PDF license is checked.",
        "role": "Academic cross-check for fundamentals, diatonic harmony, chromatic harmony, and voice leading.",
    },
    "TEREFENKO_WB": {
        "title": "Workbook to Accompany Jazz Theory: From Basic to Advanced Study",
        "author": "Dariusz Terefenko",
        "url": None,
        "access": "user_supplied_pdf_verified",
        "license": "Copyright Routledge/Taylor & Francis; reference only. Do not reproduce exercises, scores, or answer keys.",
        "role": "Primary pedagogical reference for keyboard realization, ear training, ii–V–I, chord-scale work, voicings, and jazz practice sequencing.",
    },
    "KHAIHOAN_JAZZ": {
        "title": "Hòa âm Jazz cơ bản đến nâng cao",
        "author": "Trần Khải Hoàn",
        "url": None,
        "access": "user_supplied_pdf_verified",
        "license": "Reference only unless the rights holder grants broader reuse.",
        "role": "Vietnamese reference for jazz/modern harmonic function, tensions, secondary dominants, modal interchange, and voicing.",
    },
}
