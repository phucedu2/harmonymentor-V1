"""Ballad (id cũ "ballad"): cảm giác 12/8 trong 4/4 (QĐ 11A, lưới 12 = chia ba mỗi phách), piano tay trái rải 1-5-8-10."""
PACK = {
    "label": "Ballad", "description": "Chậm, cảm giác 12/8: piano rải tay trái 1-5-8-10, trống side-stick nhẹ.",
    "default_bpm": 70, "bpm_range": [60, 84], "grid": 12, "color": "add9",
    "feel": {"swing": 0.0, "swing_sub": "8n", "sigma_ms": {"drums": 6, "bass": 9, "keys": 12, "guitar": 15},
             "pocket_ms": {"kick": 0, "snare": 6, "hat": 0, "bass": 4, "keys": 8, "guitar": 6},
             "roll_ms": [8, 24], "strum_ms": [12, 20]},
    "keys": {"instrument": "piano", "voicing": "close", "range": [58, 79], "top": 72,
             "patterns": {1: ["r==========="], 2: ["x=====o=====", "r==========="], 3: ["X=====x=====", "x==x==x==x=="]},
             "lh": {1: ["1===========", "1=====5====="], 2: ["1..5..8..3..", "1..5..8..5.."], 3: ["1..5..8..3..", "1.58.53.58.5"]}},
    "bass": {"instrument": "bass", "range": [28, 50], "approach": ["scale", "below"],
             "patterns": {1: ["R==========="], 2: ["R=====5=====", "R=====5==.A."], 3: ["R=====R==5A.", "R=====5==8A."]}},
    "guitar": {"instrument": "guitar", "voicing": "open", "min_energy": 3,
               "patterns": {3: ["1==3==2==4==", "1==2==3==4=="]}},
    "drums": {
        "patterns": {
            1: [{"kick": "o.....o.....", "xstick": "............", "hh_p": "...o.....o.."}],
            2: [{"kick": "x.....x..o..", "xstick": "...x.....x..", "hh_c": "xooxooxooxoo"},
                {"kick": "x.....x.....", "xstick": "...x.....x..", "hh_c": "xooxooxooxoo"}],
            3: [{"kick": "X.....x..x..", "snare": "...X.....X..", "hh_c": "xooxooxooxoo"},
                {"kick": "X.....x.....", "snare": "...X.....X..", "ride": "xooxooxooxoo"}],
        },
        "fills": {
            "small": [{"kick": "x.....x.....", "snare": "...X.....xxx", "hh_c": "xooxooxoo..."}],
            "big": [{"kick": "X.....X.....", "snare": "...X..xxx...", "tom_h": ".........Xx.", "tom_f": "...........X"}],
        },
    },
    "fx": {"reverb": 0.3, "room": "hall", "delay": 0.0, "lofi": False, "chorus": False, "drive": False},
}

PACK["song"] = {
    "forms": {
        "short": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("outro", 4, "A", 1)],
        "medium": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("verse", 8, "A", 2),
                   ("chorus", 8, "B", 4), ("bridge", 4, "C", 3), ("chorus", 8, "B", 5), ("outro", 4, "A", 1)],
        "full": [("intro", 4, "A", 1), ("verse", 8, "A", 2), ("chorus", 8, "B", 4), ("verse", 8, "A", 2),
                 ("chorus", 8, "B", 4), ("bridge", 8, "C", 3), ("breakdown", 4, "A", 1), ("chorus", 8, "B", 5),
                 ("chorus", 4, "B", 5), ("outro", 4, "A", 1)],
    },
    "parts": {"intro": ["keys", "hook"], "breakdown": ["keys"]},
    "verse_stick": True,
    "ending": "ritardando_fermata",
    "surprises": [("drop_bar", "chorus"), ("reverse_cymbal", "chorus"), ("stop_time", "chorus")],
    "transitions": {"chorus": "reverse_cymbal"},
    "hook": {"instrument": "piano", "rhythms": ["x==x==x=====", "x=====x==x==", "...x==x=====", "x==x=====x=="]},
}
