import sys; sys.path.insert(0,'tests')
import test_music21_crosscheck as t
from app.music_engine.errors import MusicEngineError
from app.music_engine import *
from music21 import interval as mi, pitch as mp, harmony
# interval pairs
checked=0; skipped=0
for a in t.ALL_SPELLINGS:
    lo=a.with_octave(4)
    for b in t.ALL_SPELLINGS:
        for o in (4,5):
            hi=b.with_octave(o)
            if hi.diatonic_index<lo.diatonic_index: continue
            try: interval_between(lo,hi); checked+=1
            except MusicEngineError: skipped+=1
print('interval pairs compared',checked,'rejected by engine',skipped)
n=0;rej=0
for iv in ["P1","A1","m2","M2","A2","d3","m3","M3","A3","d4","P4","A4","d5","P5","A5","m6","M6","A6","d7","m7","M7","d8","P8","M9","m10"]:
    for r in t.COMMON_ROOTS:
        try: transpose(r.with_octave(4),iv); n+=1
        except MusicEngineError: rej+=1
print('transpose cases',n,'rejected(>±2)',rej)
from app.music_engine.chord import CHORD_TYPES
c=0;cr=0
for ct in CHORD_TYPES:
    for r in t.COMMON_ROOTS:
        try: chord_tones(f"{r.name}{CHORD_TYPES[ct].display}"); c+=1
        except MusicEngineError: cr+=1
print('chord cases',c,'rejected',cr, 'types',len(CHORD_TYPES),'roots',len(t.COMMON_ROOTS))
s=0
for st in t.M21_SCALES:
    for r in t.COMMON_ROOTS:
        try: build_scale(r,st); s+=1
        except MusicEngineError: pass
print('scale cases',s)
from app.music_engine.key import all_supported_keys
print('keys',len(all_supported_keys('major')),len(all_supported_keys('minor')))
r=0
for ks in all_supported_keys('major'):
    for sv in (False,True): r+=len(diatonic_chords(ks.tonic,sv))
print('roman cases',r)
