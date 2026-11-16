"""Cuentos entre mascotas con narrador (voz) y avatares que actúan.
Uso: python3 cuentos.py pelota salida.mp4 [preview]

Estilo: fondo blanco limpio, poses claras, pausas, narrador que le habla al chico.
Voz: Piper TTS, modelo es-carlfm (dominio público), se baja solo de GitHub.
"""
import math, os, subprocess, sys, tarfile, urllib.request, wave
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nichos as N
from nichos import W, H, FPS, INK, F, text_c, ease_back, paste_emoji, CORAL, VIOLETA

BASE = 1480                       # línea de los pies
CACHE = os.path.expanduser("~/.cache/shorts_voz")
VOZ_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz"
_spr = {}

# ---------- voz ----------
def modelo_voz():
    m = os.path.join(CACHE, "es-carlfm-x-low.onnx")
    if not os.path.exists(m):
        os.makedirs(CACHE, exist_ok=True)
        tgz = os.path.join(CACHE, "v.tgz")
        urllib.request.urlretrieve(VOZ_URL, tgz)
        tarfile.open(tgz).extractall(CACHE)
    return m

def decir(texto, clave):
    out = os.path.join(CACHE, f"{clave}.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", modelo_voz(), "-f", out, "--length-scale", "1.12"],
                   input=texto.encode(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    w = wave.open(out); n = w.getnframes(); sr = w.getframerate()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    return x, sr, n / sr

# ---------- actores ----------
def sprite(char, nombre):
    k = (char, nombre)
    if k not in _spr: _spr[k] = Image.open(os.path.join(N.MASC_DIR, f"{char}_{nombre}.png")).convert("RGBA")
    return _spr[k]

def actor(im, d, char, x, t, spr, size=380, dy=0, sy=1.0, ang=0, flip=False, y=BASE):
    """Dibuja apoyado en los pies; sy<1 = aplastado, sy>1 = estirado."""
    if (t % 3.4) < 0.12 and spr in ("alentando", "act_izq", "act_der", "act_arriba"): spr = "alentando_blink" if spr == "alentando" else spr
    w = size * (2 - sy) if sy != 1 else size; h = size * sy
    sw = size * 0.34 * max(0.5, 1 - dy / 320)
    d.ellipse([x - sw, y - 12, x + sw, y + 22], fill=(224, 229, 238))
    m = sprite(char, spr).resize((max(4, int(w)), max(4, int(h))), Image.LANCZOS)
    if flip: m = m.transpose(Image.FLIP_LEFT_RIGHT)
    if ang: m = m.rotate(ang, resample=Image.BICUBIC, expand=True)
    im.paste(m, (int(x - m.width / 2), int(y - dy - h * 0.925 - (m.height - h) / 2)), m)

def salto(lt, T=0.9, alto=150):
    """Salto con anticipación: se agacha, sale estirado, cae y rebota. -> (dy, sy)"""
    k = (lt % T) / T
    if k < 0.2: return 0, 1 - 0.16 * math.sin(k / 0.2 * math.pi / 2)
    if k < 0.75:
        a = (k - 0.2) / 0.55
        return alto * math.sin(a * math.pi), 1 + 0.10 * math.cos(a * math.pi)
    b = (k - 0.75) / 0.25
    return 0, 1 - 0.14 * math.sin(b * math.pi)

def habla(t, mira="c"):
    ab = int(t * 6.5) % 2 == 0
    if mira == "c": return "act_habla_c" if ab else "alentando"
    return f"act_{mira}_h" if ab else f"act_{mira}"

def camina(t): return abs(math.sin(t * 9)) * 30, 1 + 0.04 * math.sin(t * 18), 6 * math.sin(t * 9)
def sm(k): k = max(0, min(1, k)); return k * k * (3 - 2 * k)
def lerp(a, b, k): return a + (b - a) * sm(k)

def narrador(d, txt, lt):
    f = F(62); words = txt.split(); lines = []; cur = ""
    for w_ in words:
        if f.getlength((cur + " " + w_).strip()) <= 940: cur = (cur + " " + w_).strip()
        else: lines.append(cur); cur = w_
    lines.append(cur)
    k = ease_back(lt / 0.3)
    for i, l in enumerate(lines):
        text_c(d, (W / 2, 210 + i * 84), l, 62, CORAL, (255, 255, 255), 9, scale=k)

def globo_idea(im, d, x, y, em, lt):
    k = ease_back(lt / 0.3)
    if k <= 0.02: return
    r = 105 * k
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=INK, width=7)
    d.ellipse([x - 62 * k, y + 100 * k, x - 22 * k, y + 140 * k], fill=(255, 255, 255), outline=INK, width=6)
    paste_emoji(im, em, x - 28 * k, y, 105, k)
    text_c(d, (x + 58 * k, y), "?", 110, CORAL, (255, 255, 255), 4, scale=k)

# ---------- cuento: la pelota perdida ----------
PELOTA = [
    ("a", "El Oso quiere jugar. Pero, ¿dónde está su pelota?", 0.6),
    ("b", "¡Mirá! Llegó la Rana. Rana, ¿viste la pelota del Oso?", 1.5),
    ("c", "No, no la vio. ¡Pero lo va a ayudar a buscar!", 0.5),
    ("d", "Buscan por acá, y buscan por allá.", 0.8),
    ("e", "¡Ey! El Gato vio algo.", 0.8),
    ("f", "¿Y vos? ¿Sabés dónde está la pelota?", 3.4),
    ("g", "¡Sí! ¡Atrás del arbusto! La tenía el Monstruito.", 0.8),
    ("h", "¿Y ahora? ¡A jugar todos juntos!", 4.0),
    ("i", "Jugar con amigos es mucho más divertido. ¡Chau, chau!", 1.6),
]

class Cuento:
    def __init__(self, guion, nombre):
        self.guion = guion; self.voz = []; t = 0.5; self.ini = []
        for clave, txt, extra in guion:
            x, sr, dur = decir(txt, f"{nombre}_{clave}")
            self.voz.append((x, sr, dur)); self.ini.append(t); t += dur + 0.45 + extra
        self.dur = t + 0.6

    def escena(self, t):
        i = 0
        for j, s in enumerate(self.ini):
            if t >= s: i = j
        return i, t - self.ini[i], self.voz[i][2]

def pelota_frame(C, t):
    im = Image.new("RGB", (W, H), (251, 252, 254)); d = ImageDraw.Draw(im)
    d.ellipse([-300, BASE - 70, W + 300, BASE + 1100], fill=(241, 245, 251))
    i, lt, vd = C.escena(t)
    clave, txt, extra = C.guion[i]
    if t >= C.ini[0]: narrador(d, txt, lt)
    hablando = lt < vd
    if clave == "a":
        k = lt / 1.6; x = lerp(-220, W / 2, k)
        if k < 1: dy, sy, ang = camina(t); actor(im, d, "oso", x, t, "act_der", 460, dy, sy, ang)
        elif lt < vd * 0.62: actor(im, d, "oso", x, t, "act_izq" if int(lt * 1.6) % 2 else "act_der", 460)
        else:
            actor(im, d, "oso", x, t, "act_triste", 460, sy=0.96)
            globo_idea(im, d, x + 230, BASE - 620, "⚽", lt - vd * 0.62)
    elif clave == "b":
        ox = lerp(W / 2, 320, lt / 0.8)
        k = min(1, lt / 1.5); rx = lerp(W + 220, 770, k)
        actor(im, d, "oso", ox, t, ("act_saluda1" if int(t * 5) % 2 else "act_saluda2") if 1.0 < lt < 2.6 else "act_der", 420)
        if k < 1: dy, sy = salto(lt, 0.5, 120); actor(im, d, "rana", rx, t, "act_izq", 400, dy, sy)
        elif lt < vd: actor(im, d, "rana", rx, t, "act_izq", 400)
        else:  # dice que no con la cabeza
            sh = 26 * math.sin((lt - vd) * 14)
            actor(im, d, "rana", rx + sh, t, "act_izq" if sh < 0 else "act_der", 400)
    elif clave == "c":
        dy, sy = salto(lt - 1.2, 0.8, 110) if lt > 1.2 else (0, 1)
        actor(im, d, "oso", 320, t, "festejando" if lt > 1.2 else "act_der", 420, dy * 0.7, sy)
        actor(im, d, "rana", 770, t, "act_sorpresa" if lt > 1.2 else "act_izq", 400, dy, sy)
    elif clave == "d":
        for j in range(5):  # el piso se mueve: flores y piedritas
            fx = (W + 300 - ((t * 260 + j * 330) % (W + 500)))
            paste_emoji(im, "🌼" if j % 2 else "🌱", fx, BASE + 60 + (j % 3) * 60, 90, 1)
        mirar = "act_der" if lt < vd * 0.5 else "act_izq"
        dy, sy, ang = camina(t)
        actor(im, d, "oso", 330, t, mirar, 400, dy, sy, ang)
        dy2, sy2 = salto(lt + 0.2, 0.55, 90)
        actor(im, d, "rana", 700, t, mirar, 380, dy2, sy2)
    elif clave == "e":
        gx = lerp(W + 240, 830, lt / 1.0)
        actor(im, d, "oso", 230, t, "act_der", 360)
        actor(im, d, "rana", 500, t, "act_sorpresa" if 0.8 < lt < 1.6 else "act_der", 340)
        if lt < 1.0: dy, sy, ang = camina(t); actor(im, d, "gato", gx, t, "act_izq", 380, dy, sy, ang)
        else: actor(im, d, "gato", gx, t, "pose_profe", 400, dy=abs(math.sin(t * 6)) * 14)
    elif clave in ("f", "g"):
        aparecio = clave == "g"
        if not aparecio:
            paste_emoji(im, "⚽", 965 + 12 * math.sin(t * 5), BASE - 55, 120, 1)
        else:
            dy = 120 + 330 * ease_back(lt / 0.5) + (10 * math.sin(t * 5) if lt > 0.6 else 0)
            sy = 1.1 if lt < 0.35 else 1
            actor(im, d, "monstruo", 720, t, "act_sorpresa" if lt < 1.6 else "festejando", 400, dy, sy)
            paste_emoji(im, "⚽", 950, BASE - 800 - abs(math.sin(t * 6)) * 45, 140, ease_back((lt - 0.5) / 0.3))
        paste_emoji(im, "🌳", 720, BASE - 250, 560, 1)
        est = "act_sorpresa" if (aparecio and lt < 1.4) else ("festejando" if aparecio else "act_der")
        for j, (c_, x_) in enumerate((("oso", 110), ("rana", 270), ("gato", 430))):
            dy, sy = salto(lt + j * 0.15, 0.8, 90) if (aparecio and lt > 1.4) else (0, 1)
            if not aparecio and not hablando and int((lt - vd) * 2 + j) % 3 == 0: e = "act_arriba"
            else: e = est
            actor(im, d, c_, x_, t, e, 230, dy, sy)
        if not aparecio and not hablando:
            p = lt - vd; c = max(1, 3 - int(p)); ph = p % 1
            r = 100 * ease_back(min(1, ph / 0.3))
            d.ellipse([W / 2 - r, 640 - r, W / 2 + r, 640 + r], fill=(255, 255, 255), outline=INK, width=8)
            text_c(d, (W / 2, 640), str(c), 130, (229, 57, 53), (255, 255, 255), 4, scale=ease_back(min(1, ph / 0.3)))
    elif clave == "h":
        xs = [150, 410, 670, 930]; chars = ["oso", "rana", "gato", "monstruo"]
        if lt < 1.2: bx, by, rec = 930, BASE - 520, -1
        else:
            p = (lt - 1.2) / 0.75; seq = [3, 2, 1, 0, 1, 2, 3, 2, 1, 0]
            ii = min(int(p), len(seq) - 2); f = p - ii if ii < len(seq) - 2 else 1
            a, b = xs[seq[ii]], xs[seq[ii + 1]]
            bx = a + (b - a) * f; by = BASE - 430 - 380 * math.sin(math.pi * f); rec = seq[ii + 1] if f > 0.75 else (seq[ii] if f < 0.2 else -1)
        for j, (c_, x_) in enumerate(zip(chars, xs)):
            if j == rec: dy, sy = 70, 1.06; e = "act_sorpresa"
            else:
                dy, sy = 0, 1 + 0.02 * math.sin(t * 5 + j)
                e = "act_arriba" if abs(bx - x_) < 160 else ("act_izq" if bx < x_ else "act_der")
            actor(im, d, c_, x_, t, e, 290, dy, sy)
        paste_emoji(im, "⚽", bx, by, 140, 1)
    else:  # i
        for j, (c_, x_) in enumerate(zip(["oso", "rana", "gato", "monstruo"], [150, 410, 670, 930])):
            if lt < vd * 0.55: dy, sy = salto(lt + j * 0.2, 0.8, 100); e = "festejando"
            else: dy, sy = 0, 1; e = "act_saluda1" if int(t * 5 + j) % 2 else "act_saluda2"
            actor(im, d, c_, x_, t, e, 290, dy, sy)
        if lt > vd: text_c(d, (W / 2, 1760), "Mañana, otra aventura", 66, INK, (255, 255, 255), 4, scale=ease_back((lt - vd) / 0.4))
    if t < 0.4: im = Image.blend(Image.new("RGB", (W, H), (255, 255, 255)), im, t / 0.4)
    return im

def mezclar_audio(C, path, seed=71):
    base = "/tmp/_cuento_musica.wav"
    chimes = [s for s in C.ini]
    N.audio(base, C.dur, [], chimes, [], bpm=100, seed=seed)
    w = wave.open(base); sr = w.getframerate(); n = w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768 * 0.30
    for (x, vsr, dur), s in zip(C.voz, C.ini):
        m = int(len(x) * sr / vsr)
        y = np.interp(np.linspace(0, len(x) - 1, m), np.arange(len(x)), x)
        i0 = int(s * sr); m = min(m, n - i0)
        a[i0:i0 + m] *= 0.45            # baja la música mientras habla el narrador
        a[i0:i0 + m] += y[:m] * 1.25
    a = np.tanh(a * 1.1) * 0.9
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    cual, out = sys.argv[1], sys.argv[2]
    C = Cuento(PELOTA, "pelota")
    fn = lambda t: pelota_frame(C, t)
    if len(sys.argv) > 3 and sys.argv[3] == "preview":
        pts = [C.ini[k] + C.voz[k][2] * 0.8 for k in range(len(C.ini))] + [C.ini[5] + C.voz[5][2] + 1.5, C.ini[7] + 3.0]
        ims = [fn(s).resize((216, 384)) for s in sorted(pts)]
        c = Image.new("RGB", (216 * len(ims), 384)); [c.paste(m, (k * 216, 0)) for k, m in enumerate(ims)]
        c.save("preview_cuento.jpg"); print("dur", round(C.dur, 1), [round(v[2], 1) for v in C.voz]); sys.exit()
    mezclar_audio(C, "/tmp/_cuento.wav")
    N.render(fn, C.dur, out, "/tmp/_cuento.wav")
