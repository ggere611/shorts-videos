"""Generador de shorts de nichos nuevos.
Uso: python3 nichos.py colores salida.mp4 [preview]
     python3 nichos.py animales|animales2|pipo salida.mp4 [preview]
     python3 nichos.py calculo salida.mp4 [preview]
"""
import subprocess, math, sys, wave, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
INK = (40, 40, 60)
_fc, _ec = {}, {}

def F(s):
    if s not in _fc: _fc[s] = ImageFont.truetype(BOLD, s)
    return _fc[s]

def emoji_img(ch, size):
    key = (ch, size)
    if key not in _ec:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
        _ec[key] = im
    return _ec[key]

def ease_back(t):
    t = max(0, min(1, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def text_c(d, xy, s, size, fill, outline=INK, sw=10, scale=1.0):
    if scale <= 0.01: return
    d.text(xy, s, font=F(max(1, int(size * scale))), fill=fill, anchor="mm",
           stroke_width=max(1, int(sw * scale)), stroke_fill=outline)

def paste_emoji(im, ch, cx, cy, size, scale):
    s = int(size * scale)
    if s < 4: return
    e = emoji_img(ch, size).resize((s, s), Image.LANCZOS)
    im.paste(e, (int(cx - s / 2), int(cy - s / 2)), e)

def bg(d, color, t):
    d.rectangle([0, 0, W, H], fill=color)
    for i in range(8):
        x = (i * 173 + t * 40 * (1 + i % 3)) % (W + 200) - 100
        y = (i * 311 + 120 * math.sin(t * 0.8 + i)) % H
        r = 60 + 25 * (i % 4)
        c = tuple(min(255, v + 30) for v in color)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)

# ---------------- COLORES ----------------
COLORES = [("ROJO", "RED", (229, 57, 53), "🍎🍓🚒"), ("AZUL", "BLUE", (30, 136, 229), "🐳🫐🦋"),
           ("AMARILLO", "YELLOW", (253, 216, 53), "🍌🌻🐤"), ("VERDE", "GREEN", (67, 160, 71), "🐸🥦🍀"),
           ("NARANJA", "ORANGE", (251, 140, 0), "🍊🥕🎃"), ("VIOLETA", "PURPLE", (142, 36, 170), "🍇🍆🔮")]
C_INTRO, C_EACH, C_END = 2.5, 3.6, 3.0

def colores_frame(t):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < C_INTRO:
        bg(d, (255, 214, 102), t)
        text_c(d, (W/2, 700), "¡COLORES", 150, (255, 255, 255), scale=ease_back(t / 0.5))
        text_c(d, (W/2, 900), "en inglés!", 150, (229, 57, 53), (255, 255, 255), 12, scale=ease_back((t - 0.3) / 0.5))
        for i, ch in enumerate("🎨🌈✏️"[:2]):
            paste_emoji(im, ch, 300 + i * 480, 1250, 260, ease_back((t - 0.7 - i * 0.2) / 0.4))
        return im
    t2 = t - C_INTRO
    if t2 < len(COLORES) * C_EACH:
        k = int(t2 // C_EACH); lt = t2 - k * C_EACH
        es, en, col, ems = COLORES[k]
        bg(d, col, t)
        light = sum(col) > 600
        tc = INK if light else (255, 255, 255)
        oc = (255, 255, 255) if light else INK
        text_c(d, (W/2, 330), es, 190 if len(es) <= 6 else 150, tc, oc, 12, scale=ease_back(lt / 0.35))
        ems = list(ems.replace("️", ""))
        for i, ch in enumerate(ems[:3]):
            paste_emoji(im, ch, 220 + i * 320, 820, 250, ease_back((lt - 0.3 - i * 0.18) / 0.3))
        s = ease_back((lt - 1.4) / 0.35)
        if s > 0:
            bw, bh = 760 * s, 260 * s
            d.rounded_rectangle([W/2 - bw/2, 1350 - bh/2, W/2 + bw/2, 1350 + bh/2], int(60 * s), fill=(255, 255, 255), outline=INK, width=10)
            text_c(d, (W/2, 1350), en, 170 if len(en) <= 5 else 140, col if not light else INK, INK, 6, scale=s)
            text_c(d, (W/2, 1590), "🇬🇧 en inglés".replace("🇬🇧 ", ""), 70, tc, oc, 6, scale=ease_back((lt - 1.7) / 0.3))
        return im
    lt = t2 - len(COLORES) * C_EACH
    bg(d, (129, 212, 250), t)
    text_c(d, (W/2, 700), "¡GENIAL!", 170, (255, 255, 255), scale=ease_back(lt / 0.5))
    text_c(d, (W/2, 980), "¿Cuál es tu", 100, INK, (255, 255, 255), 6, scale=ease_back((lt - 0.4) / 0.5))
    text_c(d, (W/2, 1110), "color favorito?", 100, (229, 57, 53), (255, 255, 255), 6, scale=ease_back((lt - 0.6) / 0.5))
    paste_emoji(im, "🌈", W/2, 1450, 300, ease_back((lt - 1.0) / 0.5))
    return im

def colores_beats():
    pops, chimes = [], []
    for k in range(len(COLORES)):
        st = C_INTRO + k * C_EACH
        pops += [st + 0.3 + i * 0.18 for i in range(3)]; chimes.append(st + 1.4)
    return pops, chimes

# ---------------- CÁLCULO MENTAL ----------------
PROBLEMAS = [("7 + 8", "15", "FÁCIL", (102, 187, 106)), ("6 × 4", "24", "MEDIO", (255, 167, 38)),
             ("15 − 9", "6", "MEDIO", (255, 167, 38)), ("3 × 3 + 2", "11", "DIFÍCIL", (239, 83, 80))]
M_INTRO, M_EACH, M_END = 2.8, 6.6, 3.0

def calculo_frame(t):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < M_INTRO:
        bg(d, (49, 27, 146), t)
        text_c(d, (W/2, 640), "¿Podés", 160, (255, 255, 255), scale=ease_back(t / 0.4))
        text_c(d, (W/2, 820), "resolverlo", 150, (255, 235, 59), scale=ease_back((t - 0.2) / 0.4))
        text_c(d, (W/2, 1000), "en 5 segundos?", 110, (255, 255, 255), scale=ease_back((t - 0.4) / 0.4))
        paste_emoji(im, "🧠", W/2, 1350, 320, ease_back((t - 0.8) / 0.4) * (1 + 0.05 * math.sin(t * 8)))
        return im
    t2 = t - M_INTRO
    if t2 < len(PROBLEMAS) * M_EACH:
        k = int(t2 // M_EACH); lt = t2 - k * M_EACH
        q, a, lvl, lc = PROBLEMAS[k]
        bg(d, (49, 27, 146), t)
        d.rounded_rectangle([W/2 - 230, 150, W/2 + 230, 260], 50, fill=lc, outline=(255, 255, 255), width=6)
        text_c(d, (W/2, 205), f"{k+1}/4 · {lvl}", 56, (255, 255, 255), INK, 4)
        text_c(d, (W/2, 560), q, 210 if len(q) <= 6 else 170, (255, 255, 255), scale=ease_back(lt / 0.35))
        if lt < 5.6:
            remaining = max(0, 5 - (lt - 0.6))
            n = min(5, max(1, math.ceil(remaining))) if lt >= 0.6 else 5
            frac = (remaining % 1) if lt >= 0.6 else 1
            cx, cy, r = W/2, 1180, 230
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
            ang = 360 * (remaining / 5)
            d.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + ang, fill=(255, 235, 59))
            d.ellipse([cx - r + 40, cy - r + 40, cx + r - 40, cy + r - 40], fill=(255, 255, 255), outline=INK, width=8)
            pulse = 1 + 0.15 * max(0, frac - 0.7) / 0.3
            text_c(d, (cx, cy), str(n), 220, (229, 57, 53), (255, 255, 255), 4, scale=pulse)
        else:
            s = ease_back((lt - 5.6) / 0.3)
            text_c(d, (W/2, 1180), f"= {a}", 280, (255, 235, 59), INK, 14, scale=s)
            paste_emoji(im, "✅", W/2, 1530, 200, ease_back((lt - 5.8) / 0.3))
        return im
    lt = t2 - len(PROBLEMAS) * M_EACH
    bg(d, (49, 27, 146), t)
    text_c(d, (W/2, 650), "¿Cuántas", 150, (255, 255, 255), scale=ease_back(lt / 0.4))
    text_c(d, (W/2, 820), "acertaste?", 150, (255, 235, 59), scale=ease_back((lt - 0.2) / 0.4))
    text_c(d, (W/2, 1080), "¡Desafiá a un amigo!", 70, (255, 255, 255), INK, 6, scale=ease_back((lt - 0.6) / 0.4))
    s = ease_back((lt - 1.0) / 0.5)
    if s > 0:
        bw, bh = 600 * s, 150 * s
        d.rounded_rectangle([W/2 - bw/2, 1350 - bh/2, W/2 + bw/2, 1350 + bh/2], int(40 * s), fill=(229, 57, 53), outline=(255, 255, 255), width=8)
        text_c(d, (W/2, 1350), "SUSCRIBIRME", 72, (255, 255, 255), (229, 57, 53), 2, scale=s)
    return im

def calculo_beats():
    pops, chimes, ticks = [], [], []
    for k in range(len(PROBLEMAS)):
        st = M_INTRO + k * M_EACH
        pops.append(st + 0.05); ticks += [st + 0.6 + j for j in range(5)]; chimes.append(st + 5.6)
    return pops, chimes, ticks

# ---------------- ¿QUÉ ANIMAL ES? (3 a 8 años) ----------------
ANIMALES = [("🐶", "PERRO", "¡Guau guau!", (255, 202, 40)), ("🐱", "GATO", "¡Miau!", (129, 212, 250)),
            ("🐮", "VACA", "¡Muuu!", (165, 214, 167)), ("🦁", "LEÓN", "¡Grrr!", (255, 171, 145)),
            ("🐘", "ELEFANTE", "¡Pruuu!", (206, 147, 216))]
ANIMALES2 = [("🐷", "CHANCHO", "¡Oink oink!", (244, 143, 177)), ("🐸", "RANA", "¡Croac!", (165, 214, 167)),
             ("🦆", "PATO", "¡Cuac cuac!", (129, 212, 250)), ("🐑", "OVEJA", "¡Beee!", (255, 224, 130)),
             ("🐵", "MONO", "¡U-u a-a!", (255, 171, 145))]
A_INTRO, A_EACH, A_END = 2.5, 5.4, 3.0
_sil = {}

def silhouette(ch, size):
    key = (ch, size)
    if key not in _sil:
        e = emoji_img(ch, size)
        a = e.split()[-1]
        s = Image.new("RGBA", e.size, (35, 30, 60, 255)); s.putalpha(a)
        _sil[key] = s
    return _sil[key]

def animales_frame(t):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < A_INTRO:
        bg(d, (255, 214, 102), t)
        text_c(d, (W/2, 640), "¿Qué", 190, (255, 255, 255), scale=ease_back(t / 0.4))
        text_c(d, (W/2, 850), "animal es?", 160, (229, 57, 53), (255, 255, 255), 12, scale=ease_back((t - 0.2) / 0.4))
        for i, ch in enumerate(["🐾", "🔍"]):
            paste_emoji(im, ch, 330 + i * 420, 1250, 250, ease_back((t - 0.6 - i * 0.2) / 0.4))
        return im
    t2 = t - A_INTRO
    if t2 < len(ANIMALES) * A_EACH:
        k = int(t2 // A_EACH); lt = t2 - k * A_EACH
        ch, nombre, sonido, col = ANIMALES[k]
        bg(d, col, t)
        d.rounded_rectangle([W/2 - 200, 140, W/2 + 200, 250], 50, fill=(255, 255, 255), outline=INK, width=6)
        text_c(d, (W/2, 195), f"{k+1} de {len(ANIMALES)}", 60, INK, (255, 255, 255), 2)
        size = 620
        wob = 1 + 0.03 * math.sin(t * 6)
        if lt < 3.6:
            text_c(d, (W/2, 400), "¿Quién es?", 130, (255, 255, 255), scale=ease_back(lt / 0.35))
            s = silhouette(ch, size); sc = ease_back((lt - 0.2) / 0.4) * wob
            ss = int(size * sc)
            if ss > 4:
                s2 = s.resize((ss, ss), Image.LANCZOS); im.paste(s2, (int(W/2 - ss/2), int(980 - ss/2)), s2)
            if lt >= 0.6:
                n = 3 - int(lt - 0.6); n = max(1, min(3, n)); ph = (lt - 0.6) % 1
                r = 110 * ease_back(min(1, ph / 0.3))
                d.ellipse([W/2 - r, 1530 - r, W/2 + r, 1530 + r], fill=(255, 255, 255), outline=INK, width=8)
                text_c(d, (W/2, 1530), str(n), 150, (229, 57, 53), (255, 255, 255), 4, scale=ease_back(min(1, ph / 0.3)))
        else:
            rt = lt - 3.6
            paste_emoji(im, ch, W/2, 980, size, (0.85 + 0.15 * ease_back(rt / 0.35)) * wob)
            text_c(d, (W/2, 400), nombre, 190 if len(nombre) <= 5 else (150 if len(nombre) <= 8 else 130), (255, 255, 255), scale=ease_back(rt / 0.3))
            text_c(d, (W/2, 1530), sonido, 120, (229, 57, 53), (255, 255, 255), 10, scale=ease_back((rt - 0.3) / 0.3))
        return im
    lt = t2 - len(ANIMALES) * A_EACH
    bg(d, (129, 212, 250), t)
    text_c(d, (W/2, 650), "¡MUY BIEN!", 150, (255, 255, 255), scale=ease_back(lt / 0.5))
    text_c(d, (W/2, 900), "¿Cuántos", 110, INK, (255, 255, 255), 6, scale=ease_back((lt - 0.4) / 0.5))
    text_c(d, (W/2, 1030), "adivinaste?", 110, (229, 57, 53), (255, 255, 255), 6, scale=ease_back((lt - 0.6) / 0.5))
    for i, (ch, *_r) in enumerate(ANIMALES):
        paste_emoji(im, ch, 160 + i * 190, 1400, 170, ease_back((lt - 1.0 - i * 0.12) / 0.3))
    return im

def animales_beats():
    pops, chimes, ticks = [], [], []
    for k in range(len(ANIMALES)):
        st = A_INTRO + k * A_EACH
        pops.append(st + 0.2); ticks += [st + 0.6 + j for j in range(3)]; chimes.append(st + 3.6)
    return pops, chimes, ticks


# ---------------- MASCOTAS GIMBRO (PNG en mascotas/) ----------------
_masc = {}
MASC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mascotas")
HOST = os.environ.get("MASCOTA", "carpincho")
HOST_NOMBRE = {"oso": "el Oso", "toro": "el Toro", "rana": "la Rana", "monstruo": "el Monstruito", "gato": "el Gato", "carpincho": "el Carpincho"}

def mascota_img(char, mood, blink=False):
    key = (char, mood, blink)
    if key not in _masc:
        _masc[key] = Image.open(os.path.join(MASC_DIR, f"{char}_{mood}{'_blink' if blink else ''}.png")).convert("RGBA")
    return _masc[key]

def paste_mascota(im, cx, cy, size, t, mood="alentando", talk=False, char=None, jump=False, pose=None, angle=0, flip=False, still=False):
    char = char or HOST
    if talk:
        mood = "hablando" if int(t * 6) % 2 == 0 else "alentando"
    blink = (t % 3.2) < 0.13 and mood != "festejando"
    if pose:
        key = (char, "pose_" + pose, False)
        if key not in _masc: _masc[key] = Image.open(os.path.join(MASC_DIR, f"{char}_pose_{pose}.png")).convert("RGBA")
        m = _masc[key]
    else:
        m = mascota_img(char, mood, blink)
    sq = 1 if still else 1 + 0.03 * math.sin(t * 6)
    hop = 0 if still else (abs(math.sin(t * 7)) * 60 if jump else 6 * math.sin(t * 3))
    w, h = int(size * (2 - sq)), int(size * sq)
    if w < 4: return
    mm = m.resize((w, h), Image.LANCZOS)
    if flip: mm = mm.transpose(Image.FLIP_LEFT_RIGHT)
    if angle: mm = mm.rotate(angle, resample=Image.BICUBIC, expand=True)
    im.paste(mm, (int(cx - mm.width / 2), int(cy - mm.height / 2 - hop)), mm)

# ---------------- PIPO SE EQUIVOCA (mascota original) ----------------
AMARILLO, CELESTE, CORAL, VIOLETA = (255, 210, 63), (94, 200, 242), (255, 122, 89), (142, 91, 217)

def draw_pipo(d, cx, cy, s, t, mood="feliz", wave=0.0):
    """Pipo: pollito explorador original. s = escala (1 = ~360 px de alto)."""
    bob = math.sin(t * 5) * 10 * s
    cy = cy + bob
    R = 150 * s
    # patas
    for dx in (-55, 55):
        x = cx + dx * s
        d.line([x, cy + R * 0.9, x, cy + R * 1.2], fill=(240, 140, 40), width=int(12 * s))
        d.line([x - 25 * s, cy + R * 1.2, x + 25 * s, cy + R * 1.2], fill=(240, 140, 40), width=int(12 * s))
    # alas (la derecha saluda)
    d.ellipse([cx - R - 40 * s, cy - 10 * s, cx - R + 50 * s, cy + 90 * s], fill=(245, 190, 40), outline=INK, width=int(6 * s))
    ang = math.sin(t * 14) * 25 * wave
    wx, wy = cx + R - 5 * s, cy + 20 * s - wave * 60 * s
    d.ellipse([wx - 45 * s, wy - 50 * s + ang, wx + 45 * s, wy + 50 * s + ang], fill=(245, 190, 40), outline=INK, width=int(6 * s))
    # cuerpo
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=AMARILLO, outline=INK, width=int(8 * s))
    # copete
    for i, dx in enumerate((-18, 0, 18)):
        d.ellipse([cx + dx * s - 14 * s, cy - R - 40 * s + abs(dx) * s, cx + dx * s + 14 * s, cy - R + 8 * s], fill=AMARILLO, outline=INK, width=int(5 * s))
    # gorro de explorador
    d.chord([cx - 95 * s, cy - R - 10 * s, cx + 95 * s, cy - R + 90 * s], 180, 360, fill=(120, 170, 90), outline=INK, width=int(6 * s))
    # ojos
    blink = (t % 3.2) < 0.12
    for dx in (-50, 50):
        ex, ey = cx + dx * s, cy - 25 * s
        if blink:
            d.line([ex - 22 * s, ey, ex + 22 * s, ey], fill=INK, width=int(7 * s))
        else:
            big = 1.25 if mood == "sorpresa" else 1.0
            r = 30 * s * big
            d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(255, 255, 255), outline=INK, width=int(5 * s))
            pr = 14 * s
            d.ellipse([ex - pr + 4 * s, ey - pr + 3 * s, ex + pr + 4 * s, ey + pr + 3 * s], fill=INK)
            d.ellipse([ex - 2 * s, ey - 8 * s, ex + 6 * s, ey], fill=(255, 255, 255))
    # pico
    if mood == "sorpresa":
        d.polygon([(cx - 30 * s, cy + 20 * s), (cx + 30 * s, cy + 20 * s), (cx, cy + 45 * s)], fill=(255, 140, 40), outline=INK)
        d.polygon([(cx - 26 * s, cy + 52 * s), (cx + 26 * s, cy + 52 * s), (cx, cy + 75 * s)], fill=(255, 140, 40), outline=INK)
    else:
        d.polygon([(cx - 32 * s, cy + 18 * s), (cx + 32 * s, cy + 18 * s), (cx, cy + 62 * s)], fill=(255, 140, 40), outline=INK)
    # cachetes
    for dx in (-95, 95):
        d.ellipse([cx + dx * s - 22 * s, cy + 20 * s, cx + dx * s + 22 * s, cy + 45 * s], fill=(255, 160, 150))

RONDAS = [("☀️", "El sol es", "AZUL", "AMARILLO", (66, 133, 244)),
          ("🐮", "La vaca hace", "¡GUAU!", "¡MUUU!", None),
          ("🐟", "El pez", "VUELA", "NADA", None),
          ("🍌", "La banana es", "ROJA", "AMARILLA", (229, 57, 53))]
RONDAS2 = [("🐘", "El elefante es", "CHIQUITO", "GRANDE", None),
           ("🌙", "La luna sale de", "DÍA", "NOCHE", None),
           ("🐶", "El perro hace", "¡MIAU!", "¡GUAU!", None),
           ("🍓", "La frutilla es", "AZUL", "ROJA", (66, 133, 244))]
P_INTRO, P_EACH, P_END = 3.0, 7.0, 3.5

def pipo_frame(t):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < P_INTRO:
        bg(d, CELESTE, t)
        paste_mascota(im, W/2, 1150, 760 * max(0.01, ease_back(t / 0.5)), t, talk=True)
        text_c(d, (W/2, 420), "¡Hola!", 190, (255, 255, 255), scale=ease_back((t - 0.3) / 0.4))
        text_c(d, (W/2, 620), f"Soy {HOST_NOMBRE[HOST]}", 110 if len(HOST_NOMBRE[HOST]) < 10 else 90, AMARILLO, INK, 12, scale=ease_back((t - 0.7) / 0.4))
        text_c(d, (W/2, 1650), "¿Me ayudás?", 100, (255, 255, 255), INK, 8, scale=ease_back((t - 1.6) / 0.4))
        return im
    t2 = t - P_INTRO
    if t2 < len(RONDAS) * P_EACH:
        k = int(t2 // P_EACH); lt = t2 - k * P_EACH
        em, frase, mal, bien, col = RONDAS[k]
        if lt < 2.6:  # Pipo dice algo mal
            bg(d, VIOLETA, t)
            text_c(d, (W/2, 330), frase, 110, (255, 255, 255), scale=ease_back(lt / 0.3))
            text_c(d, (W/2, 490), mal, 170, col or (255, 255, 255), INK, 12, scale=ease_back((lt - 0.4) / 0.3))
            paste_emoji(im, em.replace("️", ""), W/2, 820, 300, ease_back((lt - 0.2) / 0.4))
            paste_mascota(im, W/2, 1420, 620, t, talk=True)
        elif lt < 4.6:  # ¿Está bien? pausa para que el chico responda
            bg(d, VIOLETA, t)
            text_c(d, (W/2, 420), "¿Está bien?", 150, AMARILLO, INK, 12, scale=ease_back((lt - 2.6) / 0.3))
            paste_emoji(im, "🤔", W/2, 800, 280, ease_back((lt - 2.8) / 0.3))
            paste_mascota(im, W/2, 1420, 620, t, mood="alentando")
            dots = "." * (1 + int((lt - 2.6) * 2) % 3)
            text_c(d, (W/2, 1050), dots, 160, (255, 255, 255), INK, 8)
        else:  # ¡NO! corrección
            rt = lt - 4.6
            bg(d, CORAL, t)
            text_c(d, (W/2, 300), "¡NOOO!", 170, (255, 255, 255), scale=ease_back(rt / 0.25))
            text_c(d, (W/2, 470), frase, 100, INK, (255, 255, 255), 6, scale=ease_back((rt - 0.3) / 0.3))
            text_c(d, (W/2, 630), bien, 170, AMARILLO, INK, 12, scale=ease_back((rt - 0.5) / 0.3) * (1 + 0.04 * math.sin(t * 10)))
            paste_emoji(im, em.replace("️", ""), W/2 - 230, 950, 260, ease_back((rt - 0.4) / 0.3))
            paste_emoji(im, "✅", W/2 + 230, 950, 200, ease_back((rt - 0.7) / 0.3))
            paste_mascota(im, W/2, 1450, 620, t, mood="festejando", jump=True)
        return im
    lt = t2 - len(RONDAS) * P_EACH
    bg(d, CELESTE, t)
    text_c(d, (W/2, 400), "¡Gracias por", 120, (255, 255, 255), scale=ease_back(lt / 0.4))
    text_c(d, (W/2, 560), "ayudarme!", 140, AMARILLO, INK, 12, scale=ease_back((lt - 0.2) / 0.4))
    paste_mascota(im, W/2, 1100, 720, t, mood="festejando", jump=True)
    text_c(d, (W/2, 1580), "¡Chau chau!", 110, (255, 255, 255), INK, 8, scale=ease_back((lt - 0.8) / 0.4))
    text_c(d, (W/2, 1720), "Nos vemos mañana", 80, AMARILLO, INK, 8, scale=ease_back((lt - 1.0) / 0.4))
    return im

def pipo_beats():
    pops, chimes, ticks = [], [], []
    for k in range(len(RONDAS)):
        st = P_INTRO + k * P_EACH
        pops += [st + 0.05, st + 0.45]; ticks += [st + 2.8, st + 3.4, st + 4.0]; chimes.append(st + 4.6)
    return pops, chimes, ticks

# ---------------- VOCABULARIO BILINGÜE CON MASCOTA ----------------
VOCAB = {
    "animales_en": dict(host="rana", t1="¡Animales", t2="en inglés!", intro_em="🐾", items=[
        ("🐶", "PERRO", "DOG", (255, 202, 40)), ("🐱", "GATO", "CAT", (129, 212, 250)),
        ("🐮", "VACA", "COW", (165, 214, 167)), ("🐷", "CHANCHO", "PIG", (244, 143, 177)),
        ("🐴", "CABALLO", "HORSE", (255, 171, 145)), ("🐔", "GALLINA", "CHICKEN", (206, 147, 216))]),
    "deportes_en": dict(host="toro", t1="¡Deportes", t2="en inglés!", intro_em="🏆", items=[
        ("⚽", "FÚTBOL", "SOCCER", (102, 187, 106)), ("🏀", "BÁSQUET", "BASKETBALL", (255, 167, 38)),
        ("🎾", "TENIS", "TENNIS", (129, 212, 250)), ("🏊", "NATACIÓN", "SWIMMING", (79, 195, 247)),
        ("🚴", "CICLISMO", "CYCLING", (255, 213, 79)), ("🏐", "VÓLEY", "VOLLEYBALL", (206, 147, 216))]),
    "colores2": dict(host="gato", t1="¡Más colores", t2="en inglés!", intro_em="🎨", items=[
        ("🌸🦩🎀", "ROSA", "PINK", (244, 143, 177)), ("☁️🐑🥛", "BLANCO", "WHITE", (176, 190, 197)),
        ("🐻🍫🥔", "MARRÓN", "BROWN", (161, 110, 72)), ("🐘🐭🪨", "GRIS", "GRAY", (144, 164, 174)),
        ("🎱🎩🕷️", "NEGRO", "BLACK", (66, 66, 80)), ("🌊🐬💎", "CELESTE", "LIGHT BLUE", (94, 200, 242))]),
}
V_INTRO, V_EACH, V_END = 2.8, 4.2, 3.2
VSET = VOCAB["animales_en"]

def vocab_frame(t):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    host, items = VSET["host"], VSET["items"]
    if t < V_INTRO:
        bg(d, (255, 214, 102), t)
        text_c(d, (W/2, 420), VSET["t1"], 150 if len(VSET["t1"]) <= 10 else 125, (255, 255, 255), scale=ease_back(t / 0.4))
        text_c(d, (W/2, 590), VSET["t2"], 140, (229, 57, 53), (255, 255, 255), 12, scale=ease_back((t - 0.25) / 0.4))
        paste_emoji(im, VSET["intro_em"], W/2, 820, 200, ease_back((t - 0.6) / 0.4))
        paste_mascota(im, W/2, 1350, 700 * max(0.01, ease_back((t - 0.2) / 0.5)), t, talk=True, char=host)
        return im
    t2 = t - V_INTRO
    if t2 < len(items) * V_EACH:
        k = int(t2 // V_EACH); lt = t2 - k * V_EACH
        ems, es, en, col = items[k]
        bg(d, col, t)
        dark = sum(col) < 330
        tc, oc = (255, 255, 255), INK
        d.rounded_rectangle([W/2 - 170, 120, W/2 + 170, 220], 45, fill=(255, 255, 255), outline=INK, width=6)
        text_c(d, (W/2, 170), f"{k+1} de {len(items)}", 54, INK, (255, 255, 255), 2)
        text_c(d, (W/2, 340), es, 160 if len(es) <= 7 else 130, tc, oc, 12, scale=ease_back(lt / 0.3))
        ems = [e for e in ems.replace("️", "")]
        if len(ems) == 1:
            paste_emoji(im, ems[0], W/2, 720, 420, ease_back((lt - 0.2) / 0.35))
        else:
            for i, ch in enumerate(ems[:3]):
                paste_emoji(im, ch, 220 + i * 320, 700, 250, ease_back((lt - 0.2 - i * 0.15) / 0.3))
        s = ease_back((lt - 1.4) / 0.3)
        if s > 0:
            bw = (90 * len(en) + 160) * s; bw = min(bw, 960 * s); bh = 220 * s
            d.rounded_rectangle([W/2 - bw/2, 1100 - bh/2, W/2 + bw/2, 1100 + bh/2], int(55 * s), fill=(255, 255, 255), outline=INK, width=10)
            fs = 150 if len(en) <= 6 else (120 if len(en) <= 8 else 95)
            text_c(d, (W/2, 1100), en, fs, tuple(int(v * 0.55) for v in col) if not dark else INK, (255, 255, 255), 4, scale=s)
            text_c(d, (W/2, 1270), "en inglés", 64, tc, oc, 6, scale=ease_back((lt - 1.7) / 0.3))
        mood = "festejando" if lt > 2.9 else None
        if mood:
            paste_mascota(im, W/2, 1620, 470, t, mood="festejando", char=host, jump=True)
        else:
            paste_mascota(im, W/2, 1620, 470, t, talk=True, char=host)
        return im
    lt = t2 - len(items) * V_EACH
    bg(d, (129, 212, 250), t)
    text_c(d, (W/2, 420), "¡Muy bien!", 150, (255, 255, 255), scale=ease_back(lt / 0.4))
    text_c(d, (W/2, 590), "Very good!", 120, AMARILLO, INK, 12, scale=ease_back((lt - 0.3) / 0.4))
    paste_mascota(im, W/2, 1120, 700, t, mood="festejando", char=host, jump=True)
    text_c(d, (W/2, 1600), "¡Chau chau!", 110, (255, 255, 255), INK, 8, scale=ease_back((lt - 0.8) / 0.4))
    text_c(d, (W/2, 1740), "Bye bye!", 90, AMARILLO, INK, 8, scale=ease_back((lt - 1.0) / 0.4))
    return im

def vocab_beats():
    pops, chimes = [], []
    for k in range(len(VSET["items"])):
        st = V_INTRO + k * V_EACH
        pops += [st + 0.05, st + 0.25]; chimes.append(st + 1.4)
    return pops, chimes

# ---------------- AVENTURA CON DECISIONES ----------------
AVENTURA = dict(host="oso", titulo1="¡Aventura!", titulo2="Ayudá al Oso", meta="🍯", meta_txt="a encontrar la miel",
    pasos=[("¿Por dónde cruzo el río?", ("🌉", "PUENTE"), ("🐊", "COCODRILO"), 0, (129, 212, 250)),
           ("¿Qué camino sigo?", ("🌵", "ESPINAS"), ("🌼", "FLORES"), 1, (165, 214, 167)),
           ("¿Quién me dice dónde está?", ("🐝", "ABEJA"), ("🦈", "TIBURÓN"), 0, (255, 224, 130))],
    final1="¡La encontramos!", final2="¡Gracias, amigo!")
AV_INTRO, AV_EACH, AV_END = 3.2, 7.0, 4.0

def aventura_frame(t):
    A = AVENTURA; host = A["host"]
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < AV_INTRO:
        bg(d, (255, 171, 145), t)
        text_c(d, (W/2, 330), A["titulo1"], 150, (255, 235, 59), scale=ease_back(t / 0.3) * (1 + 0.04 * math.sin(t * 9)))
        text_c(d, (W/2, 520), A["titulo2"], 110, (255, 255, 255), scale=ease_back((t - 0.3) / 0.3))
        text_c(d, (W/2, 650), A["meta_txt"], 80, (255, 255, 255), INK, 8, scale=ease_back((t - 0.6) / 0.3))
        paste_emoji(im, A["meta"], W/2, 880, 240, ease_back((t - 0.9) / 0.4))
        paste_mascota(im, W/2, 1400, 660, t, talk=True, char=host)
        return im
    t2 = t - AV_INTRO; n = len(A["pasos"])
    if t2 < n * AV_EACH:
        k = int(t2 // AV_EACH); lt = t2 - k * AV_EACH
        preg, op1, op2, ok, col = A["pasos"][k]
        bg(d, col, t)
        # camino de progreso
        for i in range(n + 1):
            x = 190 + i * (W - 380) / n
            if i < n: d.line([x, 170, x + (W - 380) / n, 170], fill=(255, 255, 255), width=14)
        for i in range(n + 1):
            x = 190 + i * (W - 380) / n
            d.ellipse([x - 26, 144, x + 26, 196], fill=(102, 187, 106) if i <= k else (255, 255, 255), outline=INK, width=6)
        paste_emoji(im, A["meta"], W - 190, 100, 90, 1)
        size = 96 if len(preg) <= 22 else 80
        lines = preg.split(" "); mid = (len(lines) + 1) // 2
        text_c(d, (W/2, 330), " ".join(lines[:mid]), size, (255, 255, 255), scale=ease_back(lt / 0.3))
        text_c(d, (W/2, 330 + size * 1.15), " ".join(lines[mid:]), size, (255, 255, 255), scale=ease_back((lt - 0.1) / 0.3))
        reveal = lt >= 4.2
        for i, (em, lab) in enumerate((op1, op2)):
            cx = W/2 + (-260 if i == 0 else 260); cy = 860
            sc = ease_back((lt - 0.5 - i * 0.2) / 0.3)
            if sc <= 0: continue
            good = (i == ok)
            if reveal and good: sc *= 1.12 + 0.04 * math.sin(t * 10)
            if reveal and not good: sc *= 0.8
            bw = 230 * sc
            ring = (102, 187, 106) if (reveal and good) else ((200, 200, 200) if reveal else INK)
            d.rounded_rectangle([cx - bw, cy - bw, cx + bw, cy + bw], int(60 * sc), fill=(255, 255, 255), outline=ring, width=int(18 if reveal and good else 8))
            paste_emoji(im, em, cx, cy - 20 * sc, 270, sc)
            text_c(d, (cx, cy + 290 * sc), lab, 62 if len(lab) <= 7 else 50, (255, 255, 255), INK, 8, scale=sc)
            if reveal: paste_emoji(im, "✅" if good else "❌", cx + 170 * sc, cy - 170 * sc, 120, ease_back((lt - 4.2) / 0.3))
        if not reveal:
            if lt >= 1.2:
                c = 3 - int(lt - 1.2); c = max(1, min(3, c)); ph = (lt - 1.2) % 1
                r = 95 * ease_back(min(1, ph / 0.3))
                d.ellipse([W/2 - r, 1290 - r, W/2 + r, 1290 + r], fill=(255, 255, 255), outline=INK, width=8)
                text_c(d, (W/2, 1290), str(c), 130, (229, 57, 53), (255, 255, 255), 4, scale=ease_back(min(1, ph / 0.3)))
            paste_mascota(im, W/2, 1620, 440, t, talk=lt < 1.2, char=host)
        else:
            rt = lt - 4.2
            mx = W/2 + (-260 if ok == 0 else 260) * smooth_(rt / 0.8)
            text_c(d, (W/2, 1290), "¡Por acá!", 120, (255, 235, 59), scale=ease_back(rt / 0.3))
            paste_mascota(im, mx, 1620, 440, t, mood="festejando", char=host, jump=True)
        return im
    lt = t2 - n * AV_EACH
    bg(d, (129, 212, 250), t)
    text_c(d, (W/2, 380), A["final1"], 100, (255, 255, 255), scale=ease_back(lt / 0.4))
    paste_emoji(im, A["meta"], W/2, 700, 360, ease_back((lt - 0.2) / 0.5) * (1 + 0.05 * math.sin(t * 8)))
    paste_mascota(im, W/2, 1250, 620, t, mood="festejando", char=host, jump=True)
    text_c(d, (W/2, 1640), A["final2"], 100, (255, 235, 59), INK, 10, scale=ease_back((lt - 0.8) / 0.4))
    text_c(d, (W/2, 1770), "Mañana, otra aventura", 64, (255, 255, 255), INK, 6, scale=ease_back((lt - 1.2) / 0.4))
    return im

def smooth_(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)

def aventura_beats():
    pops, chimes, ticks = [], [], []
    for k in range(len(AVENTURA["pasos"])):
        st = AV_INTRO + k * AV_EACH
        pops += [st + 0.5, st + 0.7]; ticks += [st + 1.2 + j for j in range(3)]; chimes.append(st + 4.2)
    chimes.append(AV_INTRO + len(AVENTURA["pasos"]) * AV_EACH + 0.2)
    return pops, chimes, ticks

# ---------------- JUEGO: ENCONTRÁ AL INTRUSO ----------------
INTRUSO = dict(host="monstruo", rondas=[("🐶", "🐱", 2, 2, 3, "FÁCIL"), ("🍎", "🍊", 3, 3, 5, "MEDIO"),
                                        ("🐸", "🐢", 4, 4, 9, "DIFÍCIL"), ("🌝", "🌞", 4, 4, 6, "¡EXPERTO!")])
IN_INTRO, IN_EACH, IN_END = 2.8, 6.4, 3.4

def intruso_frame(t):
    host = INTRUSO["host"]; R = INTRUSO["rondas"]
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < IN_INTRO:
        bg(d, VIOLETA, t)
        text_c(d, (W/2, 380), "¡Encontrá", 150, (255, 255, 255), scale=ease_back(t / 0.3))
        text_c(d, (W/2, 560), "al INTRUSO!", 150, (255, 235, 59), scale=ease_back((t - 0.2) / 0.3) * (1 + 0.04 * math.sin(t * 9)))
        paste_emoji(im, "🔍", W/2, 820, 220, ease_back((t - 0.5) / 0.4))
        paste_mascota(im, W/2, 1380, 660, t, talk=True, char=host)
        return im
    t2 = t - IN_INTRO
    if t2 < len(R) * IN_EACH:
        k = int(t2 // IN_EACH); lt = t2 - k * IN_EACH
        base, odd, cols, rows, pos, niv = R[k]
        bg(d, [(129, 212, 250), (165, 214, 167), (255, 204, 128), (244, 143, 177)][k % 4], t)
        d.rounded_rectangle([W/2 - 260, 110, W/2 + 260, 220], 50, fill=(255, 255, 255), outline=INK, width=6)
        text_c(d, (W/2, 165), f"{k+1}/{len(R)} · {niv}", 56, INK, (255, 255, 255), 2)
        reveal = lt >= 4.3
        text_c(d, (W/2, 320), "¡Acá está!" if reveal else "¿Cuál es distinto?", 92, (255, 255, 255), scale=ease_back((lt - (4.3 if reveal else 0)) / 0.3))
        gw = 920; cell = gw / cols; gy0 = 460; es = int(cell * 0.78)
        for i in range(cols * rows):
            r_, c_ = divmod(i, cols)
            cx = W/2 - gw/2 + cell * (c_ + 0.5); cy = gy0 + cell * (r_ + 0.5)
            sc = ease_back((lt - 0.2 - i * 0.6 / (cols * rows)) / 0.25)
            if sc <= 0: continue
            is_odd = (i == pos)
            if reveal and is_odd:
                rr = cell * 0.56 * (1 + 0.06 * math.sin(t * 10))
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(255, 255, 255), outline=(229, 57, 53), width=14)
                sc *= 1.1
            elif reveal: sc *= 0.82
            paste_emoji(im, odd if is_odd else base, cx, cy, es, sc)
        gy1 = gy0 + cell * rows
        if not reveal:
            # barra de tiempo
            frac = max(0, 1 - max(0, lt - 0.8) / 3.5)
            d.rounded_rectangle([120, gy1 + 40, W - 120, gy1 + 90], 25, fill=(255, 255, 255), outline=INK, width=5)
            if frac > 0.02: d.rounded_rectangle([126, gy1 + 46, 126 + (W - 252) * frac, gy1 + 84], 20, fill=(229, 57, 53) if frac < 0.35 else (102, 187, 106))
            paste_mascota(im, W/2, 1700, 360, t, talk=lt < 0.8, char=host)
        else:
            paste_mascota(im, W/2, 1700, 360, t, mood="festejando", char=host, jump=True)
        return im
    lt = t2 - len(R) * IN_EACH
    bg(d, CELESTE, t)
    text_c(d, (W/2, 420), "¿Cuántos", 140, (255, 255, 255), scale=ease_back(lt / 0.4))
    text_c(d, (W/2, 590), "encontraste?", 130, (255, 235, 59), scale=ease_back((lt - 0.2) / 0.4))
    paste_mascota(im, W/2, 1120, 680, t, mood="festejando", char=host, jump=True)
    text_c(d, (W/2, 1620), "¡Jugá de nuevo mañana!", 68, (255, 255, 255), INK, 8, scale=ease_back((lt - 0.8) / 0.4))
    return im

def intruso_beats():
    pops, chimes, ticks = [], [], []
    for k in range(len(INTRUSO["rondas"])):
        st = IN_INTRO + k * IN_EACH
        pops += [st + 0.2 + j * 0.15 for j in range(4)]; ticks += [st + 1.3 + j for j in range(3)]; chimes.append(st + 4.3)
    return pops, chimes, ticks

# ---------------- LABERINTO ----------------
import random as _rnd
from collections import deque
LAB = dict(host="carpincho", meta="🍊", t1="¡Laberinto!", t2="Llevá al Carpincho", t3="hasta su naranja",
           niveles=[(5, 6, 4.0, 5.0, 11, "FÁCIL"), (7, 8, 5.0, 7.5, 5, "DIFÍCIL")])
LB_INTRO, LB_CHEER, LB_END = 2.8, 1.4, 3.2
_lab = {}

def make_maze(cols, rows, seed):
    key = (cols, rows, seed)
    if key in _lab: return _lab[key]
    r = _rnd.Random(seed); open_ = set(); seen = {(0, 0)}; st = [(0, 0)]
    while st:
        x, y = st[-1]
        nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < cols and 0 <= y + dy < rows and (x + dx, y + dy) not in seen]
        if not nb: st.pop(); continue
        n = r.choice(nb); open_.add(frozenset(((x, y), n))); seen.add(n); st.append(n)
    prev = {(0, 0): None}; q = deque([(0, 0)])
    while q:
        c = q.popleft()
        if c == (cols - 1, rows - 1): break
        x, y = c
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n not in prev and frozenset((c, n)) in open_: prev[n] = c; q.append(n)
    path = []; c = (cols - 1, rows - 1)
    while c is not None: path.append(c); c = prev[c]
    _lab[key] = (open_, path[::-1]); return _lab[key]

def lab_dur(): return LB_INTRO + sum(n[2] + n[3] + LB_CHEER for n in LAB["niveles"]) + LB_END

def laberinto_frame(t):
    host = LAB["host"]
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < LB_INTRO:
        bg(d, (165, 214, 167), t)
        text_c(d, (W/2, 330), LAB["t1"], 150, (255, 235, 59), scale=ease_back(t / 0.3) * (1 + 0.04 * math.sin(t * 9)))
        text_c(d, (W/2, 520), LAB["t2"], 92, (255, 255, 255), scale=ease_back((t - 0.3) / 0.3))
        text_c(d, (W/2, 640), LAB["t3"], 92, (255, 255, 255), scale=ease_back((t - 0.5) / 0.3))
        paste_emoji(im, LAB["meta"], W/2 + 300, 900, 200, ease_back((t - 0.8) / 0.4))
        paste_mascota(im, W/2 - 80, 1350, 640, t, char=host, pose="profe")
        return im
    t2 = t - LB_INTRO
    for k, (cols, rows, tthink, twalk, seed, niv) in enumerate(LAB["niveles"]):
        seg = tthink + twalk + LB_CHEER
        if t2 < seg:
            open_, path = make_maze(cols, rows, seed)
            bg(d, [(129, 212, 250), (255, 204, 128)][k % 2], t)
            d.rounded_rectangle([W/2 - 260, 100, W/2 + 260, 210], 50, fill=(255, 255, 255), outline=INK, width=6)
            text_c(d, (W/2, 155), f"Nivel {k+1} · {niv}", 56, INK, (255, 255, 255), 2)
            walking = t2 >= tthink; done = t2 >= tthink + twalk
            text_c(d, (W/2, 300), "¡Llegó!" if done else ("¡Seguilo!" if walking else "¿Por dónde va?"), 96, (255, 255, 255))
            gw = 900; cell = gw / cols; x0 = W/2 - gw/2; y0 = 400
            d.rounded_rectangle([x0 - 16, y0 - 16, x0 + gw + 16, y0 + cell * rows + 16], 30, fill=(255, 255, 255), outline=INK, width=10)
            for x in range(cols):
                for y in range(rows):
                    px, py = x0 + x * cell, y0 + y * cell
                    if x + 1 < cols and frozenset(((x, y), (x + 1, y))) not in open_: d.line([px + cell, py, px + cell, py + cell], fill=INK, width=12)
                    if y + 1 < rows and frozenset(((x, y), (x, y + 1))) not in open_: d.line([px, py + cell, px + cell, py + cell], fill=INK, width=12)
            cen = lambda c: (x0 + (c[0] + 0.5) * cell, y0 + (c[1] + 0.5) * cell)
            gx, gy = cen(path[-1])
            if not done: paste_emoji(im, LAB["meta"], gx, gy, int(cell * 0.7), 1 + 0.08 * math.sin(t * 6))
            if not walking:
                mx, my = cen(path[0]); paste_mascota(im, mx, my, cell * 0.95, t, char=host)
                frac = max(0, 1 - t2 / tthink); by = y0 + cell * rows + 60
                d.rounded_rectangle([120, by, W - 120, by + 50], 25, fill=(255, 255, 255), outline=INK, width=5)
                if frac > 0.02: d.rounded_rectangle([126, by + 6, 126 + (W - 252) * frac, by + 44], 20, fill=(229, 57, 53) if frac < 0.35 else (102, 187, 106))
            else:
                p = min(1, (t2 - tthink) / twalk) * (len(path) - 1); i = min(int(p), len(path) - 2); f = p - i
                for j in range(i + 1):
                    a, b = cen(path[j]), cen(path[j + 1]); ff = 1 if j < i else f
                    d.line([a[0], a[1], a[0] + (b[0] - a[0]) * ff, a[1] + (b[1] - a[1]) * ff], fill=(255, 122, 89), width=int(cell * 0.16))
                a, b = cen(path[i]), cen(path[i + 1])
                mx, my = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                if done: paste_mascota(im, gx, gy, cell * 1.1, t, mood="festejando", char=host, jump=True)
                else: paste_mascota(im, mx, my, cell * 0.95, t, char=host, angle=9 * math.sin(t * 14), flip=b[0] < a[0], still=True)
            return im
        t2 -= seg
    bg(d, CELESTE, t)
    text_c(d, (W/2, 380), "¡Lo logramos!", 120, (255, 255, 255), scale=ease_back(t2 / 0.4))
    paste_mascota(im, W/2, 1000, 700, t, char=host, pose="fruta", jump=True)
    text_c(d, (W/2, 1560), "¿Encontraste el camino?", 66, (255, 235, 59), INK, 8, scale=ease_back((t2 - 0.6) / 0.4))
    text_c(d, (W/2, 1700), "Mañana, otro laberinto", 64, (255, 255, 255), INK, 6, scale=ease_back((t2 - 1.0) / 0.4))
    return im

def laberinto_beats():
    pops, chimes, ticks = [], [], []; st = LB_INTRO
    for cols, rows, tthink, twalk, seed, niv in LAB["niveles"]:
        ticks += [st + 0.5 + j for j in range(int(tthink) - 1)]
        pops += [st + tthink + j * 0.45 for j in range(int(twalk / 0.45))]
        chimes.append(st + tthink + twalk); st += tthink + twalk + LB_CHEER
    return pops, chimes, ticks

# ---------------- MOVETE CON LA MASCOTA ----------------
MOVETE = dict(host="toro", t1="¡Movete", t2="con el Toro!", pasos=[
    ("¡ESTIRATE!", "estirar", (129, 212, 250)), ("¡SALTÁ!", "salto", (255, 204, 128)),
    ("¡SALTÁ LA SOGA!", "soga", (165, 214, 167)), ("¡COMÉ FRUTA!", "fruta", (244, 143, 177)),
    ("¡TOMÁ AGUA!", "agua", (128, 222, 234))])
MV_INTRO, MV_EACH, MV_FREEZE, MV_END = 2.8, 4.0, 3.6, 3.0

def movete_frame(t):
    host = MOVETE["host"]; P = MOVETE["pasos"]
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < MV_INTRO:
        bg(d, (255, 171, 145), t)
        text_c(d, (W/2, 360), MOVETE["t1"], 170, (255, 255, 255), scale=ease_back(t / 0.3))
        text_c(d, (W/2, 560), MOVETE["t2"], 130, (255, 235, 59), scale=ease_back((t - 0.2) / 0.3) * (1 + 0.04 * math.sin(t * 9)))
        text_c(d, (W/2, 720), "¡Parate y copiame!", 76, (255, 255, 255), INK, 8, scale=ease_back((t - 0.8) / 0.3))
        paste_mascota(im, W/2, 1350, 720, t, talk=True, char=host, jump=True)
        return im
    t2 = t - MV_INTRO
    if t2 < len(P) * MV_EACH:
        k = int(t2 // MV_EACH); lt = t2 - k * MV_EACH
        txt, pose, col = P[k]
        bg(d, col, t)
        text_c(d, (W/2, 330), txt, 150 if len(txt) <= 9 else 92, (255, 255, 255), scale=ease_back(lt / 0.25) * (1 + 0.05 * math.sin(t * 10)))
        beat = int(lt / 0.5); up = beat % 2 == 0
        if pose == "salto": paste_mascota(im, W/2, 1050, 760, t, mood="festejando", char=host, jump=True)
        elif pose == "estirar":
            if up: paste_mascota(im, W/2, 1020, 800, t, char=host, pose="estirar", still=True)
            else: paste_mascota(im, W/2, 1080, 760, t, char=host, still=True)
        elif pose == "soga":
            paste_mascota(im, W/2, 1080 - (70 if up else 0), 760, t, char=host, pose="soga", still=True)
        else:
            paste_mascota(im, W/2, 1060, 760, t, char=host, pose=pose, angle=6 * math.sin(t * 8), still=True)
        n = min(4, int(lt) + 1)
        for i in range(4):
            cx = W/2 - 240 + i * 160; r = 58 if i == n - 1 else 46
            d.ellipse([cx - r, 1620 - r, cx + r, 1620 + r], fill=(255, 235, 59) if i < n else (255, 255, 255), outline=INK, width=7)
            text_c(d, (cx, 1620), str(i + 1), 64, INK, (255, 255, 255), 2)
        return im
    lt = t2 - len(P) * MV_EACH
    if lt < MV_FREEZE:
        bg(d, VIOLETA, 0)
        text_c(d, (W/2, 330), "¡ESTATUA!", 160, (255, 235, 59), scale=ease_back(lt / 0.2))
        text_c(d, (W/2, 500), "No te muevas…", 84, (255, 255, 255), scale=ease_back((lt - 0.3) / 0.3))
        paste_mascota(im, W/2, 1080, 760, 0.5, char=host, pose="estirar", still=True)
        c = 3 - int(lt - 0.5) if lt >= 0.5 else 3; c = max(1, min(3, c))
        d.ellipse([W/2 - 90, 1530, W/2 + 90, 1710], fill=(255, 255, 255), outline=INK, width=8)
        text_c(d, (W/2, 1620), str(c), 120, (229, 57, 53), (255, 255, 255), 4)
        return im
    lt -= MV_FREEZE
    bg(d, CELESTE, t)
    text_c(d, (W/2, 380), "¡Muy bien!", 150, (255, 255, 255), scale=ease_back(lt / 0.4))
    text_c(d, (W/2, 550), "¡Qué energía!", 100, (255, 235, 59), INK, 10, scale=ease_back((lt - 0.3) / 0.4))
    paste_mascota(im, W/2, 1100, 720, t, mood="festejando", char=host, jump=True)
    text_c(d, (W/2, 1640), "Mañana nos movemos otra vez", 62, (255, 255, 255), INK, 6, scale=ease_back((lt - 0.8) / 0.4))
    return im

def movete_beats():
    pops, chimes, ticks = [], [], []
    for k in range(len(MOVETE["pasos"])):
        st = MV_INTRO + k * MV_EACH
        chimes.append(st); pops += [st + 0.5 * j for j in range(1, 8)]
    st = MV_INTRO + len(MOVETE["pasos"]) * MV_EACH
    ticks += [st + 0.5 + j for j in range(3)]; chimes.append(st + MV_FREEZE)
    return pops, chimes, ticks

# ---------------- CUENTO ENTRE MASCOTAS (fondo limpio, poses claras, pausas) ----------------
CU_DUR = 31.0
CU_Y = 1300

def _sombra(d, x, y, size, k=1.0):
    w = size * 0.36 * k
    d.ellipse([x - w, y + size * 0.40, x + w, y + size * 0.40 + size * 0.10], fill=(226, 230, 238))

def _actor(im, d, char, x, t, size=340, estado="idle", mira_izq=False, y=CU_Y, entra=None):
    """estado: idle | habla | camina | triste | festeja | profe"""
    sc = 1.0
    if entra is not None:
        sc = ease_back((t - entra) / 0.35)
        if sc <= 0.02: return
    hop = 0; ang = 0
    if estado == "camina": hop = abs(math.sin(t * 9)) * 34; ang = 7 * math.sin(t * 9)
    if estado == "festeja": hop = abs(math.sin(t * 8 + x)) * 80
    _sombra(d, x, y, size * sc, 1 - hop / 260)
    sq = 1 + (0.05 * math.sin(t * 9 * 2) if estado == "camina" else 0.02 * math.sin(t * 4 + x))
    kw = dict(char=char, still=True, flip=mira_izq, angle=ang)
    if estado == "habla": kw["talk"] = True
    elif estado == "triste": kw["mood"] = "corrigiendo"
    elif estado == "festeja": kw["mood"] = "festejando"
    elif estado == "profe": kw["pose"] = "profe"
    paste_mascota(im, x, y - hop + (1 - sq) * size * 0.3, size * sc * sq, t, **kw)

def _globo(d, x, y, txt, t, t0, size=58):
    sc = ease_back((t - t0) / 0.25)
    if sc <= 0.02: return
    f = F(int(size * sc) or 1); lines = txt.split("\n")
    w = max(f.getlength(l) for l in lines) + 70 * sc; h = (len(lines) * size * 1.2 + 50) * sc
    x = max(w / 2 + 20, min(W - w / 2 - 20, x))
    d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], int(40 * sc), fill=(255, 255, 255), outline=INK, width=7)
    d.polygon([(x - 24 * sc, y - 4), (x + 24 * sc, y - 4), (x, y + 44 * sc)], fill=(255, 255, 255), outline=INK)
    d.line([x - 20 * sc, y - 3, x + 20 * sc, y - 3], fill=(255, 255, 255), width=9)
    for i, l in enumerate(lines):
        d.text((x, y - h + (35 + size * 0.6 + i * size * 1.2) * sc), l, font=f, fill=INK, anchor="mm")

def _narra(d, txt, t, t0, col=CORAL):
    sc = ease_back((t - t0) / 0.3)
    if sc <= 0.02: return
    for i, l in enumerate(txt.split("\n")):
        text_c(d, (W/2, 250 + i * 110), l, 88, col, (255, 255, 255), 10, scale=sc)

def cuento_frame(t):
    im = Image.new("RGB", (W, H), (250, 251, 253)); d = ImageDraw.Draw(im)
    d.ellipse([-200, CU_Y + 60, W + 200, CU_Y + 900], fill=(240, 244, 250))  # piso suave
    lerp = lambda a, b, k: a + (b - a) * smooth_(k)
    if t < 4.5:      # 1. El Oso quiere jugar
        _narra(d, "El Oso quiere jugar…", t, 0.2)
        x = lerp(-200, W/2, t / 1.8)
        _actor(im, d, "oso", x, t, 420, "camina" if t < 1.8 else ("triste" if t > 2.4 else "idle"))
        if t > 2.4: _globo(d, x, CU_Y - 270, "¿Y mi pelota?", t, 2.4)
    elif t < 10:     # 2. Llega la Rana
        lt = t - 4.5
        _narra(d, "¡Llega la Rana!", t, 4.6, (67, 160, 71))
        ox = lerp(W/2, 330, lt / 0.8)
        rx = lerp(W + 200, 760, lt / 1.4)
        _actor(im, d, "oso", ox, t, 400, "habla" if 1.6 < lt < 3.2 else "triste")
        _actor(im, d, "rana", rx, t, 380, "camina" if lt < 1.4 else ("habla" if lt > 3.3 else "idle"), mira_izq=True)
        if 1.6 < lt < 3.3: _globo(d, ox, CU_Y - 260, "¿Viste\nmi pelota?", t, 4.5 + 1.6)
        if lt > 3.3: _globo(d, rx, CU_Y - 250, "¡No! Pero\nte ayudo", t, 4.5 + 3.3)
    elif t < 15:     # 3. Buscan y aparece el Gato
        lt = t - 10
        _narra(d, "Buscan y buscan…", t, 10.1, (30, 136, 229))
        gx = lerp(W + 220, 820, (lt - 1.6) / 1.2)
        _actor(im, d, "oso", 250, t, 360, "camina" if lt < 2.6 else "idle")
        _actor(im, d, "rana", 530, t, 340, "camina" if lt < 2.6 else "idle")
        if lt > 1.6: _actor(im, d, "gato", gx, t, 360, "profe" if lt > 2.8 else "camina", mira_izq=True)
        if lt > 3.0: _globo(d, gx, CU_Y - 290, "¡Yo vi algo\npor allá!", t, 13.0)
    elif t < 21.5:   # 4. ¿Dónde está? (pausa para el chico)
        lt = t - 15
        _narra(d, "¿Dónde está\nla pelota?" if lt < 4.2 else "¡Atrás del arbusto!", t, 15.1 if lt < 4.2 else 19.2, VIOLETA)
        paste_emoji(im, "⚽", 955 + 10 * math.sin(t * 5), CU_Y + 40, 110, 1 if lt < 4.2 else 0)
        mx_show = lt > 4.2
        if mx_show:
            my = lerp(CU_Y - 80, CU_Y - 400, (lt - 4.2) / 0.5)
            _actor(im, d, "monstruo", 720, t, 360, "festeja" if lt > 5 else "idle", y=my)
            paste_emoji(im, "⚽", 930, CU_Y - 520 - abs(math.sin(t * 6)) * 40, 130, 1)
        paste_emoji(im, "🌳", 720, CU_Y - 110, 520, 1)
        _actor(im, d, "oso", 180, t, 320, "festeja" if lt > 4.6 else "idle")
        _actor(im, d, "rana", 400, t, 300, "festeja" if lt > 4.6 else "idle")
        if lt < 4.2 and lt > 1.0:
            c = 3 - int(lt - 1.2) if lt >= 1.2 else 3; c = max(1, min(3, c))
            d.ellipse([W/2 - 80, 560, W/2 + 80, 720], fill=(255, 255, 255), outline=INK, width=8)
            text_c(d, (W/2, 640), str(c), 110, (229, 57, 53), (255, 255, 255), 4)
        if lt > 5.0: _globo(d, 640, CU_Y - 640, "¡La encontré!", t, 20.0)
    elif t < 27:     # 5. Juegan todos
        lt = t - 21.5
        _narra(d, "¿Jugamos todos?", t, 21.6, (251, 140, 0))
        xs = [150, 410, 670, 930]; chars = ["oso", "rana", "gato", "monstruo"]
        for i, (c, x) in enumerate(zip(chars, xs)):
            _actor(im, d, c, x, t, 300, "festeja" if lt > 1.5 else "idle", mira_izq=i >= 2)
        if lt > 1.2:
            p = ((lt - 1.2) / 0.7) % 6; i = int(p); f = p - i
            seq = [0, 1, 2, 3, 2, 1, 0]; a, b = xs[seq[i]], xs[seq[i + 1]]
            bx = a + (b - a) * f; by = CU_Y - 330 - 330 * math.sin(math.pi * f)
            paste_emoji(im, "⚽", bx, by, 130, 1)
        else: paste_emoji(im, "⚽", 930, CU_Y - 330, 130, 1)
    else:            # 6. Cierre
        lt = t - 27
        _narra(d, "¡Jugar juntos\nes más divertido!", t, 27.1, CORAL)
        for i, (c, x) in enumerate(zip(["oso", "rana", "gato", "monstruo"], [150, 410, 670, 930])):
            _actor(im, d, c, x, t, 300, "festeja", mira_izq=i >= 2)
        text_c(d, (W/2, 1760), "Mañana, otra aventura", 64, INK, (255, 255, 255), 4, scale=ease_back((lt - 1.2) / 0.4))
    return im

def cuento_beats():
    pops = [2.4, 6.1, 7.8, 13.0, 20.0] + [22.7 + 0.7 * j for j in range(6)]
    chimes = [0.2, 4.6, 10.1, 19.2, 27.1]; ticks = [16.2, 17.2, 18.2]
    return pops, chimes, ticks

# ---------------- AUDIO ----------------
def audio(path, dur, pops, chimes, ticks=(), bpm=120, seed=1):
    sr = 44100; n = int(dur * sr); a = np.zeros(n)
    def note(f, st, ln, vol=0.18):
        i0 = int(st * sr); m = min(int(ln * sr), n - i0)
        if m <= 0: return
        tt = np.arange(m) / sr
        w = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)
        a[i0:i0 + m] += vol * w * np.minimum(1, tt / 0.01) * np.exp(-tt * 5)
    b = 60 / bpm
    rng = random.Random(seed)
    scale = [523, 587, 659, 784, 880, 1047]
    mel = [rng.choice(scale) for _ in range(16)]
    bass = [131, 131, 175, 175, 196, 196, 131, 131]
    k = 0; t = 0.0
    while t < dur - 0.5:
        note(mel[k % 16], t, b * 0.9, 0.09)
        if k % 2 == 0: note(bass[(k // 2) % 8], t, b * 1.8, 0.15)
        k += 1; t += b
    for p in pops: note(1000, p, 0.12, 0.15)
    for c in chimes:
        for j, f in enumerate([1047, 1319, 1568]): note(f, c + j * 0.06, 0.6, 0.14)
    for tk in ticks: note(660, tk, 0.15, 0.17)
    a = np.tanh(a * 1.2) * 0.8
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

def render(frame_fn, dur, out, apath):
    tmp = out + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", apath,
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for fi in range(int(dur * FPS)):
        p.stdin.write(frame_fn(fi / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out); print("ok", out, dur)

if __name__ == "__main__":
    kind, out = sys.argv[1], sys.argv[2]
    if kind == "seequivoca2":
        RONDAS[:] = RONDAS2; HOST = os.environ.get("MASCOTA", "gato"); kind = "seequivoca"
    if kind == "animales2":
        ANIMALES[:] = ANIMALES2; kind = "animales"
    preview = len(sys.argv) > 3 and sys.argv[3] == "preview"
    if kind == "colores":
        fn, dur = colores_frame, C_INTRO + len(COLORES) * C_EACH + C_END
        pts = [1.5, C_INTRO + 2.2, C_INTRO + 2 * C_EACH + 2.2, dur - 0.5]
    elif kind == "aventura":
        fn, dur = aventura_frame, AV_INTRO + len(AVENTURA["pasos"]) * AV_EACH + AV_END
        pts = [1.8, AV_INTRO + 2.5, AV_INTRO + 5.2, AV_INTRO + AV_EACH + 5.2, AV_INTRO + 2 * AV_EACH + 2.5, dur - 1.0]
    elif kind == "intruso":
        fn, dur = intruso_frame, IN_INTRO + len(INTRUSO["rondas"]) * IN_EACH + IN_END
        pts = [1.8, IN_INTRO + 2.5, IN_INTRO + IN_EACH + 5.0, IN_INTRO + 2 * IN_EACH + 2.5, IN_INTRO + 3 * IN_EACH + 5.0, dur - 1.0]
    elif kind == "laberinto":
        fn, dur = laberinto_frame, lab_dur()
        pts = [1.8, LB_INTRO + 2.0, LB_INTRO + 6.5, LB_INTRO + 12.0, LB_INTRO + 19.0, dur - 1.0]
    elif kind == "movete":
        fn, dur = movete_frame, MV_INTRO + len(MOVETE["pasos"]) * MV_EACH + MV_FREEZE + MV_END
        pts = [1.8, MV_INTRO + 0.2, MV_INTRO + MV_EACH + 1.0, MV_INTRO + 2 * MV_EACH + 0.2, MV_INTRO + 3 * MV_EACH + 1.0, MV_INTRO + 5 * MV_EACH + 1.5]
    elif kind == "cuento":
        fn, dur = cuento_frame, CU_DUR
        pts = [3.5, 8.5, 13.8, 17.0, 20.6, 24.0, 29.0]
    elif kind in VOCAB:
        VSET = VOCAB[kind]
        fn, dur = vocab_frame, V_INTRO + len(VSET["items"]) * V_EACH + V_END
        pts = [1.8, V_INTRO + 1.0, V_INTRO + 2 * V_EACH + 2.0, V_INTRO + 4 * V_EACH + 3.3, dur - 0.6]
    elif kind in ("pipo", "seequivoca"):
        fn, dur = pipo_frame, P_INTRO + len(RONDAS) * P_EACH + P_END
        pts = [1.8, P_INTRO + 1.8, P_INTRO + 3.6, P_INTRO + 5.6, dur - 1.0]
    elif kind == "animales":
        fn, dur = animales_frame, A_INTRO + len(ANIMALES) * A_EACH + A_END
        pts = [1.5, A_INTRO + 1.8, A_INTRO + 3 * A_EACH + 4.3, A_INTRO + 4 * A_EACH + 4.3, dur - 0.5]
    else:
        fn, dur = calculo_frame, M_INTRO + len(PROBLEMAS) * M_EACH + M_END
        pts = [1.5, M_INTRO + 2.0, M_INTRO + 3 * M_EACH + 6.2, dur - 0.5]
    if preview:
        ims = [fn(s).resize((270, 480)) for s in pts]
        c = Image.new("RGB", (270 * len(ims), 480)); [c.paste(im, (i * 270, 0)) for i, im in enumerate(ims)]
        c.save(f"preview_{kind}.jpg"); sys.exit()
    ap = f"/tmp/{kind}.wav"
    if kind == "colores":
        pops, chimes = colores_beats(); audio(ap, dur, pops, chimes, seed=3)
    elif kind == "aventura":
        pops, chimes, ticks = aventura_beats(); audio(ap, dur, pops, chimes, ticks, bpm=124, seed=31)
    elif kind == "intruso":
        pops, chimes, ticks = intruso_beats(); audio(ap, dur, pops, chimes, ticks, bpm=128, seed=41)
    elif kind == "laberinto":
        pops, chimes, ticks = laberinto_beats(); audio(ap, dur, pops, chimes, ticks, bpm=116, seed=51)
    elif kind == "movete":
        pops, chimes, ticks = movete_beats(); audio(ap, dur, pops, chimes, ticks, bpm=120, seed=61)
    elif kind == "cuento":
        pops, chimes, ticks = cuento_beats(); audio(ap, dur, pops, chimes, ticks, bpm=104, seed=71)
    elif kind in VOCAB:
        pops, chimes = vocab_beats(); audio(ap, dur, pops, chimes, bpm=118, seed=len(kind) * 7)
    elif kind in ("pipo", "seequivoca"):
        pops, chimes, ticks = pipo_beats(); audio(ap, dur, pops, chimes, ticks, bpm=115, seed=21)
    elif kind == "animales":
        pops, chimes, ticks = animales_beats(); audio(ap, dur, pops, chimes, ticks, bpm=110, seed=11)
    else:
        pops, chimes, ticks = calculo_beats(); audio(ap, dur, pops, chimes, ticks, bpm=130, seed=7)
    render(fn, dur, out, ap)
