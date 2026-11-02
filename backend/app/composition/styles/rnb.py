"""R&B / Soul (mới): swing 16 nhẹ, snare + clap trễ, hat 16, conga/shaker/triangle, phím điện m9/maj9 rải chậm."""
PACK = {
    "label": "R&B", "description": "Nhịp 16 lắc nhẹ, snare + clap trễ phách, conga và shaker, phím điện rải chậm.",
    "default_bpm": 78, "bpm_range": [64, 92], "grid": 16, "color": "rich",
    "feel": {"swing": 0.55, "swing_sub": "16n", "sigma_ms": {"drums": 6, "bass": 8, "keys": 12, "guitar": 12},
             "pocket_ms": {"kick": 0, "snare": 14, "hat": 2, "bass": 6, "keys": 10, "guitar": 6},
             "roll_ms": [12, 30], "strum_ms": [10, 18]},
    "keys": {"instrument": "epiano", "voicing": "rootless", "range": [52, 77], "top": 69, "max_span": 12,
             "patterns": {1: ["r==============="], 2: ["r=======r=======", "r=========..t==="], 3: ["r=====t=r=====t=", "r=======..t.r==="]}},
    "bass": {"instrument": "bass", "range": [28, 48], "approach": ["below", "above"],
             "patterns": {1: ["R==============="], 2: ["R=======..5=.A..", "R=========..R=A."], 3: ["R=====R...5=.A..", "R=======..R.5.A."]}},
    "guitar": {"instrument": "guitar", "voicing": "high", "min_energy": 3,
               "patterns": {3: ["..........2=1===", "......3=2=......"]}},
    "drums": {
        "patterns": {
            1: [{"kick": "X.........x.....", "xstick": "....o.......o...", "hh_c": "o.o.o.o.o.o.o.o."}],
            2: [{"kick": "X......x..x.....", "snare": "....X.......X...", "hh_c": "xoxoxoxoxoxoxoxo"},
                {"kick": "X.....x...x..x..", "snare": "....X.......X...", "hh_c": "xoxoxoxoxoxoxoxo"}],
            3: [{"kick": "X......x..x...x.", "snare": "....X..g....X...", "hh_c": "xoxoxoxoxoxoxo..", "hh_o": "..............x."}],
        },
        "fills": {"small": [{"kick": "X......x..x.....", "snare": "....X.......X.gg", "hh_c": "xoxoxoxoxoxo...."}],
                  "big": [{"kick": "X......x........", "snare": "....X...g.gX....", "tom_h": "............xx..",
                           "tom_f": "..............XX"}]},
        "perc": {1: [{"shaker": "x.o.x.o.x.o.x.o."}],
                 2: [{"clap": "....x.......x...", "shaker": "x.o.x.o.x.o.x.o.", "conga_h": "..o...o..o..o..."}],
                 3: [{"clap": "....x.......x...", "shaker": "xoxoxoxoxoxoxoxo", "conga_h": "..o...o..o..o...",
                      "conga_l": "x.......x.......", "tri": "....x.......x..."}]},
    },
    "fx": {"reverb": 0.22, "room": "plate", "delay": 0.0, "lofi": False, "chorus": False, "drive": False},
}

PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("outro", 4, "A", 2)],
        "medium": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4),
                   ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("bridge", 4, "C", 3),
                   ("chorus", 8, "B", 5), ("outro", 4, "A", 2)],
        "full": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("post", 4, "B", 3),
                 ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("post", 4, "B", 3),
                 ("bridge", 8, "C", 3), ("chorus", 8, "B", 5), ("chorus", 8, "B", 5), ("outro", 4, "A", 2)],
    },
    "parts": {"intro": ["keys", "perc", "hook"], "breakdown": ["keys"]},
    "verse_stick": True,
    # Bù độ to Chorus − Verse (dB) đo trên bản thu 02/11/2026, xem song.sec_db.
    "chorus_trim_db": -0.3,
    "ending": "ritardando_fermata",
    "surprises": [("drop_bar", "chorus"), ("half", "bridge"), ("reverse_cymbal", "chorus"), ("riser", "chorus")],
    "transitions": {},
    "hook": {"instrument": "epiano", "rhythms": ["..x=x=x=========", "x=.x..x=x=======", "....x.x.x======="]},
}
