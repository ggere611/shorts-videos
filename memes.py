"""Memes originales (no infantiles) con las mascotas 3D.
Uso: python3 memes.py <sueno|parcial|plata> salida.mp4 [preview]
Formato: situación -> remate con golpe de zoom y sonido; 10-12 s, pensado para loop.
"""
import math, os, sys, wave
os.environ.setdefault("MASC_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mascotas3d"))
import numpy as np
from PIL import Image, ImageDraw
import nichos as N, cuentos as Q
from nichos import W, H, F, text_c, ease_back
from cuentos import BASE, actor
from episodios import estado, objeto, A, P

def texto_meme(d, txt, lt, noche):
    f = F(84); lines = []
    for par in txt.split("\n"):
        cur = ""
        for w_ in par.split():
            if f.getlength((cur + " " + w_).strip()) <= 960: cur = (cur + " " + w_).strip()
            else: lines.append(cur); cur = w_
        lines.append(cur)
    k = ease_back(lt / 0.22)
    for i, l in enumerate(lines):
        text_c(d, (W / 2, 300 + i * 108), l, 84, (255, 255, 255), (15, 15, 20), 12, scale=k)

def frame(M, t):
    acc = 0
    for i, b in enumerate(M):
        if t < acc + b["dur"] or i == len(M) - 1: break
        acc += b["dur"]
    lt = t - acc; noche = b.get("fondo") == "noche"
    col = (22, 28, 58) if noche else b.get("color", (255, 214, 102))
    im = Image.new("RGB", (W, H), col); d = ImageDraw.Draw(im)
    piso = (34, 42, 80) if noche else tuple(int(c * 0.86) for c in col)
    d.ellipse([-300, BASE - 70, W + 300, BASE + 1100], fill=piso)
    Q.SOMBRA = tuple(int(c * 0.7) for c in piso)
    acts = b.get("a", []); est = [estado(s, lt, t, 99) for s in acts]
    for p in b.get("p", []):
        if p[4].get("atras"): im = objeto(im, d, p, lt, t, est)
    for s, e in zip(acts, est):
        if e: actor(im, d, s[0], e[1], t, e[0], s[3].get("s", 520), e[2], e[3], e[4])
    for p in b.get("p", []):
        if not p[4].get("atras"): im = objeto(im, d, p, lt, t, est)
    d = ImageDraw.Draw(im); texto_meme(d, b["t"], lt, noche)
    if b.get("boom") and lt < 0.35:      # golpe de zoom en el remate
        z = 1 + 0.16 * (1 - lt / 0.35); w2, h2 = int(W / z), int(H / z)
        im = im.crop(((W - w2) // 2, (H - h2) // 2 + 60, (W - w2) // 2 + w2, (H - h2) // 2 + 60 + h2)).resize((W, H), Image.BILINEAR)
    return im

def audio(M, path, sr=44100):
    dur = sum(b["dur"] for b in M); a = np.zeros(int(dur * sr)); tt = np.arange(len(a)) / sr
    a += 0.05 * np.sin(2 * np.pi * 110 * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 2 * tt))   # pulso de fondo
    acc = 0
    for b in M:
        i0 = int(acc * sr)
        m = int(0.12 * sr); x = np.arange(m) / sr                      # "pop" al cambiar el texto
        a[i0:i0 + m] += 0.25 * np.sin(2 * np.pi * (700 - 2500 * x) * x) * np.exp(-x * 30)
        if b.get("boom"):
            m = int(0.9 * sr); x = np.arange(m) / sr
            a[i0:i0 + m] += 0.95 * np.sin(2 * np.pi * (58 * x + 40 * (1 - np.exp(-x * 9)) / 9)) * np.exp(-x * 4.5)
        acc += b["dur"]
    a = np.tanh(a * 1.3) * 0.9
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((a * 32767).astype(np.int16).tobytes())

MEMES = {
 "sueno": [
  dict(t='Yo a las 22:00:\n"hoy me duermo temprano"', dur=3.0, color=(186, 225, 255),
       a=[A("rana", 540, "saluda", s=560)], p=[P("🛏️", 880, 150, s=300, atras=True)]),
  dict(t="Yo a las 3:47 AM:", dur=4.2, fondo="noche", boom=True,
       a=[A("rana", 520, "tiembla", s=640)], p=[P("📱", 820, 330, "flota", s=220), P("🌙", 880, 1000, s=170, atras=True), P("", 800, 340, "luz", dir=-1, atras=True)]),
  dict(t='"un videíto más y ya"', dur=3.2, fondo="noche",
       a=[A("rana", 520, "busca", s=640)], p=[P("📱", 820, 330, "flota", s=220), P("🌙", 880, 1000, s=170, atras=True), P("", 800, 340, "luz", dir=-1, atras=True)]),
 ],
 "parcial": [
  dict(t='El profe:\n"el parcial es re fácil"', dur=3.0, color=(200, 240, 200),
       a=[A("gato", 540, "saluda", s=560)], p=[P("📚", 860, 90, s=220)]),
  dict(t="El parcial:", dur=4.0, color=(255, 120, 110), boom=True,
       a=[A("monstruo", 640, "quieto", m="izq", s=1050), A("oso", 190, "tiembla", s=260)], p=[P("txt:¡GRRR!", 270, 720, d=0.3, s=120)]),
  dict(t='Yo: "¿esto lo vimos?"', dur=3.4, color=(255, 120, 110),
       a=[A("monstruo", 640, "quieto", m="izq", s=1050), A("oso", 190, "triste", s=260)], p=[P("❓", 200, 420, "flota", s=150)]),
 ],
 "plata": [
  dict(t="Yo el día 1 del mes:", dur=3.2, color=(190, 240, 170),
       a=[A("toro", 540, "salta", s=600)], p=[P("💸", 240, 900, "flota", s=200), P("💸", 860, 760, "flota", s=180), P("🛍️", 880, 100, s=240), P("🍕", 200, 90, s=200)]),
  dict(t="Yo el día 5:", dur=3.6, color=(190, 195, 205), boom=True,
       a=[A("toro", 540, "triste", s=600)], p=[P("🕸️", 870, 200, s=280, atras=True), P("🪙", 240, 60, "cae", d=0.5, s=110)]),
  dict(t='"¿Aceptan pago\nel mes que viene?"', dur=3.2, color=(190, 195, 205),
       a=[A("toro", 540, "saluda", s=600)], p=[P("🕸️", 870, 200, s=280, atras=True), P("🪙", 240, 60, s=110)]),
 ],
}

if __name__ == "__main__":
    M = MEMES[sys.argv[1]]; dur = sum(b["dur"] for b in M); fn = lambda t: frame(M, t)
    if len(sys.argv) > 3:
        acc = 0; ims = []
        for b in M: ims.append(fn(acc + b["dur"] * 0.6).resize((270, 480))); acc += b["dur"]
        c = Image.new("RGB", (270 * len(ims), 480)); [c.paste(m, (k * 270, 0)) for k, m in enumerate(ims)]
        c.save(f"/tmp/meme_{sys.argv[1]}.jpg"); sys.exit()
    audio(M, "/tmp/_meme.wav"); N.render(fn, dur, sys.argv[2], "/tmp/_meme.wav")
