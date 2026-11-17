import subprocess, math, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from nichos import paste_mascota, paste_emoji
except Exception:
    paste_mascota = paste_emoji = None
TABLE = int(sys.argv[1]) if len(sys.argv) > 1 else 2
# Variación real entre videos (para que no parezcan una plantilla repetida):
# cada tabla tiene su mascota, su objeto, su pregunta-desafío y su música.
VARIANTES = {6: ("monstruo", "🍎"), 7: ("toro", "⭐"), 8: ("rana", "⚽"), 9: ("gato", "🍩"), 10: ("oso", "🎈"),
             2: ("carpincho", "🍊"), 3: ("rana", "🍓"), 4: ("gato", "🐟"), 5: ("oso", "🍯")}
MASCOTA = os.environ.get("MASCOTA", VARIANTES.get(TABLE, ("monstruo", "⭐"))[0])
OBJETO = VARIANTES.get(TABLE, ("monstruo", "⭐"))[1]
Q = (TABLE * 3) % 5 + 5  # factor del desafío: cambia en cada tabla
OUT = sys.argv[2] if len(sys.argv) > 2 else f"tabla_{TABLE}.mp4"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(s): return ImageFont.truetype(BOLD, s)

T_INTRO, T_EQ, T_QUIZ, T_END = 2.5, 2.6, 5.0, 3.5
DUR = T_INTRO + 10 * T_EQ + T_QUIZ + T_END
NF = int(DUR * FPS)

BGS = [(255, 214, 102), (129, 212, 250), (165, 214, 167), (244, 143, 177), (206, 147, 216),
       (255, 171, 145), (128, 222, 234), (197, 225, 165), (255, 224, 130), (179, 157, 219)]
DOTS = [(229, 57, 53), (30, 136, 229), (67, 160, 71), (251, 140, 0), (142, 36, 170), (0, 172, 193)]

def ease_back(t):
    t = max(0, min(1, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def text_c(d, xy, s, size, fill, outline=(40, 40, 60), sw=10, scale=1.0):
    if scale <= 0.01: return
    f = F(max(1, int(size * scale)))
    wpx = d.textbbox((0, 0), s, font=f, stroke_width=max(1, int(sw * scale)))[2]
    if wpx > W - 120:  # que nunca se salga de pantalla (ej. tabla del 10)
        scale *= (W - 120) / wpx
        f = F(max(1, int(size * scale)))
    d.text(xy, s, font=f, fill=fill, anchor="mm", stroke_width=max(1, int(sw * scale)), stroke_fill=outline)

def bg(d, color, t):
    d.rectangle([0, 0, W, H], fill=color)
    # floating soft circles
    for i in range(8):
        x = (i * 173 + t * 40 * (1 + i % 3)) % (W + 200) - 100
        y = (i * 311 + 120 * math.sin(t * 0.8 + i)) % H
        r = 60 + 25 * (i % 4)
        c = tuple(min(255, v + 30) for v in color)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)

def frame(fi):
    t = fi / FPS
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    if t < T_INTRO:
        if t < 1.5:  # gancho: la pregunta del desafío, antes que el título
            bg(d, (142, 91, 217), t)
            text_c(d, (W/2, 430), "¿Cuánto es", 120, (255, 255, 255), scale=ease_back(t / 0.25))
            text_c(d, (W/2, 700), f"{TABLE} × {Q}?", 260, (255, 235, 59), scale=ease_back((t - 0.1) / 0.3) * (1 + 0.04 * math.sin(t * 10)))
            if paste_mascota: paste_mascota(im, W/2, 1250, 620, t, talk=True, char=MASCOTA)
            text_c(d, (W/2, 1700), "Pensalo… ¡al final la respuesta!", 58, (255, 255, 255), (40, 40, 60), 6, scale=ease_back((t - 0.5) / 0.3))
            return im
        t = t - 1.5
        bg(d, (255, 214, 102), t)
        s = ease_back(t / 0.3)
        wob = 1 + 0.04 * math.sin(t * 8)
        text_c(d, (W/2, 760), "¡TABLA", 190, (255, 255, 255), scale=s * wob)
        text_c(d, (W/2, 980), f"DEL {TABLE}!", 230, (229, 57, 53), (255, 255, 255), 14, scale=ease_back((t - 0.15) / 0.3) * wob)
        text_c(d, (W/2, 1300), "¡Aprendé jugando!", 80, (40, 40, 60), (255, 255, 255), 6, scale=ease_back((t - 0.4) / 0.3))
        if paste_mascota: paste_mascota(im, W/2, 1620, 480, t, talk=True, char=MASCOTA)
        return im
    t2 = t - T_INTRO
    if t2 < 10 * T_EQ:
        n = int(t2 // T_EQ) + 1; lt = t2 - (n - 1) * T_EQ
        bg(d, BGS[n - 1], t)
        # progress bar
        d.rounded_rectangle([90, 120, W - 90, 160], 20, fill=(255, 255, 255))
        d.rounded_rectangle([90, 120, 90 + (W - 180) * (n - 1 + min(lt / T_EQ, 1)) / 10, 160], 20, fill=(40, 40, 60))
        text_c(d, (W/2, 380), f"{TABLE} × {n}", 220 if len(f"{TABLE}{n}") <= 3 else 180, (255, 255, 255), scale=ease_back(lt / 0.35))
        # groups: n groups of TABLE dots
        cols = 5 if n > 4 else n
        rows = math.ceil(n / cols)
        drows = math.ceil(TABLE / 2); sp = 75 if drows <= 2 else 56; rad = 30 if drows <= 2 else 21
        gw, gh = 180, 34 + sp * drows
        top = 640 + (2 - rows) * gh * 0.5 - (40 if drows > 3 else 0)
        appear = 1.0
        for g in range(n):
            r_, c_ = divmod(g, cols)
            rowcount = min(cols, n - r_ * cols)
            x0 = W/2 - rowcount * (gw + 16) / 2 + c_ * (gw + 16)
            y0 = top + r_ * (gh + 30)
            gs = ease_back((lt - 0.3 - g * appear / n) / 0.25)
            if gs <= 0: continue
            cx, cy = x0 + gw/2, y0 + gh/2
            hw, hh = gw/2 * gs, gh/2 * gs
            d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], int(30 * gs), fill=(255, 255, 255), outline=(40, 40, 60), width=6)
            col = DOTS[(n - 1) % len(DOTS)]
            for k in range(TABLE):
                kr, kc = divmod(k, 2)
                per = min(2, TABLE - kr * 2)
                dx = (kc - (per - 1) / 2) * sp * gs
                dy = (kr - (drows - 1) / 2) * sp * gs
                rr = rad * gs
                if paste_emoji: paste_emoji(im, OBJETO, cx + dx, cy + dy, int(rad * 2.3), gs)
                else: d.ellipse([cx + dx - rr, cy + dy - rr, cx + dx + rr, cy + dy + rr], fill=col, outline=(40, 40, 60), width=4)
        rs = ease_back((lt - 1.5) / 0.35)
        if rs > 0:
            pulse = 1 + 0.06 * math.sin((lt - 1.5) * 12) * max(0, 1 - (lt - 1.5))
            text_c(d, (W/2, 1450), f"= {TABLE * n}", 300 if TABLE * n < 100 else 240, (255, 255, 255), (40, 40, 60), 14, scale=rs * pulse)
        if paste_mascota:
            if rs > 0: paste_mascota(im, 190, 1730, 280, t, mood="festejando", char=MASCOTA, jump=True)
            else: paste_mascota(im, 190, 1730, 280, t, talk=True, char=MASCOTA)
        return im
    lt = t2 - 10 * T_EQ
    if lt < T_QUIZ:
        bg(d, (255, 138, 101), t)
        text_c(d, (W/2, 420), "¡DESAFÍO!", 150, (255, 235, 59), scale=ease_back(lt / 0.4) * (1 + 0.05 * math.sin(t * 10)))
        text_c(d, (W/2, 780), f"¿{TABLE} × {Q}?", 230, (255, 255, 255), scale=ease_back((lt - 0.3) / 0.4))
        if lt < 3.6:
            k = 3 - int((lt - 0.6) // 1) if lt >= 0.6 else 3
            k = max(1, min(3, k)); ph = ((lt - 0.6) % 1) if lt >= 0.6 else 0
            r = 150 * ease_back(min(1, ph / 0.3))
            d.ellipse([W/2 - r, 1250 - r, W/2 + r, 1250 + r], fill=(255, 255, 255), outline=(40, 40, 60), width=10)
            text_c(d, (W/2, 1250), str(k), 200, (229, 57, 53), (255, 255, 255), 4, scale=ease_back(min(1, ph / 0.3)))
        else:
            text_c(d, (W/2, 1250), f"= {TABLE * Q}", 280, (255, 255, 255), scale=ease_back((lt - 3.6) / 0.35))
            text_c(d, (W/2, 1550), "¿Acertaste? 🎉".replace(" 🎉", ""), 90, (40, 40, 60), (255, 255, 255), 6, scale=ease_back((lt - 3.9) / 0.4))
        return im
    lt -= T_QUIZ
    bg(d, (129, 212, 250), t)
    text_c(d, (W/2, 700), "¡MUY BIEN!", 145, (255, 255, 255), scale=ease_back(lt / 0.5))
    text_c(d, (W/2, 1000), "Suscribite para", 90, (40, 40, 60), (255, 255, 255), 6, scale=ease_back((lt - 0.5) / 0.5))
    text_c(d, (W/2, 1130), f"la tabla del {TABLE + 1}", 110, (229, 57, 53), (255, 255, 255), 8, scale=ease_back((lt - 0.7) / 0.5))
    s = ease_back((lt - 1.2) / 0.5)
    if s > 0:
        bw, bh = 560 * s, 150 * s
        d.rounded_rectangle([W/2 - bw/2, 1400 - bh/2, W/2 + bw/2, 1400 + bh/2], int(40 * s), fill=(229, 57, 53), outline=(255, 255, 255), width=8)
        text_c(d, (W/2, 1400), "SUSCRIBIRME", 72, (255, 255, 255), (229, 57, 53), 2, scale=s)
    if paste_mascota: paste_mascota(im, W/2, 1680, 420, t, mood="festejando", char=MASCOTA, jump=True)
    return im

def audio(path):
    sr = 44100; n = int(DUR * sr); a = np.zeros(n)
    def note(f, st, ln, vol=0.18, kind="sq"):
        i0 = int(st * sr); m = min(int(ln * sr), n - i0)
        if m <= 0: return
        tt = np.arange(m) / sr
        w = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)
        env = np.minimum(1, tt / 0.01) * np.exp(-tt * 5)
        a[i0:i0 + m] += vol * w * env
    import random
    rng = random.Random(TABLE * 13)
    bpm = 108 + (TABLE * 7) % 24; b = 60 / bpm
    esc = [523, 587, 659, 784, 880, 1047]
    mel = [rng.choice(esc) for _ in range(16)]
    bass = [131, 131, 175, 175, 131, 131, 196, 196]
    k = 0; tt = 0.0
    while tt < DUR - 0.5:
        note(mel[k % 16], tt, b * 0.9, 0.10)
        if k % 2 == 0: note(bass[(k // 2) % 8], tt, b * 1.8, 0.16)
        k += 1; tt += b
    # pops and chimes
    for nn in range(1, 11):
        st = T_INTRO + (nn - 1) * T_EQ
        for g in range(nn): note(900 + 60 * g, st + 0.3 + g / nn, 0.12, 0.15)
        for j, f in enumerate([1047, 1319, 1568]): note(f, st + 1.5 + j * 0.06, 0.6, 0.14)
    q0 = T_INTRO + 10 * T_EQ
    for j in range(3): note(660, q0 + 0.6 + j, 0.25, 0.2)
    for j, f in enumerate([784, 988, 1175, 1568]): note(f, q0 + 3.6 + j * 0.08, 0.7, 0.16)
    a = np.tanh(a * 1.2) * 0.8
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3] == "preview":
        for s in [0.9, 2.2, T_INTRO + 9 * T_EQ + 2.2, T_INTRO + 10 * T_EQ + 1.0, T_INTRO + 10 * T_EQ + 4.5, DUR - 0.5]:
            frame(int(s * FPS)).save(f"prev_{s:.1f}.jpg", quality=85)
        sys.exit()
    audio("music.wav")
    tmp = OUT + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "music.wav",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp],
                         stdin=subprocess.PIPE)
    for fi in range(NF):
        p.stdin.write(frame(fi).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, OUT); print("ok", OUT, DUR); print(f"DESAFIO: {TABLE} x {Q} = {TABLE * Q} | MASCOTA: {MASCOTA}")
