"""Funk (mới): hat 16 có nhấn, snare ghost, kick lệch phách, bass nốt chết + quãng tám, guitar chicken scratch."""
PACK = {
    "label": "Funk", "description": "Hat móc kép có nhấn, snare ghost, bass nốt chết, guitar chicken scratch, clavi.",
    "default_bpm": 104, "bpm_range": [92, 118], "grid": 16, "color": "ninth",
    "feel": {"swing": 0.53, "swing_sub": "16n", "sigma_ms": {"drums": 4, "bass": 5, "keys": 7, "guitar": 6},
             "pocket_ms": {"kick": 0, "snare": 2, "hat": -2, "bass": 0, "keys": 0, "guitar": -2},
             "roll_ms": [2, 6], "strum_ms": [3, 6]},
    "keys": {"instrument": "clav", "voicing": "close", "range": [57, 79], "top": 72,
             "patterns": {1: ["o=======........"], 2: ["..x...x...x..x..", "..t...t.t...t..."], 3: ["..x.t.x...x.tx..", "x.t...x.t.x...t."]}},
    "bass": {"instrument": "bass", "range": [28, 50], "approach": ["below", "above"],
             "patterns": {1: ["R=.....R=......."], 2: ["R..x8.R.x.R.5.A.", "R=.xR.x8..R.x5A."], 3: ["R.xR8.xR.xR.8xA.", "R..x8.R.x.R8x5A."]}},
    "guitar": {"instrument": "guitar", "voicing": "high", "min_energy": 2,
               "patterns": {2: ["M.S.M.SMM.S.M.SM", "MMS.MMS.MMS.MMSM"], 3: ["MMSMMMSMMMSMMMSM", "M.SMM.S.MMSMM.SM"]}},
    "drums": {
        "patterns": {
            1: [{"kick": "X.........x.....", "snare": "....x.......x...", "hh_c": "x.o.x.o.x.o.x.o."}],
            2: [{"kick": "X..x..x...X...x.", "snare": "....X..g.g..X..g", "hh_c": "XoxoXoxoXoxoXoxo"},
                {"kick": "X.x...x...X..x..", "snare": "....X..g.g..X.g.", "hh_c": "XoxoXoxoXoxoXoxo"}],
            3: [{"kick": "X..x..x...X.x.x.", "snare": "....X.gg.g..X..g", "hh_c": "XoxoXoxoXoxoXo..", "hh_o": "..............x."}],
        },
        "fills": {"small": [{"kick": "X..x..x...X.....", "snare": "....X..g.g..XgXg", "hh_c": "XoxoXoxoXoxo...."}],
                  "big": [{"kick": "X..x..x.........", "snare": "....X..g.gxXx...", "tom_h": "............Xx..",
                           "tom_f": "..............XX"}]},
    },
    "fx": {"reverb": 0.1, "room": "room", "delay": 0.0, "lofi": False, "chorus": False, "drive": False},
}

PACK["song"] = {
    "forms": {
        "short": [("intro", 2, "A", 2), ("verse", 8, "A", 3, "Vamp A"), ("chorus", 8, "B", 4, "Vamp B"),
                  ("verse", 8, "A", 4, "Vamp A"), ("outro", 4, "A", 3)],
        "medium": [("intro", 2, "A", 2), ("verse", 8, "A", 3, "Vamp A"), ("chorus", 8, "B", 4, "Vamp B"),
                   ("verse", 8, "A", 3, "Vamp A"), ("chorus", 8, "B", 4, "Vamp B"), ("breakdown", 4, "A", 2),
                   ("verse", 8, "A", 4, "Vamp A (đủ)"), ("chorus", 8, "B", 5, "Vamp B"), ("outro", 4, "A", 3)],
        "full": [("intro", 4, "A", 2), ("verse", 8, "A", 3, "Vamp A"), ("chorus", 8, "B", 4, "Vamp B"),
                 ("verse", 8, "A", 3, "Vamp A"), ("chorus", 8, "B", 4, "Vamp B"), ("solo", 16, "A", 4, "Solo"),
                 ("breakdown", 8, "A", 2), ("verse", 8, "A", 4, "Vamp A (đủ)"), ("chorus", 8, "B", 5, "Vamp B"),
                 ("chorus", 8, "B", 5, "Vamp B"), ("outro", 8, "A", 3)],
    },
    "parts": {"intro": ["drums"], "breakdown": ["bass", "drums"]},
    "verse_stick": False,
    # Bù độ to Chorus − Verse (dB) đo trên bản thu 02/11/2026, xem song.sec_db.
    "chorus_trim_db": 2.4,
    "ending": "big_hit",
    "surprises": [("stop_time", "chorus"), ("drop_bar", "chorus"), ("stop_time", "verse")],
    "transitions": {},
    "hook": {"instrument": "clav", "rhythms": ["..x..x.x........", "x..x..x.x.......", "...x.x...x.x...."]},
}
