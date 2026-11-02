"""Jazz swing (mới): ride "ding-ding-da-ding", hat pedal 2–4, walking bass, piano rootless comping Charleston."""
PACK = {
    "label": "Jazz", "description": "Swing: ride ding-ding-da-ding, walking bass, piano rootless, guitar 4 nhát/ô.",
    "default_bpm": 120, "bpm_range": [90, 160], "grid": 12, "color": "rich",
    "feel": {"swing": 0.0, "swing_sub": "8n", "sigma_ms": {"drums": 5, "bass": 6, "keys": 10, "guitar": 9},
             "pocket_ms": {"kick": 0, "snare": 4, "hat": 0, "ride": -6, "bass": -3, "keys": 6, "guitar": 0},
             "roll_ms": [3, 12], "strum_ms": [4, 8]},
    "keys": {"instrument": "piano", "voicing": "rootless", "range": [50, 74], "top": 66, "max_span": 10,
             "patterns": {1: ["x=====......", "x==========."], 2: ["x====x......", "...x=....x=.", "x.....x....."],
                          3: ["x====x...x=.", "..x...x==..x", "x====x......"]}},
    "bass": {"instrument": "upright", "range": [28, 50], "walk": True, "approach": ["below", "above", "fifth"],
             "patterns": {1: ["R=====5====="]}},
    "guitar": {"instrument": "guitar", "voicing": "shell", "min_energy": 3,
               "patterns": {3: ["d..d..d..d.."]}},
    "drums": {
        "kit": "brush",
        "patterns": {
            1: [{"br_ride": "x..x.xx..x.x", "hh_p": "...x.....x..", "kick": "g.....g....."}],
            2: [{"ride": "x..x.xx..x.x", "hh_p": "...x.....x..", "kick": "g..g..g..g.."},
                {"ride": "x..x.xx..x.x", "hh_p": "...x.....x..", "snare": "........g...", "kick": "g..g..g..g.."}],
            3: [{"ride": "x..x.xx..x.x", "hh_p": "...x.....x..", "snare": ".....g....g.", "kick": "g..g..g..g.o"},
                {"ride": "x..x.xx..x.x", "hh_p": "...x.....x..", "snare": "..g.....g...", "kick": "g..g..g..o.."}],
        },
        "fills": {"small": [{"ride": "x..x.xx.....", "hh_p": "...x........", "snare": "........gxox", "kick": "g..g..g....."}],
                  "big": [{"ride": "x..x.x......", "snare": "...xox..x.ox", "tom_h": "......x.....", "tom_f": "........x.x."}]},
    },
    "fx": {"reverb": 0.1, "room": "room", "delay": 0.0, "lofi": False, "chorus": False, "drive": False},
}
