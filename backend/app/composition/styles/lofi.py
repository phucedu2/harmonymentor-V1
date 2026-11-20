"""Lo-fi (id cũ "lofi"): swing 16 nhẹ, snare "lười" trễ phách, Rhodes/FM piano maj7–m9 ngân dài, vinyl."""
PACK = {
    "label": "Lo-fi", "description": "Nhịp lắc nhẹ, snare trễ, phím điện maj7/9 ngân dài, có tiếng đĩa than.",
    "default_bpm": 80, "bpm_range": [68, 92], "grid": 16, "color": "ninth",
    "feel": {"swing": 0.58, "swing_sub": "16n", "sigma_ms": {"drums": 9, "bass": 11, "keys": 14, "guitar": 16},
             "pocket_ms": {"kick": 8, "snare": 24, "hat": 6, "bass": 10, "keys": 14, "guitar": 10},
             "roll_ms": [10, 30], "strum_ms": [14, 24]},
    "keys": {"instrument": "epiano", "voicing": "rootless", "range": [52, 77], "top": 68, "max_span": 12,
             "patterns": {1: ["r==============="], 2: ["r=========..o===", "r==============="],
                          3: ["r=======..x.o===", "r=====o===..r==="]}},
    "bass": {"instrument": "bass", "range": [28, 48], "approach": ["below", "scale"],
             "patterns": {1: ["R==============="], 2: ["R=========5=..A.", "R===========..A."], 3: ["R=======..R.5=A.", "R=========5=..A."]}},
    "guitar": {"instrument": "guitar", "voicing": "high", "min_energy": 3,
               "patterns": {3: ["........s.......", "......3=2=1....."]}},
    "drums": {
        "patterns": {
            1: [{"kick": "x.........x.....", "xstick": "....o.......o...", "hh_c": "o...o...o...o..."}],
            2: [{"kick": "X.........x.....", "snare": "....x.......x...", "hh_c": "x.o.x.oox.o.x.o."},
                {"kick": "X......x..x.....", "snare": "....x.......x...", "hh_c": "x.o.x.o.x.o.x.oo"}],
            3: [{"kick": "X......x..x...x.", "snare": "....x..g....x...", "hh_c": "x.oox.o.x.oox.o.",
                 "hh_o": "..............o."}],
        },
        "fills": {"small": [{"kick": "X.........x.....", "snare": "....x.......x.g.", "hh_c": "x.o.x.oox.o....."}],
                  "big": [{"kick": "X.........x.....", "snare": "....x...g...x.xx", "hh_c": "x.o.x.o........."}]},
    },
    "fx": {"reverb": 0.2, "room": "plate", "delay": 0.0, "lofi": True, "chorus": False, "drive": False},
}

PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 1), ("verse", 8, "A", 2, "A"), ("chorus", 8, "B", 3, "B"), ("outro", 4, "A", 2)],
        "medium": [("intro", 4, "A", 1), ("verse", 8, "A", 2, "A"), ("chorus", 8, "B", 3, "B"),
                   ("verse", 8, "A", 3, "A (thêm lớp)"), ("chorus", 8, "B", 4, "B"), ("outro", 4, "A", 2)],
        "full": [("intro", 4, "A", 1), ("verse", 8, "A", 2, "A"), ("chorus", 8, "B", 3, "B"),
                 ("verse", 8, "A", 3, "A (thêm lớp)"), ("chorus", 8, "B", 4, "B"), ("breakdown", 4, "A", 1),
                 ("verse", 8, "A", 3, "A"), ("chorus", 8, "B", 4, "B"), ("chorus", 8, "B", 5, "B"), ("outro", 8, "A", 2)],
    },
    "parts": {"breakdown": ["keys", "drums"]},
    "verse_stick": False,
    # Bù độ to Chorus − Verse (dB) đo trên bản thu 02/11/2026, xem song.sec_db.
    "chorus_trim_db": 1.2,
    "ending": "fade",
    "surprises": [("drop_bar", "chorus"), ("stop_time", "chorus"), ("reverse_cymbal", "chorus")],
    "transitions": {},
    "hook": {"instrument": "epiano", "rhythms": ["x=====x=x=======", "....x=x=x=======", "x===x=====x====="]},
}
