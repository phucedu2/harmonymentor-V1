"""Indie (mới): hat 16 + tambourine, guitar clean chorus rải nốt treo, bass giai điệu, reverb dài."""
PACK = {
    "label": "Indie", "description": "Hat móc kép, tambourine, guitar clean chorus rải nốt treo, reverb rộng.",
    "default_bpm": 112, "bpm_range": [96, 132], "grid": 16, "color": "add9",
    "feel": {"swing": 0.0, "swing_sub": "8n", "sigma_ms": {"drums": 6, "bass": 8, "keys": 10, "guitar": 12},
             "pocket_ms": {"kick": 0, "snare": 4, "hat": 0, "bass": 2, "keys": 4, "guitar": 0},
             "roll_ms": [4, 14], "strum_ms": [6, 11]},
    "keys": {"instrument": "piano", "voicing": "close", "range": [57, 79], "top": 74,
             "patterns": {1: ["o==============="], 2: ["o=======o=======", "o==============="], 3: ["x=======x=======", "x===o===x===o==="]}},
    "bass": {"instrument": "bass", "range": [30, 52], "approach": ["scale", "below"],
             "patterns": {1: ["R==============="], 2: ["R=====5=8=====5=", "R=====R=5=====A="], 3: ["R.R.5.R.8.R.5.A.", "R=====5=8=5=R=A="]}},
    "guitar": {"instrument": "guitar", "voicing": "high", "min_energy": 2,
               "patterns": {2: ["1.2.3.2.1.2.3.2.", "1.3.2.3.1.3.2.3."], 3: ["D.DUDUDUD.DUDUDU", "1.2.3.2.D.DU.UDU"]}},
    "drums": {
        "patterns": {
            1: [{"kick": "x.......x.......", "hh_c": "xoooxoooxoooxooo"}],
            2: [{"kick": "X.......x.......", "snare": "....x.......x...", "hh_c": "xoooxoooxoooxooo"},
                {"kick": "X.......x.x.....", "snare": "....x.......x...", "hh_c": "xoooxoooxoooxooo"}],
            3: [{"kick": "X.......X.......", "snare": "....X.......X...", "tom_f": "x.x.x.x.x.x.x.x."},
                {"kick": "X.......x.x.....", "snare": "....X.......X...", "hh_o": "x.x.x.x.x.x.x.x."}],
        },
        "fills": {"small": [{"kick": "X.......x.......", "snare": "....x.......xxxx", "hh_c": "xoooxoooxooo...."}],
                  "big": [{"kick": "X.......X.......", "snare": "....X...........", "tom_f": "........XxXxXxXx",
                           "tom_h": "........x...x..."}]},
        "perc": {2: [{"tamb": "....x.......x..."}], 3: [{"tamb": "..x...x...x...x."}]},
    },
    "fx": {"reverb": 0.3, "room": "hall", "delay": 0.18, "lofi": False, "chorus": True, "drive": False},
}

PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("outro", 4, "A", 2)],
        "medium": [("intro", 8, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("verse", 8, "A", 2),
                   ("chorus", 8, "B", 4), ("bridge", 8, "C", 3, "Bridge (dồn dài)"), ("chorus", 8, "B", 5),
                   ("outro", 8, "A", 2)],
        "full": [("intro", 8, "A", 1), ("verse", 16, "A", 2), ("chorus", 8, "B", 4), ("post", 4, "B", 3),
                 ("verse", 16, "A", 2), ("chorus", 8, "B", 4), ("post", 4, "B", 3), ("bridge", 8, "C", 3, "Bridge (dồn dài)"),
                 ("breakdown", 4, "A", 1), ("chorus", 8, "B", 5), ("chorus", 8, "B", 5), ("outro", 8, "A", 2)],
    },
    "parts": {"intro": ["guitar", "drums", "hook"], "breakdown": ["guitar", "keys"]},
    "verse_stick": False,
    "ending": "fade",
    "surprises": [("drop_bar", "chorus"), ("half", "bridge"), ("riser", "chorus")],
    "transitions": {"chorus_from_bridge": "snare_build"},
    "hook": {"instrument": "guitar", "rhythms": ["x===x===x=======", "x.....x.....x===", "x=x=x===........"]},
}
