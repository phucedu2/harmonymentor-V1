def L(h):
    h=h.lstrip('#');c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    c=[x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def cr(a,b):
    a,b=L(a),L(b);return (max(a,b)+0.05)/(min(a,b)+0.05)
T={
'SK light':dict(bg='#f4f2f8',surface='#ffffff',ink='#17142b',muted='#57536e',primary='#4b33b8',onp='#ffffff',success='#1d6b40',danger='#b02a37',warning='#7a4a00',soft='#e8e3fa'),
'SK dark':dict(bg='#0e0c1b',surface='#18152b',ink='#ecebf5',muted='#a9a5c2',primary='#f2b33d',onp='#1a1405',success='#74d39c',danger='#ff9a94',warning='#f2b33d',soft='#2d2614'),
'GN light':dict(bg='#fbf8f1',surface='#fffdf8',ink='#1d1b18',muted='#5c564b',primary='#9e2a2b',onp='#ffffff',success='#2a6a3c',danger='#a3242b',warning='#7a4a00',soft='#f6e4df'),
'GN dark':dict(bg='#17150f',surface='#211e17',ink='#efe9dc',muted='#b3aa97',primary='#f0938a',onp='#2a0d0b',success='#8fd19e',danger='#ff9a94',warning='#e8c06a',soft='#3a201d'),
}
for n,t in T.items():
    out=[]
    for k in ['ink','muted','primary','success','danger','warning']:
        out.append(f"{k}/bg {cr(t[k],t['bg']):.1f} /surf {cr(t[k],t['surface']):.1f}")
    out.append(f"onp/primary {cr(t['onp'],t['primary']):.1f}  primary/soft {cr(t['primary'],t['soft']):.1f} ink/soft {cr(t['ink'],t['soft']):.1f}")
    print(n,'|',' ; '.join(out))
