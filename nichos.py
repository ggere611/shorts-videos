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

def paste_mascota(im, cx, cy, size, t, mood="alentando", talk=False, char=None, jump=False):
    char = char or HOST
    if talk:
        mood = "hablando" if int(t * 6) % 2 == 0 else "alentando"
    blink = (t % 3.2) < 0.13 and mood != "festejando"
    m = mascota_img(char, mood, blink)
    sq = 1 + 0.03 * math.sin(t * 6)
    hop = abs(math.sin(t * 7)) * 60 if jump else 6 * math.sin(t * 3)
    w, h = int(size * (2 - sq)), int(size * sq)
    if w < 4: return
    mm = m.resize((w, h), Image.LANCZOS)
    im.paste(mm, (int(cx - w / 2), int(cy - h / 2 - hop)), mm)

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
    if kind == "animales2":
        ANIMALES[:] = ANIMALES2; kind = "animales"
    preview = len(sys.argv) > 3 and sys.argv[3] == "preview"
    if kind == "colores":
        fn, dur = colores_frame, C_INTRO + len(COLORES) * C_EACH + C_END
        pts = [1.5, C_INTRO + 2.2, C_INTRO + 2 * C_EACH + 2.2, dur - 0.5]
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
    elif kind in ("pipo", "seequivoca"):
        pops, chimes, ticks = pipo_beats(); audio(ap, dur, pops, chimes, ticks, bpm=115, seed=21)
    elif kind == "animales":
        pops, chimes, ticks = animales_beats(); audio(ap, dur, pops, chimes, ticks, bpm=110, seed=11)
    else:
        pops, chimes, ticks = calculo_beats(); audio(ap, dur, pops, chimes, ticks, bpm=130, seed=7)
    render(fn, dur, out, ap)
