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
        im = susto(t, lt)
    return post(im, L, t)

def post(im, L, t):
    im = ImageChops.multiply(im, VIN); im = Image.blend(im, GRANO[int(t * 24) % 4], 0.055)
    if t < 0.4: im = Image.eval(im, lambda v: int(v * t / 0.4))
    if t > L.dur - 0.9: im = Image.eval(im, lambda v: int(v * max(0, (L.dur - t) / 0.9)))
    return im

def susto(t, lt):
    if lt < 0.07: return Image.new("RGB", (W, H), (255, 240, 235))
    if lt > 1.25: return Image.new("RGB", (W, H), (0, 0, 0))
    g = sm(lt / 0.32); pulso = 0.5 + 0.5 * math.sin(lt * 70)
    im = Image.new("RGB", (W, H), (int(70 + 60 * pulso), 0, 0)); d = ImageDraw.Draw(im)
    s = lerp(0.35, 1.5, g); jx, jy = random.Random(int(t * 30)).uniform(-26, 26), random.Random(int(t * 30) + 1).uniform(-26, 26)
    perro(d, W / 2 + jx, 760 + jy, s); return ojos(im, W / 2 + jx, 720 + jy, 1.0 + 1.6 * g, 1)

def ingenio(im, t, rojo=0.0, humo=True, apagado=False, luna=True):
    if luna: im = luz(im, LUNA, 800, 430)
    d = ImageDraw.Draw(im)
    if luna: d.ellipse([757, 387, 843, 473], fill=(206, 212, 228))
    d.rectangle([0, 1280, W, H], fill=(5, 6, 10))
    d.polygon([(120, 1290), (120, 1010), (330, 930), (540, 1010), (540, 1290)], fill=(4, 5, 9))
    d.polygon([(250, 1100), (268, 520), (332, 520), (350, 1100)], fill=(4, 5, 9))
    for j in range(3): d.rectangle([170 + j * 120, 1120, 220 + j * 120, 1190], fill=(12, 12, 16) if apagado else (int(lerp(70, 200, rojo)), int(lerp(55, 20, rojo)), int(lerp(20, 10, rojo))))
    for j in range(7 if humo else 0):
        ph = (t * 0.22 + j / 7) % 1; r = 40 + 120 * ph; xh = 300 + 90 * ph + 30 * math.sin(t + j); yh = 520 - 430 * ph
        g = int(lerp(46, 14, ph)); d.ellipse([xh - r, yh - r * 0.7, xh + r, yh + r * 0.7], fill=(int(g + 60 * rojo * (1 - ph)), g, g + 4))
    return im

def sendero(t, alba=False, luna=True):
    im = (CIELO_ALBA if alba else CIELO).copy()
    if luna and not alba: im = luz(im, LUNA.resize((360, 360)), 250, 330)
    d = ImageDraw.Draw(im); camino(d, alba); col = (3, 4, 8) if not alba else (18, 20, 26)
    canaveral(d, t, -1, col=col); canaveral(d, t, 1, col=col); return im

def bruma(im, t, alba=False, k=0.42):
    nb = NIEBLA[0].crop((int((t * 38) % W), 0, int((t * 38) % W) + W, 700))
    im.paste(Image.new("RGB", (W, 700), (60, 66, 84) if not alba else (120, 112, 112)), (0, SUELO - 380), Image.eval(nb, lambda v: int(v * k))); return im

# ------------------------------------------------------------------ parte 2
FAMILIAR2 = dict(
  titulo="El Familiar · Parte 2", ep=2, proximo="El pacto",
  beats=[
    ("frio",    "Tres días después... el farol seguía prendido.", 0.9),
    ("hermano", "Lo levantó Ramón, el hermano del peón. En el ingenio, nadie quiso hablar.", 0.5),
    ("viejo",   "Solo un viejo le dijo algo. No lo busqués de noche. Y si te llama... no le contestés.", 0.9),
    ("entra",   "Esa noche, Ramón entró al cañaveral. Con el farol de su hermano.", 0.5),
    ("voz",     "A mitad de camino, escuchó una voz. Era su hermano. Lo llamaba por su nombre.", 2.2),
    ("canas",   "Venía de adentro de las cañas.", 2.0),
    ("sigue",   "Ramón no contestó. Siguió caminando. Y la voz... lo siguió.", 0.9),
    ("galpon",  "Llegó al galpón viejo. La puerta estaba abierta. Adentro colgaba una cadena... con un collar.", 1.0),
    ("vacio",   "El collar estaba vacío.", 2.2),
    ("atras",   "Y atrás suyo, la voz dijo su nombre. Pero esta vez... no era la de su hermano.", 1.3),
    ("scare",   "", 1.7),
    ("final",   "A la mañana, en el camino, había dos faroles.", 1.2),
    ("cierre",  "Y desde la casa grande... el patrón miraba.", 2.8),
  ])

def cuadro2(L, t):
    ep = L.ep; b, lt = L.en(t); k = b["clave"]
    if k == "scare": return post(susto(t, lt), L, t)
    if k == "frio":                                   # arranque en frío: el farol del episodio 1
        im = sendero(t); d = ImageDraw.Draw(im)
        d.rectangle([520, SUELO + 40, 550, SUELO + 96], fill=(255, 190, 90))
        im = luz(im, GLOW[1 + int(t * 7) % 2].resize((560, 560)), 535, SUELO + 70); im = bruma(im, t)
        d = ImageDraw.Draw(im); a = sm(lt / 1.0)
        d.text((W / 2, 760), "PARTE 2", font=F(120), fill=(int(190 * a), 0, 0), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    elif k in ("hermano", "viejo"):
        im = ingenio(CIELO.copy(), t); d = ImageDraw.Draw(im)
        if k == "viejo":                              # fogón con dos siluetas
            fl = 1 + int(t * 9) % 2; im = luz(im, GLOW[fl].resize((700, 700)), 700, 1500); d = ImageDraw.Draw(im)
            d.polygon([(660, 1540), (700, 1440 - 20 * math.sin(t * 9)), (740, 1540)], fill=(255, 170, 60))
            for xs, alto_ in ((560, 1.0), (850, 0.86)):
                gy = 1560; h = 300 * alto_
                d.polygon([(xs - 50, gy), (xs + 50, gy), (xs + 36, gy - h), (xs - 36, gy - h)], fill=(2, 2, 4))
                d.ellipse([xs - 28, gy - h - 58, xs + 28, gy - h - 2], fill=(2, 2, 4)); d.ellipse([xs - 60, gy - h - 34, xs + 60, gy - h - 14], fill=(2, 2, 4))
        canaveral(d, t, -1, base=1700, alto=420); canaveral(d, t, 1, base=1700, alto=420)
    elif k in ("entra", "voz", "sigue"):
        im = sendero(t); d = ImageDraw.Draw(im); t0 = L.ini("entra")
        if k == "sigue": x = lerp(470, 600, lt / (b["fin"] - b["ini"])); anda = True
        else:
            x = lerp(250, 470, (t - t0) / (L.ini("voz") + 2.5 - t0)); anda = not (k == "voz" and lt > 2.5)
        fx, fy = peon(d, x, t, anda=anda)
        apaga = k == "voz" and lt > b["vd"] and random.Random(int(t * 12)).random() < 0.3
        im = luz(im, GLOW[0 if apaga else 1 + int(t * 9) % 2], fx, fy); im = bruma(im, t)
    elif k == "canas":                                # subjetiva: las cañas de cerca
        im = Image.new("RGB", (W, H), (4, 6, 12)); d = ImageDraw.Draw(im)
        abre = sm((lt - b["vd"]) / 1.6)
        for i, (u, h, ph, incl) in enumerate(CANAS):
            x0 = u * W; lado = -1 if x0 < W / 2 else 1; x0 += lado * 150 * abre * (1 - abs(x0 - W / 2) / (W / 2))
            sway = 50 * math.sin(t * 2.2 + ph) + 120 * incl
            d.line([(x0, H + 40), (x0 + sway * 0.4, H * 0.5), (x0 + sway, -40)], fill=(1, 2, 4) if i % 3 else (9, 12, 18), width=14 + i % 9)
        im = luz(im, GLOW[1 + int(t * 9) % 2].resize((1300, 1300)), W / 2, H + 120)
        im = ojos(im, W / 2, 900, 0.22, abre * 0.55 * (0 if (t % 1.9) < 0.1 else 1))
    elif k in ("galpon", "vacio", "atras"):           # interior del galpón
        im = Image.new("RGB", (W, H), (3, 3, 5)); d = ImageDraw.Draw(im)
        d.polygon([(330, 1500), (330, 560), (750, 560), (750, 1500)], fill=(46, 8, 6)); im = luz(im, Image.eval(GLOW[0], lambda v: int(v * 0.8)).resize((1300, 1300)), 540, 1000)
        d = ImageDraw.Draw(im); d.rectangle([0, 1500, W, H], fill=(8, 6, 7)); d.polygon([(330, 1500), (750, 1500), (980, H), (100, H)], fill=(34, 10, 8))
        quieta = k != "galpon"; amp = 0 if quieta else 70 * math.sin(t * 1.7)
        if k == "vacio": amp = 70 * math.sin(L.ini("vacio") * 1.7) * max(0, 1 - lt / 0.5)
        px, py = 540, 560
        for j in range(13):                            # cadena colgando
            qx, qy = 540 + amp * ((j + 1) / 13) ** 1.5, 560 + (j + 1) * 46
            d.line([(px, py), (qx, qy)], fill=(2, 2, 3), width=10); d.ellipse([qx - 13, qy - 13, qx + 13, qy + 13], outline=(2, 2, 3), width=7); px, py = qx, qy
        d.ellipse([px - 70, py, px + 70, py + 110], outline=(2, 2, 3), width=16)          # collar vacío
        if k == "atras":
            a = sm((lt - b["vd"] * 0.45) / 1.6); gy = 1700
            d.polygon([(420, gy), (660, gy), (630, gy - 520), (450, gy - 520)], fill=(0, 0, 0)); d.ellipse([490, gy - 640, 590, gy - 540], fill=(0, 0, 0)); d.ellipse([440, gy - 600, 640, gy - 566], fill=(0, 0, 0))
            im = ojos(im, 540, 420, 1.5 + 0.5 * a, a * 0.5)
    elif k == "final":
        im = sendero(t, alba=True); d = ImageDraw.Draw(im)
        for xl in (470, 610):
            d.rectangle([xl - 15, SUELO + 40, xl + 15, SUELO + 96], fill=(255, 190, 90)); im = luz(im, GLOW[1 + int(t * 7 + xl) % 2].resize((460, 460)), xl, SUELO + 70); d = ImageDraw.Draw(im)
        im = bruma(im, t, alba=True)
    else:                                             # cierre: la casa grande, una ventana roja
        im = ingenio(CIELO.copy(), t, rojo=sm(lt / 2.0)); d = ImageDraw.Draw(im)
        d.rectangle([398, 1108, 426, 1190], fill=(0, 0, 0)); d.ellipse([398, 1090, 426, 1118], fill=(0, 0, 0))     # silueta en la ventana
        canaveral(d, t, -1, base=1700, alto=420); canaveral(d, t, 1, base=1700, alto=420)
        if lt > b["vd"] + 0.3:
            a = sm((lt - b["vd"] - 0.3) / 0.8)
            d.text((W / 2, 1420), "EL FAMILIAR", font=F(104), fill=(int(200 * a), int(10 * a), int(10 * a)), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
            d.text((W / 2, 1520), f"Próximo episodio: {ep['proximo']}", font=F(44, False), fill=(int(220 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    d = ImageDraw.Draw(im)
    if k != "frio" or lt > 1.2: cabecera(d, ep)
    subtitulo(d, b, lt)
    return post(im, L, t)

# ------------------------------------------------------------------ sonido
def pasa_bajos(x, n): return np.convolve(x, np.ones(n) / n, "same")
def susurro(texto, clave, rate, vol):
    crudo = f"/tmp/_ts_{clave}_raw.wav"; out = f"/tmp/_ts_{clave}.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", Q.modelo_voz(), "-f", crudo, "--length-scale", "1.5"], input=texto.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sr = wave.open(crudo).getframerate()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", crudo, "-af", f"asetrate={int(sr*rate)},aresample={SR},highpass=f=300,lowpass=f=2600,aecho=0.9:0.8:180|360|620:0.6|0.4|0.25,volume={vol}", "-ac", "1", "-ar", str(SR), out], check=True)
    w = wave.open(out); return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768

def marcas1(L):
    tc = L.ini("cadenas"); bc = next(b for b in L.b if b["clave"] == "cadenas"); tf, to, ts = L.ini("frena"), L.ini("ojos"), L.ini("scare")
    rng = np.random.default_rng(13); cad = []; x = tc + bc["vd"] * 0.32
    while x < tf + 0.5: cad.append((x, 0.5)); x += rng.uniform(0.55, 0.85)
    cad += [(tf + 1.1, 0.38), (tf + 1.75, 0.38)] + [(x_, 0.22) for x_ in np.arange(to + 1.0, ts - 0.4, 1.3)]
    return dict(lat=tc, sil=[(tf, to)], susto=ts, campana=L.ini("final"), cadenas=cad, extra=[])

def marcas2(L):
    g = lambda c: next(b for b in L.b if b["clave"] == c)
    tv, tcn, tsg, tg, tva, ta, ts = (L.ini(c) for c in ("voz", "canas", "sigue", "galpon", "vacio", "atras", "scare"))
    cad = [(x, 0.3) for x in np.arange(tg + g("galpon")["vd"] * 0.6, tva, 0.8)] + [(ts - 0.5, 0.3)]
    extra = [(tv + g("voz")["vd"] + 0.4, susurro("Ramón...", "r1", 0.8, 0.9)), (tcn + g("canas")["vd"] + 0.3, susurro("Ramón... vení.", "r2", 0.78, 1.0)),
             (tsg + g("sigue")["vd"] * 0.75, susurro("Ramón...", "r3", 0.76, 0.7)), (ta + g("atras")["vd"] + 0.15, susurro("Ramón.", "r4", 0.5, 1.6))]
    return dict(lat=tv + g("voz")["vd"], sil=[(tcn + g("canas")["vd"] - 0.2, tsg), (tva, ta)], susto=ts, campana=L.ini("final"), cadenas=cad, extra=extra)

def sonido(L, path, M):
    n = int(L.dur * SR); t = np.arange(n) / SR; rng = np.random.default_rng(13); a = np.zeros(n)
    def env(t0, t1, fa=0.6): return np.clip((t - t0) / fa, 0, 1) * np.clip((t1 - t) / fa, 0, 1)
    ts, tfin = M["susto"], M["campana"]
    calla = np.ones(n)
    for (s0, s1) in M["sil"]: calla *= (1 - 0.92 * env(s0, s1, 0.4))
    drone = (np.sin(2 * np.pi * 55 * t) + 0.7 * np.sin(2 * np.pi * 58.3 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t + 2 * np.sin(2 * np.pi * 0.13 * t)))
    drone *= 0.085 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t)) * calla * (1 - env(ts + 1.2, tfin + 0.5, 0.3))
    viento = pasa_bajos(rng.standard_normal(n), 220) * 2.2 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t + 1)) * 0.16
    a += drone + viento * (0.4 + 0.6 * calla)
    for (t0, vol) in M["cadenas"]:
        m = int(0.42 * SR); tt = np.arange(m) / SR; ru = rng.standard_normal(m); ru = ru - pasa_bajos(ru, 14)
        g = ru * (np.sin(2 * np.pi * 2300 * tt) * 0.6 + np.sin(2 * np.pi * 3700 * tt) * 0.4 + 0.5) * np.exp(-tt * 9)
        g += 0.5 * np.roll(g, int(0.07 * SR)) * (tt > 0.07); i0 = int(t0 * SR); k = min(m, n - i0)
        if k > 0: a[i0:i0 + k] += g[:k] * vol
    tl = M["lat"]
    while tl < ts:
        bpm = lerp(58, 150, (tl - M["lat"]) / (ts - M["lat"])); vol = lerp(0.25, 0.75, (tl - M["lat"]) / (ts - M["lat"]))
        for off, v in ((0, 1.0), (0.16, 0.7)):
            m = int(0.22 * SR); tt = np.arange(m) / SR; i0 = int((tl + off) * SR); k = min(m, n - i0)
            if k > 0: a[i0:i0 + k] += np.sin(2 * np.pi * (62 - 60 * tt) * tt) * np.exp(-tt * 16) * vol * v
        tl += 60 / bpm
    m = int(1.5 * SR); tt = np.arange(m) / SR; i0 = int(ts * SR)
    g = rng.standard_normal(m) * np.exp(-tt * 5) * 0.9
    for f0 in (196, 207.6, 277.2, 293.7, 415.3): g += 0.35 * np.sign(np.sin(2 * np.pi * f0 * (1 - 0.25 * tt) * tt)) * np.exp(-tt * 2.2)
    g += 1.1 * np.sin(2 * np.pi * (70 - 30 * tt) * tt) * np.exp(-tt * 3)
    k = min(m, n - i0); a[i0:i0 + k] += g[:k] * 0.8
    m = int(3.5 * SR); tt = np.arange(m) / SR; i0 = int((tfin + 0.3) * SR); k = min(m, n - i0)
    a[i0:i0 + k] += (np.sin(2 * np.pi * 110 * tt) + 0.5 * np.sin(2 * np.pi * 277 * tt) + 0.3 * np.sin(2 * np.pi * 415 * tt))[:k] * np.exp(-tt[:k] * 1.1) * 0.22
    for (t0, x) in M["extra"]:
        i0 = int(t0 * SR); k = min(len(x), n - i0)
        if k > 0: a[i0:i0 + k] += x[:k]
    for b in L.b:
        if not b["txt"]: continue
        i0 = int(b["ini"] * SR); k = min(len(b["x"]), n - i0); a[i0:i0 + k] *= 0.6; a[i0:i0 + k] += b["x"][:k] * 0.95
    a = np.tanh(a * 1.25) * 0.92
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((a * 32767).astype(np.int16).tobytes())

# ------------------------------------------------------------------ parte 3
FAMILIAR3 = dict(
  titulo="El Familiar · Final", ep=3, proximo="El Lobizón",
  beats=[
    ("frio",   "Todos los años, la misma noche, el patrón deja una puerta abierta.", 0.9),
    ("origen", "Hace treinta años, el ingenio se moría. Una noche, alguien golpeó tres veces.", 1.7),
    ("trato",  "Era un hombre de negro, con un perro atado. Le ofreció cosechas eternas. A cambio de darle de comer... una vez al año.", 0.8),
    ("firma",  "El patrón firmó. Y esa misma noche, el perro quedó suelto.", 1.4),
    ("anios",  "Treinta años. Treinta peones. Treinta faroles.", 1.0),
    ("hoy",    "Pero este año pasó algo distinto. Ramón no contestó. Y el Familiar... volvió con hambre.", 0.9),
    ("casa",   "Esa noche, el patrón escuchó cadenas. Subiendo la escalera.", 1.8),
    ("puerta", "Cerró con llave. Las cadenas... se frenaron del otro lado.", 2.2),
    ("voz",    "Y una voz que él conocía le dijo: ya comí tu parte. Ahora vengo por la mía.", 1.3),
    ("scare",  "", 1.7),
    ("final",  "A la mañana, el ingenio amaneció apagado. Por primera vez en treinta años.", 1.2),
    ("cierre", "En el camino había un farol más. Y ese... nadie lo quiso levantar.", 3.0),
  ])

def cadena_colgada(d, amp):
    px, py = 540, 560
    for j in range(13):
        qx, qy = 540 + amp * ((j + 1) / 13) ** 1.5, 560 + (j + 1) * 46
        d.line([(px, py), (qx, qy)], fill=(2, 2, 3), width=10); d.ellipse([qx - 13, qy - 13, qx + 13, qy + 13], outline=(2, 2, 3), width=7); px, py = qx, qy
    d.ellipse([px - 70, py, px + 70, py + 110], outline=(2, 2, 3), width=16)

def vano(abierto=1.0):
    """Interior oscuro con una puerta al fondo; abierto 0..1 = cuánta luz roja entra."""
    im = Image.new("RGB", (W, H), (3, 3, 5)); d = ImageDraw.Draw(im)
    d.polygon([(330, 1500), (330, 560), (750, 560), (750, 1500)], fill=(int(8 + 38 * abierto), int(6 + 2 * abierto), 6))
    if abierto > 0.05: im = luz(im, Image.eval(GLOW[0], lambda v: int(v * 0.8 * abierto)).resize((1300, 1300)), 540, 1000)
    d = ImageDraw.Draw(im); d.rectangle([0, 1500, W, H], fill=(8, 6, 7))
    d.polygon([(330, 1500), (750, 1500), (980, H), (100, H)], fill=(int(8 + 26 * abierto), int(6 + 4 * abierto), 8)); return im

def cuadro3(L, t):
    ep = L.ep; b, lt = L.en(t); k = b["clave"]
    if k == "scare": return post(susto(t, lt), L, t)
    if k == "frio":
        im = ingenio(CIELO.copy(), t, rojo=1.0); d = ImageDraw.Draw(im)
        canaveral(d, t, -1, base=1700, alto=420); canaveral(d, t, 1, base=1700, alto=420); a = sm(lt / 1.0)
        d.text((W / 2, 300), "PARTE 3", font=F(110), fill=(int(190 * a), 0, 0), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((W / 2, 400), "EL PACTO", font=F(60, False), fill=(int(200 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    elif k == "origen":                                   # puerta cerrada; tres golpes la sacuden
        gol = [b["vd"] + 0.15, b["vd"] + 0.6, b["vd"] + 1.05]; sac = max([max(0, 1 - (lt - g) / 0.18) if lt >= g else 0 for g in gol])
        im = vano(0.06 + 0.5 * sac); d = ImageDraw.Draw(im)
        d.line([(540 + 8 * sac, 560), (540 + 8 * sac, 1500)], fill=(0, 0, 0), width=6); d.ellipse([690, 1010, 716, 1036], fill=(60, 50, 30))
    elif k == "trato":                                    # la puerta abierta: el hombre de negro y el perro
        ab = sm(lt / 1.2); im = vano(ab); d = ImageDraw.Draw(im); c = (0, 0, 0); gy = 1500
        d.polygon([(470, gy), (640, gy), (610, 760), (500, 760)], fill=c); d.ellipse([515, 650, 595, 760], fill=c); d.ellipse([455, 668, 655, 706], fill=c); d.rectangle([505, 610, 605, 690], fill=c)
        d.ellipse([650, 1290, 760, 1500], fill=c); d.ellipse([662, 1210, 748, 1310], fill=c)             # perro sentado
        for q in (-1, 1): d.polygon([(705 + q * 22, 1230), (705 + q * 52, 1150), (705 + q * 40, 1260)], fill=c)
        d.line([(610, 1040), (700, 1300)], fill=c, width=7)
        im = ojos(im, 705, 1258, 0.16, sm((lt - b["vd"] * 0.6) / 1.0))
    elif k == "firma":
        im = vano(1.0); d = ImageDraw.Draw(im); cadena_colgada(d, 90 * math.sin(t * 2.1) * max(0.25, 1 - lt / 6))
    elif k == "anios":                                    # una fila de faroles en el camino
        im = sendero(t); n_ = int(1 + 30 * sm(lt / max(0.1, b["vd"] + 0.6))); rr = random.Random(4)
        for j in range(min(30, n_)):
            f = j / 29; yy_ = lerp(H - 120, SUELO - 10, f ** 0.6); half = lerp(400, 90, f ** 0.6); xx_ = W / 2 + rr.uniform(-1, 1) * half; sc = lerp(1.0, 0.25, f ** 0.6)
            im = luz(im, GLOW[1 + (int(t * 6) + j) % 2].resize((int(300 * sc) + 20,) * 2), xx_, yy_)
            ImageDraw.Draw(im).rectangle([xx_ - 9 * sc, yy_ - 22 * sc, xx_ + 9 * sc, yy_ + 14 * sc], fill=(255, 200, 110))
        im = bruma(im, t, k=0.3)
    elif k == "hoy":
        im = sendero(t); a = sm(lt / 1.5); e = lerp(0.14, 0.62, sm((lt - b["vd"] * 0.55) / (b["vd"] * 0.6)))
        im = ojos(im, 540, SUELO - 130 + 40 * e, e, a); im = bruma(im, t)
    elif k == "casa":                                     # el cuarto del patrón: ventana con luna
        im = Image.new("RGB", (W, H), (4, 4, 8)); d = ImageDraw.Draw(im)
        d.rectangle([600, 520, 900, 1000], fill=(30, 40, 78)); im = luz(im, LUNA.resize((300, 300)), 800, 640); d = ImageDraw.Draw(im)
        d.line([(750, 520), (750, 1000)], fill=(4, 4, 8), width=12); d.line([(600, 760), (900, 760)], fill=(4, 4, 8), width=12)
        d.polygon([(600, 1560), (900, 1560), (1080, H), (520, H)], fill=(14, 18, 34))
        gy = 1640; c = (0, 0, 0); gira = sm((lt - b["vd"] * 0.5) / 0.6) * 40
        d.polygon([(250, gy), (450, gy), (420, gy - 540), (280, gy - 540)], fill=c); d.ellipse([300 - gira * 0.3, gy - 660, 400 - gira * 0.3, gy - 540], fill=c)
    elif k in ("puerta", "voz"):                          # la puerta desde adentro: luz roja por debajo
        im = Image.new("RGB", (W, H), (3, 3, 5)); d = ImageDraw.Draw(im)
        d.rectangle([330, 520, 750, 1500], fill=(12, 10, 10)); d.rectangle([330, 520, 750, 1500], outline=(0, 0, 0), width=10); d.ellipse([690, 1010, 716, 1036], fill=(70, 58, 34))
        a = sm(lt / 1.5) if k == "puerta" else 1.0; gr = 8 + (34 * sm((lt - b["vd"] * 0.5) / 1.5) if k == "voz" else 0)
        d.rectangle([336, 1500 - gr, 744, 1500], fill=(int(220 * a), int(18 * a), int(10 * a)))
        im = luz(im, Image.eval(GLOW[0], lambda v: int(v * 0.7 * a)).resize((1100, 500)), 540, 1520)
        if k == "voz": im = ojos(im, 540, 1500 - gr / 2, 0.11, sm((lt - b["vd"] * 0.7) / 0.8))
    elif k == "final":
        im = ingenio(CIELO_ALBA.copy(), t, humo=False, apagado=True, luna=False); d = ImageDraw.Draw(im)
        canaveral(d, t, -1, base=1700, alto=420, col=(18, 20, 26)); canaveral(d, t, 1, base=1700, alto=420, col=(18, 20, 26))
    else:
        im = sendero(t, alba=True); d = ImageDraw.Draw(im)
        d.rectangle([525, SUELO + 40, 555, SUELO + 96], fill=(255, 190, 90)); im = luz(im, GLOW[1 + int(t * 7) % 2].resize((480, 480)), 540, SUELO + 70); im = bruma(im, t, alba=True)
        d = ImageDraw.Draw(im)
        if lt > b["vd"] + 0.4:
            a = sm((lt - b["vd"] - 0.4) / 0.9)
            d.text((W / 2, 660), "FIN", font=F(170), fill=(int(200 * a), int(10 * a), int(10 * a)), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
            d.text((W / 2, 800), "de El Familiar", font=F(52), fill=(int(220 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
            d.text((W / 2, 900), f"Próxima historia: {ep['proximo']}", font=F(44, False), fill=(int(200 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    d = ImageDraw.Draw(im)
    if k != "frio": cabecera(d, ep)
    subtitulo(d, b, lt)
    return post(im, L, t)

def golpe():
    m = int(0.3 * SR); tt = np.arange(m) / SR
    return (np.sin(2 * np.pi * (95 - 80 * tt) * tt) * np.exp(-tt * 14) + 0.3 * np.random.default_rng(2).standard_normal(m) * np.exp(-tt * 60)) * 0.95

def marcas3(L):
    g = lambda c: next(b for b in L.b if b["clave"] == c)
    to, tfi, tca, tp, tv, ts = (L.ini(c) for c in ("origen", "firma", "casa", "puerta", "voz", "scare"))
    extra = [(to + g("origen")["vd"] + d_, golpe()) for d_ in (0.15, 0.6, 1.05)]
    extra += [(tp + g("puerta")["vd"] + 0.5, susurro("Abrime.", "p1", 0.5, 1.5)), (tv + g("voz")["vd"] + 0.1, susurro("Abrime.", "p2", 0.45, 1.8))]
    cad = [(tfi + g("firma")["vd"] * 0.7 + i * 0.5, 0.3) for i in range(3)]
    x = tca + g("casa")["vd"] * 0.35; v = 0.22
    while x < tp + g("puerta")["vd"] * 0.6: cad.append((x, v)); x += 0.6; v = min(0.6, v + 0.06)
    return dict(lat=tca, sil=[(tp + g("puerta")["vd"] * 0.7, tv)], susto=ts, campana=L.ini("final"), cadenas=cad, extra=extra)

# ------------------------------------------------------------------ episodios 4-6 (motor por escenas)
ORB = radial(520, (150, 255, 190), 2.4)

def G(titulo, ep, proximo, filas):
    """filas: (texto, pausa, escena, fx)."""
    return dict(titulo=titulo, ep=ep, proximo=proximo, beats=[(str(i), f[0], f[1]) for i, f in enumerate(filas)], esc=[f[2] for f in filas], fx=[f[3] for f in filas])

def campo(t, e, lt, dur):
    alba = e.get("alba", False); im = (CIELO_ALBA if alba else CIELO).copy(); f = sm(lt / max(0.1, dur))
    if not alba:
        tam = int(520 * e.get("luna", 1.0)); im = luz(im, LUNA.resize((tam, tam)), 760, 430); r = 43 * e.get("luna", 1.0)
        ImageDraw.Draw(im).ellipse([760 - r, 430 - r, 760 + r, 430 + r], fill=(214, 220, 234))
    d = ImageDraw.Draw(im); c = (4, 5, 9) if not alba else (20, 22, 28); d.rectangle([0, 1300, W, H], fill=(6, 7, 11) if not alba else (38, 36, 40))
    if e.get("arboles"):
        for xa, ha in ((150, 520), (420, 380), (930, 600)):
            d.rectangle([xa - 14, 1300 - ha * 0.5, xa + 14, 1300], fill=c)
            for j in range(5): d.ellipse([xa - 130 + j * 34 - 40, 1300 - ha - 60 + (j % 2) * 70, xa - 130 + j * 34 + 150, 1300 - ha * 0.45 + (j % 3) * 30], fill=c)
    if e.get("rancho"):
        d.rectangle([150, 1120, 470, 1300], fill=c); d.polygon([(120, 1130), (310, 990), (500, 1130)], fill=c)
        if e.get("vent"): d.rectangle([340, 1180, 410, 1250], fill=(230, 150, 60)); im = luz(im, GLOW[1 + int(t * 6) % 2].resize((420, 420)), 375, 1215); d = ImageDraw.Draw(im)
    if e.get("cruces"):
        d.ellipse([460, 1230, 1180, 1420], fill=c)
        for j, xc in enumerate((560, 660, 770, 880, 990)):
            h = 110 + (j * 37) % 60; yb = 1262 - (j % 2) * 12
            d.rectangle([xc - 7, yb - h, xc + 7, yb], fill=c); d.rectangle([xc - 34, yb - h * 0.72, xc + 34, yb - h * 0.72 + 13], fill=c)
    if "fig" in e:                                      # figura agachada que se levanta
        xf, h0, h1 = e["fig"]; h = lerp(h0, h1, sm((lt - dur * 0.35) / (dur * 0.5))); yb = 1290
        d.ellipse([xf - 50, yb - h, xf + 50, yb + 10], fill=(0, 0, 0)); d.ellipse([xf - 30, yb - h - 46, xf + 30, yb - h + 14], fill=(0, 0, 0))
        if h1 > 200:
            for q in (-1, 1): d.polygon([(xf + q * 12, yb - h - 30), (xf + q * 34, yb - h - 92 * sm((h - h0) / max(1, h1 - h0))), (xf + q * 30, yb - h - 14)], fill=(0, 0, 0))
    if "peon" in e:
        x0, x1 = e["peon"]; anda = x0 != x1; gy0 = globals()["SUELO"]; globals()["SUELO"] = 1420
        fx, fy = peon(d, lerp(x0, x1, lt / max(0.1, dur)), t, anda=anda); globals()["SUELO"] = gy0
        im = luz(im, GLOW[1 + int(t * 9) % 2].resize((640, 640)), fx, fy); d = ImageDraw.Draw(im)
    if "orb" in e:
        x0, y0, x1, y1, k0, k1 = e["orb"]; k = lerp(k0, k1, f) * (0.8 + 0.2 * math.sin(t * 9)); xo = lerp(x0, x1, f) + 14 * math.sin(t * 1.3); yo = lerp(y0, y1, f) + 10 * math.sin(t * 2.1)
        tam = max(20, int(520 * (0.3 + 0.7 * k))); o = Image.eval(ORB.resize((tam, tam)), lambda v: int(v * min(1, k * 1.3)))
        im = luz(im, o, xo, yo); im = luz(im, Image.eval(o.resize((tam, max(8, tam // 4))), lambda v: int(v * 0.4)), xo, 1330); d = ImageDraw.Draw(im)
        if k > 0.05: d.ellipse([xo - 9 * k - 4, yo - 9 * k - 4, xo + 9 * k + 4, yo + 9 * k + 4], fill=(235, 255, 240))
    if "ojos" in e:
        xo, yo, s0, s1 = e["ojos"]; im = ojos(im, xo, yo, lerp(s0, s1, f), sm(lt / 1.2) * (0 if (t % 2.3) < 0.09 else 1)); d = ImageDraw.Draw(im)
    canaveral(d, t, -1, base=1760, alto=300, col=c); canaveral(d, t, 1, base=1760, alto=300, col=c)
    return bruma(im, t, alba=alba, k=0.3) if e.get("bruma", True) else im

def cueva(t, e, lt, dur):
    z = lerp(e.get("c0", 0.4), e.get("c1", 0.4), sm(lt / max(0.1, dur))); im = CIELO.copy(); d = ImageDraw.Draw(im)
    d.polygon([(0, 1500), (0, 1000), (200, 760 - 200 * z), (540, 560 - 420 * z), (860, 800 - 200 * z), (W, 960), (W, 1500)], fill=(5, 5, 7)); d.rectangle([0, 1480, W, H], fill=(4, 4, 6))
    cx, cy, w, h = 540, 1480, 190 * z * 2.2, 330 * z * 2.2; fl = 1 + int(t * 9) % 2
    d.pieslice([cx - w, cy - h * 2, cx + w, cy], 180, 360, fill=(250, 130, 40)); d.rectangle([cx - w, cy - h, cx + w, cy], fill=(250, 130, 40))
    for j in range(4):                                  # sombras que bailan adentro
        xs = cx + (j - 1.5) * w * 0.42 + 14 * math.sin(t * 3 + j); hs = h * (0.9 + 0.25 * math.sin(t * 4.2 + j * 2))
        d.polygon([(xs - 18 * z, cy), (xs + 18 * z, cy), (xs + 10 * z + 20 * z * math.sin(t * 5 + j), cy - hs)], fill=(40, 12, 4))
    im = luz(im, GLOW[fl].resize((int(900 * z + 300),) * 2), cx, cy - h * 0.6); d = ImageDraw.Draw(im)
    if "peon" in e:
        gy0 = globals()["SUELO"]; globals()["SUELO"] = 1620; peon(d, lerp(e["peon"][0], e["peon"][1], lt / max(0.1, dur)), t, anda=e["peon"][0] != e["peon"][1]); globals()["SUELO"] = gy0
    canaveral(d, t, -1, base=1800, alto=260); canaveral(d, t, 1, base=1800, alto=260); return im

def cuadroG(L, t):
    ep = L.ep; b, lt = L.en(t); i = L.b.index(b); e = ep["esc"][i]; dur = b["fin"] - b["ini"]; tipo = e["t"]
    if tipo == "susto": return post(susto(t, lt), L, t)
    if tipo == "texto":
        im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im); a = sm(lt / 0.5) * (0.82 + 0.18 * math.sin(t * 31))
        d.text((W / 2, 820), e["l1"], font=F(130), fill=(int(190 * a), 0, 0), anchor="mm"); d.text((W / 2, 1000), e["l2"], font=F(150), fill=(int(210 * a), 0, 0), anchor="mm")
        im = ojos(im, W / 2, 1330, 0.5, sm((lt - 1.2) / 1.5) * (0 if (t % 2.7) < 0.12 else 1))
    elif tipo == "campo": im = campo(t, e, lt, dur)
    elif tipo == "cueva": im = cueva(t, e, lt, dur)
    elif tipo == "sendero":
        im = sendero(t, alba=e.get("alba", False)); d = ImageDraw.Draw(im)
        if "peon" in e:
            x0, x1 = e["peon"]; fx, fy = peon(d, lerp(x0, x1, lt / max(0.1, dur)), t, anda=x0 != x1); im = luz(im, GLOW[1 + int(t * 9) % 2], fx, fy)
        if "orb" in e:
            x0, y0, x1, y1, k0, k1 = e["orb"]; f = sm(lt / max(0.1, dur)); k = lerp(k0, k1, f) * (0.8 + 0.2 * math.sin(t * 9)); tam = max(20, int(520 * (0.3 + 0.7 * k)))
            im = luz(im, Image.eval(ORB.resize((tam, tam)), lambda v: int(v * min(1, k * 1.3))), lerp(x0, x1, f), lerp(y0, y1, f))
        if "ojos" in e:
            xo, yo, s0, s1 = e["ojos"]; im = ojos(im, xo, yo, lerp(s0, s1, sm(lt / dur)), sm(lt / 1.2))
        im = bruma(im, t, alba=e.get("alba", False))
    elif tipo == "vano":
        im = vano(e.get("ab", 1.0)); d = ImageDraw.Draw(im)
        if e.get("sombras"):
            for j in range(3):
                xs = 420 + j * 120 + 16 * math.sin(t * 3 + j); hs = 520 + 130 * math.sin(t * 4.2 + j * 2)
                d.polygon([(xs - 24, 1500), (xs + 24, 1500), (xs + 30 * math.sin(t * 5 + j), 1500 - hs)], fill=(18, 4, 3))
        if e.get("fig"):
            gy = 1700; d.polygon([(420, gy), (660, gy), (630, gy - 520), (450, gy - 520)], fill=(0, 0, 0)); d.ellipse([490, gy - 640, 590, gy - 540], fill=(0, 0, 0)); d.ellipse([440, gy - 600, 640, gy - 566], fill=(0, 0, 0))
        if "ojos" in e:
            xo, yo, s0, s1 = e["ojos"]; a = sm((lt - b["vd"] * 0.45) / 1.6); im = ojos(im, xo, yo, lerp(s0, s1, a), a * 0.55)
    else:                                               # negro
        im = Image.new("RGB", (W, H), (2, 2, 4))
        if "ojos" in e: xo, yo, s0, s1 = e["ojos"]; im = ojos(im, xo, yo, lerp(s0, s1, sm(lt / dur)), sm((lt - b["vd"] * 0.6) / 1.0) * 0.6)
    d = ImageDraw.Draw(im)
    if tipo != "texto": cabecera(d, ep)
    if "card" in e and lt > b["vd"] + 0.4:
        a = sm((lt - b["vd"] - 0.4) / 0.9); l1, l2, l3 = e["card"]
        d.text((W / 2, 660), l1, font=F(120 if len(l1) < 8 else 84), fill=(int(200 * a), int(10 * a), int(10 * a)), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
        d.text((W / 2, 800), l2, font=F(50), fill=(int(220 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((W / 2, 890), l3, font=F(42, False), fill=(int(200 * a),) * 3, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    subtitulo(d, b, lt)
    return post(im, L, t)

def fx_aullido(vol=0.5):
    m = int(2.6 * SR); tt = np.arange(m) / SR; f = 300 + 230 * np.sin(np.pi * np.clip(tt / 2.6, 0, 1)) ** 0.7 + 6 * np.sin(2 * np.pi * 5.5 * tt)
    ph = 2 * np.pi * np.cumsum(f) / SR; x = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)
    return x * np.sin(np.pi * tt / 2.6) ** 0.8 * vol * 0.4
def fx_musica(vol=0.2):
    out = []
    for f0, du in ((293.7, 0.7), (349.2, 0.7), (277.2, 0.9), (415.3, 0.5), (392.0, 0.5), (293.7, 1.3)):
        m = int(du * SR); tt = np.arange(m) / SR; ph = 2 * np.pi * f0 * tt + 0.25 * np.sin(2 * np.pi * 6 * tt)
        out.append(pasa_bajos(2 * ((ph / (2 * np.pi)) % 1) - 1, 9) * np.minimum(1, tt / 0.06) * np.exp(-tt * 0.8))
    return np.concatenate(out) * vol
def fx_tono(vol=0.1):
    m = int(3.2 * SR); tt = np.arange(m) / SR
    return (np.sin(2 * np.pi * 1244 * tt) + np.sin(2 * np.pi * 1251 * tt) + 0.5 * np.sin(2 * np.pi * 1866 * tt)) * np.sin(np.pi * tt / 3.2) ** 2 * vol

def marcasG(L):
    ep = L.ep; M = dict(lat=None, sil=[], susto=None, campana=None, cadenas=[], extra=[])
    for i, b in enumerate(L.b):
        fx = ep["fx"][i]; fin = b["ini"] + b["vd"]
        if ep["esc"][i]["t"] == "susto": M["susto"] = b["ini"]; M["campana"] = b["fin"]
        if fx.get("lat") and M["lat"] is None: M["lat"] = b["ini"]
        if fx.get("sil"): M["sil"].append((fin - 0.2, b["fin"]))
        for kind in fx.get("sfx", []):
            if kind == "cadena": M["cadenas"] += [(fin + 0.2 + j * 0.6, 0.35) for j in range(2)]
            elif kind == "golpe": M["extra"] += [(fin + 0.15 + j * 0.45, golpe()) for j in range(3)]
            elif kind == "aullido": M["extra"].append((fin + 0.1, fx_aullido()))
            elif kind == "aullido_lejos": M["extra"].append((b["ini"] + b["vd"] * 0.5, fx_aullido(0.22)))
            elif kind == "musica": M["extra"].append((b["ini"] + 0.3, fx_musica()))
            elif kind == "tono": M["extra"].append((b["ini"] + 0.2, fx_tono()))
        if "sus" in fx: tx, rate, vol = fx["sus"]; M["extra"].append((fin + 0.3, susurro(tx, f"g{ep['ep']}_{i}", rate, vol)))
    if M["lat"] is None: M["lat"] = M["susto"] - 8
    return M

LOBIZON = G("El Lobizón", 4, "La Salamanca", [
 ("Si un viernes de luna llena te golpean la puerta... no abras.", 0.7, dict(t="texto", l1="NO ABRAS", l2="LA PUERTA"), dict(sfx=["golpe"])),
 ("En el campo dicen que el séptimo hijo varón nace marcado.", 0.6, dict(t="campo", rancho=True, luna=1.5), dict(sfx=["aullido_lejos"])),
 ("Los Ferreyra tuvieron siete. Al último lo llamaron Benito. Era el más callado.", 0.6, dict(t="campo", rancho=True, vent=True, luna=1.5), {}),
 ("Cada luna llena, Benito salía solo. Decía que iba a caminar. Siempre para el lado del cementerio.", 0.7, dict(t="campo", cruces=True, luna=1.5, fig=(770, 70, 70)), {}),
 ("Una noche, su hermano mayor lo siguió. Con un farol... y un cuchillo.", 0.6, dict(t="sendero", peon=(250, 520)), dict(lat=True)),
 ("Lo encontró entre las tumbas. De rodillas. De espaldas.", 2.0, dict(t="campo", cruces=True, luna=1.5, fig=(770, 70, 70), peon=(210, 210)), dict(sil=True, sfx=["aullido"])),
 ("Lo llamó por su nombre. Benito se dio vuelta. Y ya no era Benito.", 1.2, dict(t="campo", cruces=True, luna=1.5, fig=(770, 70, 330), peon=(210, 210), ojos=(770, 950, 0.1, 0.2)), dict(sil=True)),
 ("", 1.7, dict(t="susto"), {}),
 ("A la mañana, Benito desayunó con la familia. Como siempre. En la mesa... sobraba un lugar.", 1.0, dict(t="campo", rancho=True, vent=True, alba=True), {}),
 ("Dicen que todavía vive en el pueblo. Y que saluda a todos.", 3.0, dict(t="campo", cruces=True, luna=1.5, ojos=(770, 1180, 0.14, 0.18), card=("EL LOBIZÓN", "Episodio 4", "Próxima historia: La Salamanca")), dict(sfx=["aullido_lejos"])),
])
SALAMANCA = G("La Salamanca", 5, "La Luz Mala", [
 ("Hay una cueva donde te enseñan cualquier cosa. El precio... lo ponés vos.", 0.7, dict(t="texto", l1="¿QUÉ DARÍAS", l2="A CAMBIO?"), {}),
 ("Santiago del Estero. Monte adentro. Una cueva que no figura en ningún mapa.", 0.6, dict(t="campo", arboles=True, luna=0.8), {}),
 ("De noche, desde adentro, se escucha música. Guitarras. Violines. Risas.", 0.8, dict(t="cueva", c0=0.28, c1=0.36), dict(sfx=["musica"])),
 ("Anselmo era el peor guitarrero del pago. Y estaba cansado de que se rieran.", 0.6, dict(t="sendero", peon=(250, 500)), {}),
 ("Encontró la entrada un martes. Adentro había que pasar tres pruebas. Sin mirar atrás.", 0.7, dict(t="cueva", c0=0.4, c1=0.85, peon=(380, 470)), dict(sfx=["musica"], lat=True)),
 ("Pasó la primera. Pasó la segunda. En la tercera... alguien le tocó el hombro.", 2.0, dict(t="vano", ab=1.0, sombras=True, fig=True), dict(sil=True)),
 ("No se dio vuelta. Y una voz le dijo: bien. Ahora, tocá.", 1.2, dict(t="vano", ab=1.0, fig=True, ojos=(540, 420, 1.2, 1.7)), dict(sus=("Tocá.", 0.5, 1.5))),
 ("Volvió al pueblo tocando como nadie. La gente lloraba al escucharlo.", 0.7, dict(t="campo", rancho=True, vent=True, luna=0.8), dict(sfx=["musica"])),
 ("Pero desde esa noche, Anselmo no tiene sombra. Y cuando toca solo... alguien más aplaude.", 1.8, dict(t="negro", ojos=(540, 900, 0.3, 0.9)), dict(sil=True)),
 ("", 1.7, dict(t="susto"), {}),
 ("La cueva sigue ahí. Y siempre hay lugar para uno más.", 3.0, dict(t="cueva", c0=0.5, c1=0.62, card=("LA SALAMANCA", "Episodio 5", "Próxima historia: La Luz Mala")), dict(sfx=["musica"])),
])
LUZMALA = G("La Luz Mala", 6, "Temporada 2", [
 ("Si en el campo ves una luz que flota... no la sigas.", 0.7, dict(t="texto", l1="NO LA", l2="SIGAS"), dict(sfx=["tono"])),
 ("Pampa abierta. Ni un árbol. Ni un rancho. Solo el camino.", 0.6, dict(t="campo", luna=0.7), {}),
 ("Los viejos dicen que es un alma en pena. Que cuida algo enterrado.", 0.8, dict(t="campo", luna=0.7, orb=(820, 1150, 760, 1120, 0.12, 0.2)), dict(sfx=["tono"])),
 ("Un arriero la vio una noche. Chiquita. Lejos. Como un farol olvidado.", 0.6, dict(t="sendero", peon=(250, 430), orb=(560, 1330, 570, 1320, 0.1, 0.14)), {}),
 ("Caminó hacia ella. La luz retrocedió. Siempre a la misma distancia.", 0.9, dict(t="campo", luna=0.7, peon=(200, 420), orb=(700, 1120, 900, 1080, 0.3, 0.22)), dict(sfx=["tono"], lat=True)),
 ("Cuando quiso volver... el camino ya no estaba.", 2.0, dict(t="campo", luna=0.7, peon=(430, 430), orb=(900, 1080, 880, 1060, 0.22, 0.5), bruma=True), dict(sil=True)),
 ("La luz se apagó. Y en la oscuridad sintió una mano fría... que le agarraba la suya.", 1.4, dict(t="negro"), dict(sil=True, sus=("Vení.", 0.5, 1.5))),
 ("", 1.7, dict(t="susto"), {}),
 ("Lo encontraron al amanecer. Vivo. Escarbando la tierra con las uñas. Nunca dijo qué buscaba.", 1.0, dict(t="campo", alba=True, fig=(600, 80, 80)), {}),
 ("Argentina está llena de luces así. Si ves una... ya sabés.", 3.2, dict(t="campo", luna=0.7, orb=(540, 1100, 540, 1040, 0.3, 0.75), card=("FIN", "Temporada 1", "Argentina inexplicable")), dict(sfx=["tono"])),
])

EPISODIOS = {"familiar": (FAMILIAR, cuadro, marcas1), "familiar2": (FAMILIAR2, cuadro2, marcas2), "familiar3": (FAMILIAR3, cuadro3, marcas3), "lobizon": (LOBIZON, cuadroG, marcasG), "salamanca": (SALAMANCA, cuadroG, marcasG), "luzmala": (LUZMALA, cuadroG, marcasG)}
if __name__ == "__main__":
    cual, out = sys.argv[1], sys.argv[2]; ep, cq, mk = EPISODIOS[cual]; L = Linea(ep, cual); fn = lambda t: cq(L, t)
    if len(sys.argv) > 3:
        pts = [b["ini"] + min(b["vd"] + 0.6, b["fin"] - b["ini"] - 0.05) if b["txt"] else b["ini"] + 0.5 for b in L.b] + [L.dur - 1.6]
        ims = [fn(s).resize((180, 320)) for s in pts]
        c = Image.new("RGB", (180 * len(ims), 320)); [c.paste(m, (i * 180, 0)) for i, m in enumerate(ims)]
        c.save("/tmp/prev_terror.jpg"); print("dur", round(L.dur, 1), [(b["clave"], round(b["ini"], 1)) for b in L.b]); sys.exit()
    sonido(L, "/tmp/_terror.wav", mk(L)); N.render(fn, L.dur, out, "/tmp/_terror.wav")
