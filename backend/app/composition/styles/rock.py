"""Rock (mới): kick 1 & 3, snare 2–4 mạnh, bass móc đơn đều, guitar power chord chặn tiếng/mở tiếng."""
PACK = {
    "label": "Rock", "description": "Trống mạnh, bass móc đơn đều, guitar power chord chặn tiếng, mở tiếng ở cao trào.",
    "default_bpm": 116, "bpm_range": [96, 150], "grid": 16, "color": "none",
    "feel": {"swing": 0.0, "swing_sub": "8n", "sigma_ms": {"drums": 4, "bass": 5, "keys": 8, "guitar": 6},
             "pocket_ms": {"kick": 0, "snare": 0, "hat": 0, "bass": 0, "keys": 2, "guitar": -2},
             "roll_ms": [2, 8], "strum_ms": [5, 8]},
    "keys": {"instrument": "piano", "voicing": "close", "range": [55, 79], "top": 72,
             "patterns": {1: ["o==============="], 2: ["o=======o======="], 3: ["x=======x======="]}},
    "bass": {"instrument": "bass", "range": [28, 47], "approach": ["below", "scale"],
             "patterns": {1: ["R=======R======="], 2: ["R.R.R.R.R.R.R.R.", "R.R.R.R.R.R.R.A."], 3: ["R.R.R.R.R.R.R.A.", "R.RRR.R.R.RRR.A."]}},
    "guitar": {"instrument": "guitar", "voicing": "power", "min_energy": 1,
               "patterns": {1: ["O===============", "O=======O======="], 2: ["P.P.P.P.P.P.P.P.", "P.PPP.P.P.PPP.P."],
                            3: ["O=====O=O=====O.", "O===P.P.O===P.P."]}},
    "drums": {
        "patterns": {
            1: [{"kick": "x.......x.......", "snare": "....x.......x...", "hh_c": "o.o.o.o.o.o.o.o."}],
            2: [{"kick": "X.......X.x.....", "snare": "....X.......X...", "hh_c": "x.x.x.x.x.x.x.x."},
                {"kick": "X.x.....X.x.....", "snare": "....X.......X...", "hh_c": "x.x.x.x.x.x.x.x."}],
            3: [{"kick": "X.x.....X.x.....", "rim": "....X.......X...", "ride": "x.x.x.x.x.x.x.x.", "ride_b": "x...x...x...x..."},
                {"kick": "X.......X.x...x.", "rim": "....X.......X...", "hh_o": "x.x.x.x.x.x.x.x."}],
        },
        "fills": {"small": [{"kick": "X.......X.......", "snare": "....X.......XXXX", "hh_c": "x.x.x.x.x.x....."}],
                  "big": [{"kick": "X.......X.......", "snare": "....X...XXXX....", "tom_h": "............XX..",
                           "tom_m": "..............X.", "tom_f": "...............X"}]},
    },
    "fx": {"reverb": 0.2, "room": "room", "delay": 0.0, "lofi": False, "chorus": False, "drive": True},
}

PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 2), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("outro", 4, "B", 4)],
        "medium": [("intro", 4, "A", 2), ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4),
                   ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("solo", 8, "A", 4),
                   ("breakdown", 4, "A", 2), ("chorus", 8, "B", 5), ("chorus", 8, "B", 5)],
        "full": [("intro", 8, "A", 2), ("verse", 16, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4),
                 ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("solo", 16, "A", 4),
                 ("breakdown", 4, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 5), ("chorus", 8, "B", 5),
                 ("outro", 8, "B", 4)],
    },
    "parts": {"intro": ["guitar", "hook"], "breakdown": ["bass", "drums"]},
    "verse_stick": False,
    "ending": "big_hit",
    "surprises": [("double", "last_chorus"), ("stop_time", "chorus"), ("drop_bar", "chorus"), ("riser", "chorus")],
    "transitions": {},
    "hook": {"instrument": "guitar", "rhythms": ["x.x.x.x.x=======", "x=x=x===x=======", "x...x...x.x.x==="]},
}
