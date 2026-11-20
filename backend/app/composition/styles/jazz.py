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

# Jazz: Head A A B A (vòng A cho A, vòng B cho B), solo đệm cho học sinh ứng tác, kết tag ii–V × 3.
PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 2), ("verse", 8, "A", 3, "Head A"), ("bridge", 8, "B", 3, "Head B"),
                  ("outro", 8, "A", 2, "Tag ii–V")],
        "medium": [("intro", 4, "A", 2), ("verse", 8, "A", 3, "Head A"), ("verse", 8, "A", 3, "Head A"),
                   ("bridge", 8, "B", 3, "Head B"), ("verse", 8, "A", 3, "Head A"), ("solo", 16, "A", 4, "Solo"),
                   ("verse", 8, "A", 4, "Head A"), ("outro", 8, "A", 2, "Tag ii–V")],
        "full": [("intro", 4, "A", 2), ("verse", 8, "A", 3, "Head A"), ("verse", 8, "A", 3, "Head A"),
                 ("bridge", 8, "B", 3, "Head B"), ("verse", 8, "A", 3, "Head A"), ("solo", 16, "A", 4, "Solo"),
                 ("solo", 16, "B", 4, "Solo"), ("verse", 8, "A", 4, "Head A"), ("verse", 8, "A", 4, "Head A"),
                 ("bridge", 8, "B", 3, "Head B"), ("verse", 8, "A", 4, "Head A"), ("outro", 8, "A", 2, "Tag ii–V")],
    },
    "parts": {"intro": ["keys", "bass", "hook"]},
    "verse_stick": False,
    # Bù độ to Chorus − Verse (dB) đo trên bản thu 02/11/2026, xem song.sec_db.
    "chorus_trim_db": 0.0,
    "ending": "tag_x3",
    "surprises": [("stop_time", "solo"), ("stop_time", "verse"), ("reverse_cymbal", "solo")],
    "transitions": {},
    "hook": {"instrument": "piano", "rhythms": ["x==x.x=====.", "..x..x.x===.", "x.x..x======"]},
}
