"""Serie de terror "Argentina inexplicable" — episodios narrados (no infantil).
Uso: python3 terror/serie.py familiar salida.mp4 [preview]
Narrador: Piper TTS (es-carlfm, dominio público) bajado de tono y con eco.
Todo el sonido (drone, latidos, cadenas, golpe) es sintetizado: sin copyright.
"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import nichos as N
import cuentos as Q

W, H, FPS, SR = 1080, 1920, 30, 44100
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_f = {}
def F(s, serif=True):
    k = (s, serif)
    if k not in _f: _f[k] = ImageFont.truetype(SERIF if serif else SANS, s)
    return _f[k]
def sm(k): k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)
def lerp(a, b, k): return a + (b - a) * max(0.0, min(1.0, k))

# ------------------------------------------------------------------ guion
FAMILIAR = dict(
  titulo="El Familiar", ep=1, proximo="El Lobizón",
  beats=[
    ("hook",   "Si de noche escuchás cadenas... no mires atrás.", 0.7),
    ("lugar",  "Tucumán. Los viejos ingenios azucareros. De día, puro trabajo. De noche... otra cosa.", 0.5),
    ("pacto",  "Decían que el patrón había hecho un pacto. Riqueza... a cambio de un peón por año.", 0.7),
    ("peon",   "Una noche, un peón volvía solo por el cañaveral.", 0.5),
    ("cadenas","Y atrás suyo escuchó algo. Cadenas. Arrastrándose. Despacio.", 1.3),
    ("frena",  "Se frenó. Las cadenas... también.", 1.8),
    ("ojos",   "No quiso darse vuelta. Levantó el farol para ver el camino. Y adelante... había dos ojos.", 1.5),
    ("scare",  "", 1.7),
    ("final",  "A la mañana encontraron el farol. Todavía prendido. Del peón... nunca más se supo.", 0.9),
    ("cierre", "Dicen que El Familiar sigue ahí. Esperando al próximo.", 2.6),
  ])

# ------------------------------------------------------------------ voz
def voz(texto, clave):
    crudo = f"/tmp/_tv_{clave}_raw.wav"; out = f"/tmp/_tv_{clave}.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", Q.modelo_voz(), "-f", crudo, "--length-scale", "1.12"],
                   input=texto.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sr = wave.open(crudo).getframerate()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", crudo, "-af",
                    f"asetrate={int(sr*0.86)},aresample={SR},lowpass=f=4200,aecho=0.8:0.55:70|140:0.28|0.16,volume=1.6",
                    "-ac", "1", "-ar", str(SR), out], check=True)
    w = wave.open(out); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    return x

class Linea:
    def __init__(self, ep, nombre):
        self.ep = ep; self.b = []; t = 0.4
        for i, (clave, txt, pausa) in enumerate(ep["beats"]):
            x = voz(txt, f"{nombre}_{i}") if txt else np.zeros(1)
            vd = len(x) / SR if txt else 0.0
            self.b.append(dict(clave=clave, txt=txt, ini=t, vd=vd, fin=t + vd + pausa, x=x)); t += vd + pausa
        self.dur = t + 0.3
    def en(self, t):
        cur = self.b[0]
        for b in self.b:
            if t >= b["ini"]: cur = b
        return cur, t - cur["ini"]
    def ini(self, clave): return next(b["ini"] for b in self.b if b["clave"] == clave)

# ------------------------------------------------------------------ capas fijas
def degradado(top, bot):
    a = np.linspace(0, 1, H)[:, None, None]; im = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a)
    return Image.fromarray(np.repeat(im, W, axis=1).astype(np.uint8))
def radial(size, color, potencia=2.0):
    y, x = np.mgrid[-1:1:size * 1j, -1:1:size * 1j]; r = np.clip(1 - np.sqrt(x * x + y * y), 0, 1) ** potencia
    return Image.fromarray((r[:, :, None] * np.array(color)[None, None, :]).astype(np.uint8))
def niebla(seed):
    rng = np.random.default_rng(seed); a = rng.random((40, 48)) ** 2
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((W * 2, 700), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    return im
CIELO = degradado((10, 14, 34), (26, 32, 54)); CIELO_ALBA = degradado((30, 32, 52), (70, 62, 66))
LUNA = radial(520, (150, 160, 190), 3.2); GLOW = [radial(1000, (int(255 * k), int(150 * k), int(50 * k)), 2.2) for k in (0.55, 0.75, 0.95)]
OJO = radial(160, (255, 20, 10), 2.6); NIEBLA = [niebla(3), niebla(9)]
rng0 = np.random.default_rng(5)
GRANO = [Image.fromarray(rng0.integers(0, 60, (H // 2, W // 2), dtype=np.uint8)).resize((W, H)).convert("RGB") for _ in range(4)]
yy, xx = np.mgrid[-1:1:H * 1j, -1:1:W * 1j]
VIN = Image.fromarray((np.clip(1.22 - (xx ** 2 * 0.75 + yy ** 2 * 0.6), 0.3, 1) * 255).astype(np.uint8)).convert("RGB")
rs = random.Random(11)
CANAS = [(rs.uniform(0, 1), rs.uniform(0.75, 1.25), rs.uniform(0, 6.28), rs.uniform(-0.25, 0.25)) for _ in range(150)]
SUELO = 1430

def luz(im, capa, cx, cy):
    lay = Image.new("RGB", (W, H)); lay.paste(capa, (int(cx - capa.width / 2), int(cy - capa.height / 2)))
    return ImageChops.screen(im, lay)

def canaveral(d, t, lado, base=SUELO, alto=820, col=(3, 4, 8)):
    """Pared de cañas a un lado del camino; lado=-1 izq, 1 der."""
    for i, (u, h, ph, incl) in enumerate(CANAS):
        if (i % 2 == 0) != (lado < 0): continue
        x0 = (u * 330) if lado < 0 else (W - u * 330); hh = alto * h; y0 = base + 40 + (i % 7) * 26
        sway = 26 * math.sin(t * 1.3 + ph) + 80 * incl
        d.line([(x0, y0), (x0 + sway * 0.4, y0 - hh * 0.55), (x0 + sway, y0 - hh)], fill=col, width=7 + i % 5)
        for k in (0.55, 0.75, 0.92):   # hojas
            xb, yb = x0 + sway * k, y0 - hh * k; s = 1 if (i + int(k * 10)) % 2 else -1
            d.line([(xb, yb), (xb + s * 70, yb + 46)], fill=col, width=5)

def camino(d, alba=False):
    c = (26, 24, 26) if not alba else (64, 56, 54); t_ = (12, 12, 16) if not alba else (40, 38, 40)
    d.rectangle([0, SUELO - 40, W, H], fill=t_)
    d.polygon([(440, SUELO - 40), (640, SUELO - 40), (980, H), (100, H)], fill=c)

def peon(d, x, t, anda=True, farol_y=0):
    gy = SUELO + 60; c = (2, 2, 4); s = math.sin(t * 6.5) if anda else 0
    d.line([(x, gy - 150), (x - 34 * s, gy)], fill=c, width=24); d.line([(x, gy - 150), (x + 34 * s, gy)], fill=c, width=24)
    d.polygon([(x - 44, gy - 150), (x + 44, gy - 150), (x + 36, gy - 330), (x - 36, gy - 330)], fill=c)
    d.ellipse([x - 30, gy - 396, x + 30, gy - 336], fill=c); d.ellipse([x - 62, gy - 372, x + 62, gy - 350], fill=c)
    d.rectangle([x - 34, gy - 404, x + 34, gy - 362], fill=c)
    fx, fy = x + 96, gy - 200 - farol_y
    d.line([(x + 20, gy - 300), (fx, fy - 40)], fill=c, width=18)
    d.rectangle([fx - 15, fy - 34, fx + 15, fy + 22], fill=(255, 190, 90)); d.rectangle([fx - 20, fy - 44, fx + 20, fy - 34], fill=c)
    return fx, fy

def ojos(im, cx, cy, escala, k=1.0):
    if k <= 0.02: return im
    o = OJO.resize((max(8, int(160 * escala)),) * 2); o = Image.eval(o, lambda v: int(v * k)); sep = 62 * escala
    for s in (-1, 1): im = luz(im, o, cx + s * sep, cy)
    return im

def perro(d, cx, cy, s):
    """Silueta original de perro enorme de frente."""
    c = (0, 0, 0)
    d.ellipse([cx - 300 * s, cy - 250 * s, cx + 300 * s, cy + 330 * s], fill=c)
    for q in (-1, 1): d.polygon([(cx + q * 150 * s, cy - 190 * s), (cx + q * 330 * s, cy - 520 * s), (cx + q * 300 * s, cy - 60 * s)], fill=c)
    d.ellipse([cx - 180 * s, cy + 120 * s, cx + 180 * s, cy + 520 * s], fill=c)
    d.ellipse([cx - 700 * s, cy + 300 * s, cx + 700 * s, cy + 2200 * s], fill=c)

def subtitulo(d, b, lt):
    if not b["txt"]: return
    partes = [p.strip() for p in b["txt"].replace("...", "…").replace("…", "…|").replace(". ", ".|").split("|") if p.strip()]
    pesos = [len(p) + 6 for p in partes]; tot = sum(pesos); f = min(0.999, lt / max(0.1, b["vd"])); acc = 0; cur = partes[-1]
    if lt < b["vd"]:
        for p, w_ in zip(partes, pesos):
            acc += w_ / tot
            if f < acc: cur = p; break
    elif lt > b["vd"] + 0.9: return
    fnt = F(60); words = cur.split(); lines = []; l = ""
    for w_ in words:
        if fnt.getlength((l + " " + w_).strip()) <= 920: l = (l + " " + w_).strip()
        else: lines.append(l); l = w_
    lines.append(l)
    for i, ln in enumerate(lines):
        d.text((W / 2, 1610 + i * 78), ln, font=fnt, fill=(238, 232, 220), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))

def cabecera(d, ep, a=1.0):
    c = (int(150 * a), int(20 * a), int(20 * a))
    d.text((W / 2, 150), "A R G E N T I N A   I N E X P L I C A B L E", font=F(30, False), fill=c, anchor="mm")
    d.text((W / 2, 196), f"EPISODIO {ep['ep']}", font=F(24, False), fill=(int(110 * a),) * 3, anchor="mm")

def cuadro(L, t):
    ep = L.ep; b, lt = L.en(t); k = b["clave"]; dur_b = b["fin"] - b["ini"]
    if k == "hook":
        im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
        a = sm(lt / 0.5) * (0.82 + 0.18 * math.sin(t * 31))
        d.text((W / 2, 820), "NO MIRES", font=F(150), fill=(int(190 * a), 0, 0), anchor="mm")
        d.text((W / 2, 1000), "ATRÁS", font=F(190), fill=(int(210 * a), 0, 0), anchor="mm")
        im = ojos(im, W / 2, 1330, 0.5, sm((lt - 1.2) / 1.5) * (0 if (t % 2.7) < 0.12 else 1))
        d = ImageDraw.Draw(im); subtitulo(d, b, lt)
    elif k in ("lugar", "pacto"):
        im = CIELO.copy(); im = luz(im, LUNA, 800, 430); d = ImageDraw.Draw(im)
        d.ellipse([757, 387, 843, 473], fill=(206, 212, 228))
        z = 1 + 0.03 * (t - L.ini("lugar"))
        d.rectangle([0, 1280, W, H], fill=(5, 6, 10))
        d.polygon([(120, 1290), (120, 1010), (330, 930), (540, 1010), (540, 1290)], fill=(4, 5, 9))       # galpón
        d.polygon([(250, 1100), (268, 520), (332, 520), (350, 1100)], fill=(4, 5, 9))                     # chimenea
        rojo = sm((t - L.ini("pacto")) / 2.5) if k == "pacto" else 0
        for j in range(3): d.rectangle([170 + j * 120, 1120, 220 + j * 120, 1190], fill=(int(lerp(70, 200, rojo)), int(lerp(55, 20, rojo)), int(lerp(20, 10, rojo))))
        for j in range(7):      # humo
            ph = (t * 0.22 + j / 7) % 1; r = 40 + 120 * ph; xh = 300 + 90 * ph + 30 * math.sin(t + j); yh = 520 - 430 * ph
            g = int(lerp(46, 14, ph)); d.ellipse([xh - r, yh - r * 0.7, xh + r, yh + r * 0.7], fill=(int(g + 60 * rojo * (1 - ph)), g, g + 4))
        canaveral(d, t, -1, base=1560, alto=560); canaveral(d, t, 1, base=1560, alto=560)
        if rojo: im = luz(im, Image.eval(GLOW[0], lambda v: int(v * rojo * 0.5)), 300, 1150)
        d = ImageDraw.Draw(im); cabecera(d, ep, sm(lt / 1.0) if k == "lugar" else 1); subtitulo(d, b, lt)
    elif k in ("peon", "cadenas", "frena", "ojos", "final", "cierre"):
        alba = k == "final"
        im = (CIELO_ALBA if alba else CIELO).copy()
        if not alba: im = luz(im, LUNA.resize((360, 360)), 250, 330)
        d = ImageDraw.Draw(im); camino(d, alba)
        tp = L.ini("peon"); x = lerp(250, 540, (t - tp) / (L.ini("frena") - tp + 0.4))
        quieto = k in ("frena", "ojos")
        col = (3, 4, 8) if not alba else (18, 20, 26)
        canaveral(d, t, -1, col=col); canaveral(d, t, 1, col=col)
        if k in ("peon", "cadenas", "frena", "ojos"):
            sube = 60 * sm((lt - b["vd"] * 0.35) / 0.8) if k == "ojos" else 0
            fx, fy = peon(d, x, t, anda=not quieto, farol_y=sube)
            par = 0 if (k in ("cadenas", "frena") and random.Random(int(t * 13)).random() < 0.18) else 1 + (int(t * 9) % 2)
            im = luz(im, GLOW[par], fx, fy)
            if k == "ojos":
                a = sm((lt - b["vd"] * 0.78) / 0.9); im = ojos(im, 800, SUELO - 120, 0.34 + 0.1 * a, a)
        elif k == "final":
            d.rectangle([520, SUELO + 40, 550, SUELO + 96], fill=(255, 190, 90)); im = luz(im, GLOW[1 + int(t * 7) % 2].resize((520, 520)), 535, SUELO + 70)
        else:   # cierre: camino vacío, ojos que parpadean al fondo
            a = sm((lt - 0.6) / 1.2) * (0 if 0.0 < ((t * 0.7) % 1) < 0.07 else 1); im = ojos(im, 540, SUELO - 150, 0.3, a * 0.9)
        nb = NIEBLA[0].crop((int((t * 38) % W), 0, int((t * 38) % W) + W, 700))
        im.paste(Image.new("RGB", (W, 700), (60, 66, 84) if not alba else (120, 112, 112)), (0, SUELO - 380), Image.eval(nb, lambda v: int(v * 0.42)))
        d = ImageDraw.Draw(im); cabecera(d, ep)
        if k == "cierre" and lt > b["vd"] + 0.3:
            a = sm((lt - b["vd"] - 0.3) / 0.8)
            d.text((W / 2, 700), ep["titulo"].upper(), font=F(110), fill=(int(200 * a), int(10 * a), int(10 * a)), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
            d.text((W / 2, 830), f"Próximo episodio: {ep['proximo']}", font=F(44, False), fill=(int(220 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
            d.text((W / 2, 910), "Seguí la serie… si te animás.", font=F(40, False), fill=(int(170 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
        subtitulo(d, b, lt)
    else:   # scare
        if lt < 0.07: return Image.new("RGB", (W, H), (255, 240, 235))
        if lt > 1.25: return Image.new("RGB", (W, H), (0, 0, 0))
        g = sm(lt / 0.32); pulso = 0.5 + 0.5 * math.sin(lt * 70)
        im = Image.new("RGB", (W, H), (int(70 + 60 * pulso), 0, 0)); d = ImageDraw.Draw(im)
        s = lerp(0.35, 1.5, g); jx, jy = random.Random(int(t * 30)).uniform(-26, 26), random.Random(int(t * 30) + 1).uniform(-26, 26)
        perro(d, W / 2 + jx, 760 + jy, s); im = ojos(im, W / 2 + jx, 720 + jy, 1.0 + 1.6 * g, 1)
    im = ImageChops.multiply(im, VIN); im = Image.blend(im, GRANO[int(t * 24) % 4], 0.055)
    if t < 0.4: im = Image.eval(im, lambda v: int(v * t / 0.4))
    if t > L.dur - 0.9: im = Image.eval(im, lambda v: int(v * max(0, (L.dur - t) / 0.9)))
    return im

# ------------------------------------------------------------------ sonido
def pasa_bajos(x, n): return np.convolve(x, np.ones(n) / n, "same")
def sonido(L, path):
    n = int(L.dur * SR); t = np.arange(n) / SR; rng = np.random.default_rng(13); a = np.zeros(n)
    def env(t0, t1, fa=0.6):   # ventana suave entre t0 y t1
        return np.clip((t - t0) / fa, 0, 1) * np.clip((t1 - t) / fa, 0, 1)
    tf, to, ts, tfin = L.ini("frena"), L.ini("ojos"), L.ini("scare"), L.ini("final")
    drone = (np.sin(2 * np.pi * 55 * t) + 0.7 * np.sin(2 * np.pi * 58.3 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t + 2 * np.sin(2 * np.pi * 0.13 * t)))
    drone *= 0.085 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t)) * (1 - 0.9 * env(tf, to, 0.4)) * (1 - env(ts + 1.2, tfin + 0.5, 0.3))
    viento = pasa_bajos(rng.standard_normal(n), 220) * 2.2 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + 1)) * 0.16
    a += drone + viento
    tc = L.ini("cadenas"); bc = next(b for b in L.b if b["clave"] == "cadenas")   # cadenas
    def cadena(t0, vol):
        m = int(0.42 * SR); tt = np.arange(m) / SR; ru = rng.standard_normal(m); ru = ru - pasa_bajos(ru, 14)
        g = ru * (np.sin(2 * np.pi * 2300 * tt) * 0.6 + np.sin(2 * np.pi * 3700 * tt) * 0.4 + 0.5) * np.exp(-tt * 9)
        g += 0.5 * np.roll(g, int(0.07 * SR)) * (tt > 0.07)
        i0 = int(t0 * SR); k = min(m, n - i0)
        if k > 0: a[i0:i0 + k] += g[:k] * vol
    tt0 = tc + bc["vd"] * 0.32
    while tt0 < tf + 0.5: cadena(tt0, 0.5); tt0 += rng.uniform(0.55, 0.85)
    for x_ in (tf + 1.1, tf + 1.75): cadena(x_, 0.38)
    for x_ in np.arange(to + 1.0, ts - 0.4, 1.3): cadena(x_, 0.22)
    tl = tc                                             # latidos que se aceleran
    while tl < ts:
        bpm = lerp(58, 150, (tl - tc) / (ts - tc)); vol = lerp(0.25, 0.75, (tl - tc) / (ts - tc))
        for off, v in ((0, 1.0), (0.16, 0.7)):
            m = int(0.22 * SR); tt = np.arange(m) / SR; i0 = int((tl + off) * SR); k = min(m, n - i0)
            if k > 0: a[i0:i0 + k] += np.sin(2 * np.pi * (62 - 60 * tt) * tt) * np.exp(-tt * 16) * vol * v
        tl += 60 / bpm
    m = int(1.5 * SR); tt = np.arange(m) / SR; i0 = int(ts * SR)          # golpe del susto
    g = rng.standard_normal(m) * np.exp(-tt * 5) * 0.9
    for f0 in (196, 207.6, 277.2, 293.7, 415.3): g += 0.35 * np.sign(np.sin(2 * np.pi * f0 * (1 - 0.25 * tt) * tt)) * np.exp(-tt * 2.2)
    g += 1.1 * np.sin(2 * np.pi * (70 - 30 * tt) * tt) * np.exp(-tt * 3)
    k = min(m, n - i0); a[i0:i0 + k] += g[:k] * 0.8
    m = int(3.5 * SR); tt = np.arange(m) / SR; i0 = int((tfin + 0.3) * SR); k = min(m, n - i0)   # campana final
    a[i0:i0 + k] += (np.sin(2 * np.pi * 110 * tt) + 0.5 * np.sin(2 * np.pi * 277 * tt) + 0.3 * np.sin(2 * np.pi * 415 * tt))[:k] * np.exp(-tt[:k] * 1.1) * 0.22
    for b in L.b:                                        # narrador (baja el fondo cuando habla)
        if not b["txt"]: continue
        i0 = int(b["ini"] * SR); k = min(len(b["x"]), n - i0); a[i0:i0 + k] *= 0.6; a[i0:i0 + k] += b["x"][:k] * 0.95
    a = np.tanh(a * 1.25) * 0.92
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((a * 32767).astype(np.int16).tobytes())

EPISODIOS = {"familiar": FAMILIAR}
if __name__ == "__main__":
    cual, out = sys.argv[1], sys.argv[2]; L = Linea(EPISODIOS[cual], cual); fn = lambda t: cuadro(L, t)
    if len(sys.argv) > 3:
        pts = [b["ini"] + min(b["vd"] * 0.85, b["fin"] - b["ini"] - 0.05) if b["txt"] else b["ini"] + 0.5 for b in L.b] + [L.ini("cierre") + 5.0]
        ims = [fn(s).resize((216, 384)) for s in pts]
        c = Image.new("RGB", (216 * len(ims), 384)); [c.paste(m, (i * 216, 0)) for i, m in enumerate(ims)]
        c.save("/tmp/prev_terror.jpg"); print("dur", round(L.dur, 1), [(b["clave"], round(b["ini"], 1)) for b in L.b]); sys.exit()
    sonido(L, "/tmp/_terror.wav"); N.render(fn, L.dur, out, "/tmp/_terror.wav")
