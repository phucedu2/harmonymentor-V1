"""Pop (id cũ "pop"): trống chắc, hợp âm 3 nốt dẫn giọng, bass móc đơn đi vào gốc ô sau."""
PACK = {
    "label": "Pop", "description": "Trống chắc, kick 1 và 'và-của-3', hợp âm có dẫn giọng, guitar quạt ở cao trào.",
    "default_bpm": 100, "bpm_range": [80, 130], "grid": 16, "color": "add9",
    "feel": {"swing": 0.0, "swing_sub": "8n", "sigma_ms": {"drums": 5, "bass": 7, "keys": 9, "guitar": 12},
             "pocket_ms": {"kick": 0, "snare": 3, "hat": -2, "bass": 2, "keys": 4, "guitar": 0},
             "roll_ms": [4, 14], "strum_ms": [7, 12]},
    "keys": {"instrument": "piano", "voicing": "close", "range": [53, 79], "top": 69,
             "patterns": {1: ["o===============", "o=======o======="],
                          2: ["X=====x=X=====x=", "X===x===X===x==="],
                          3: ["X=====x=X=====x=", "X=x===x=X=x===x="]}},
    "bass": {"instrument": "bass", "range": [28, 50], "approach": ["below", "scale", "above"],
             "patterns": {1: ["R=======R======="],
                          2: ["R==.R.R.R==.5.A.", "R=====R=5=====A="],
                          3: ["R.R.R.R.R.R.R.A.", "R=.RR=.R5=.5R=A."]}},
    "guitar": {"instrument": "guitar", "voicing": "open", "min_energy": 2,
               "patterns": {2: ["1=3=2=4=1=3=2=4=", "1===3===2===4==="],
                            3: ["D.DU.UDUD.DU.UDU", "D.DU.UDUD.D..UDU"]}},
    "drums": {
        "patterns": {
            1: [{"kick": "x.......x.......", "xstick": "....o.......o...", "hh_c": "o.o.o.o.o.o.o.o."}],
            2: [{"kick": "X.......x.x.....", "snare": "....X.......X...", "hh_c": "x.o.x.o.x.o.x.o."},
                {"kick": "X......xx.......", "snare": "....X.......X..g", "hh_c": "x.o.x.o.x.o.x.oo"},
                {"kick": "X.......x.x...x.", "snare": "....X.......X...", "hh_c": "x.o.x.o.x.o.x.o."}],
            3: [{"kick": "X.....x.x.x.....", "snare": "....X..g....X...", "hh_c": "X.x.X.x.X.x.X...",
                 "hh_o": "..............x."},
                {"kick": "X.......x.x...x.", "snare": "....X.......X...", "ride": "x.x.x.x.x.x.x.x.",
                 "ride_b": "x.......x......."}],
        },
        "fills": {
            "small": [{"kick": "X.......x.......", "snare": "....X.......XxXx", "hh_c": "x.o.x.o.x.o....."},
                      {"kick": "X.......x.......", "snare": "....X.......X...", "hh_c": "x.o.x.o.x.o.....",
                       "tom_h": "............Xx..", "tom_f": "..............Xx"}],
            "big": [{"kick": "X.......X.......", "snare": "....X...XxxxX...", "hh_c": "x.x.x.x.........",
                     "tom_h": "............Xx..", "tom_m": "..............X.", "tom_f": "...............X"},
                    {"kick": "X.......X.....x.", "snare": "....X...Xx.xXx..", "tom_h": "........Xx......",
                     "tom_m": "..........Xx....", "tom_f": "..............XX", "hh_c": "x.x.x.x........."}],
        },
    },
    "fx": {"reverb": 0.16, "room": "room", "delay": 0.0, "lofi": False, "chorus": False, "drive": False},
}

# Bài hát (ADR-013 đề xuất): khuôn theo độ dài, luật từng loại đoạn, kết bài, đột biến cho phép, hook.
# Mỗi đoạn: (loại, số ô, vòng, năng lượng 1–5[, nhãn]). Nguồn: docs/backing-track/CAU_TRUC_BAI_HAT.md mục B.
PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("outro", 4, "A", 2)],
        "medium": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4),
                   ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("bridge", 8, "C", 3),
                   ("chorus", 8, "B", 5), ("outro", 4, "A", 2)],
        "full": [("intro", 4, "A", 1), ("verse", 16, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4),
                 ("post", 4, "B", 3), ("verse", 8, "A", 2), ("pre", 4, "A", 3), ("chorus", 8, "B", 4), ("post", 4, "B", 3),
                 ("bridge", 8, "C", 3), ("breakdown", 4, "A", 1), ("pre", 4, "A", 3), ("chorus", 8, "B", 5),
                 ("chorus", 8, "B", 5), ("outro", 8, "A", 2)],
    },
    "parts": {"intro": ["keys", "hook"], "breakdown": ["keys"]},
    "verse_stick": True,
    "ending": "fade",
    "surprises": [("drop_bar", "chorus"), ("stop_time", "chorus"), ("half", "bridge"), ("reverse_cymbal", "chorus")],
    "transitions": {},
    "hook": {"instrument": "piano", "rhythms": ["x.x.x=======....", "x=..x=..x=======", "..x.x.x=x=======",
                                                "x=x=x===x======="]},
}
