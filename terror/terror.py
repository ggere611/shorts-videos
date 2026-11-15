"""Leyendas argentinas — short de terror (sin gore).
Uso: python3 terror.py salida.mp4 [preview]
"""
import math, os, subprocess, sys, wave, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
rng = random.Random(7)
_f = {}
def F(s, serif=False):
    k = (s, serif)
    if k not in _f: _f[k] = ImageFont.truetype(SERIF if serif else BOLD, s)
    return _f[k]

# (inicio, fin, texto, palabra destacada)
GUION = [
    (0.3, 3.4, "Si ves una luz en el campo…", None),
    (3.4, 6.6, "NO la sigas.", "NO"),
    (6.6, 11.5, "En el campo argentino la llaman la LUZ MALA.", "LUZ MALA"),
    (11.5, 17.0, "Aparece de noche, flotando en medio de la nada.", None),
    (17.0, 23.0, "Los viejos dicen que marca el lugar donde hay un muerto enterrado…", None),
    (23.0, 28.0, "…o un tesoro maldito.", "maldito"),
    (28.0, 34.5, "Si la seguís, te aleja cada vez más del camino.", None),
    (34.5, 40.5, "Y cuando te das vuelta…", None),
    (42.6, 47.0, "…ya no sabés volver.", None),
    (47.0, 53.0, "¿Vos la viste alguna vez?", None),
]
DUR = 53.0
SCARE = 40.6

def lerp(a, b, t): return a + (b - a) * max(0, min(1, t))
def smooth(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)

# ---------- capas fijas ----------
def make_sky():
    Wb, Hb = int(W * 1.25), int(H * 1.25)
    y = np.linspace(0, 1, Hb)[:, None]
    top, bot = np.array([6, 8, 22]), np.array([28, 26, 52])
    g = (top + (bot - top) * y ** 1.4)
    img = np.repeat(g[:, None, :], Wb, axis=1).reshape(Hb, Wb, 3)
    sky = Image.fromarray(img.astype(np.uint8))
    d = ImageDraw.Draw(sky)
    for _ in range(420):
        x, yy = rng.randint(0, Wb), rng.randint(0, int(Hb * 0.62))
        b = rng.randint(90, 230); r = rng.choice([1, 1, 1, 2])
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=(b, b, min(255, b + 20)))
    # luna con halo
    mx, my = int(Wb * 0.76), int(Hb * 0.16)
    halo = Image.new("L", (Wb, Hb), 0); hd = ImageDraw.Draw(halo)
    for r in range(260, 90, -10): hd.ellipse([mx - r, my - r, mx + r, my + r], fill=int(40 * (1 - (r - 90) / 170)))
    sky = Image.composite(Image.new("RGB", (Wb, Hb), (120, 130, 170)), sky, halo.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(sky)
    d.ellipse([mx - 85, my - 85, mx + 85, my + 85], fill=(222, 222, 205))
    d.ellipse([mx - 50, my - 95, mx + 120, my + 75], fill=tuple(int(c) for c in g[my]))  # luna menguante
    return sky

def make_ground():
    Wb, Hb = int(W * 1.25), int(H * 1.25)
    g = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    hz = int(Hb * 0.64)
    pts = [(0, Hb)]
    for x in range(0, Wb + 40, 40):
        pts.append((x, hz + 18 * math.sin(x / 210) + 10 * math.sin(x / 63)))
    pts.append((Wb, Hb)); d.polygon(pts, fill=(4, 6, 10, 255))
    # pasto en primer plano
    for _ in range(900):
        x = rng.randint(0, Wb); y0 = rng.randint(int(Hb * 0.80), Hb); h = rng.randint(25, 90)
        d.line([x, y0, x + rng.randint(-14, 14), y0 - h], fill=(2, 3, 6, 255), width=3)
    # alambrado
    for i in range(9):
        x = 60 + i * 150; top = hz + 60 + i * 14
        d.line([x, top, x - 6, top + 130], fill=(10, 10, 14, 255), width=9)
    for k in range(3):
        d.line([0, hz + 90 + k * 34, Wb, hz + 205 + k * 34], fill=(12, 12, 16, 255), width=2)
    # ombú / árbol solitario y molino
    tx, ty = int(Wb * 0.22), hz + 8
    d.rectangle([tx - 14, ty - 180, tx + 14, ty], fill=(4, 6, 10, 255))
    for _ in range(70):
        cx, cy = tx + rng.randint(-170, 170), ty - 230 + rng.randint(-90, 70); r = rng.randint(40, 80)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(4, 6, 10, 255))
    mx = int(Wb * 0.80)
    d.line([mx - 60, hz + 10, mx, hz - 330], fill=(4, 6, 10, 255), width=10)
    d.line([mx + 60, hz + 10, mx, hz - 330], fill=(4, 6, 10, 255), width=10)
    for a in range(0, 360, 30):
        r = math.radians(a)
        d.line([mx, hz - 340, mx + 110 * math.cos(r), hz - 340 + 110 * math.sin(r)], fill=(4, 6, 10, 255), width=6)
    return g

def make_fog(seed):
    r = random.Random(seed)
    fog = Image.new("L", (W * 2, 700), 0); d = ImageDraw.Draw(fog)
    for _ in range(60):
        x, y = r.randint(0, W * 2), r.randint(150, 600); rx, ry = r.randint(150, 400), r.randint(40, 110)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=r.randint(25, 60))
    return fog.filter(ImageFilter.GaussianBlur(45))

def make_glow(size):
    y, x = np.mgrid[-1:1:complex(size), -1:1:complex(size)]
    r = np.sqrt(x * x + y * y)
    a = np.clip(1 - r, 0, 1) ** 2.2
    core = np.clip(1 - r * 5, 0, 1)
    rgb = np.zeros((size, size, 3))
    rgb[..., 0] = 255 * np.clip(a * 1.0 + core, 0, 1)
    rgb[..., 1] = 255 * np.clip(a * 0.85 + core, 0, 1)
    rgb[..., 2] = 255 * np.clip(a * 0.45 + core, 0, 1)
    al = np.clip(a * 1.3 + core, 0, 1) * 255
    return Image.fromarray(np.dstack([rgb, al]).astype(np.uint8), "RGBA")

SKY, GROUND = make_sky(), make_ground()
FOG1, FOG2 = make_fog(1), make_fog(2)
GLOW = make_glow(600)

def luz_pos(t):
    """Posición y tamaño de la luz (en coords de pantalla)."""
    if t < 11.5: return None
    if t < 28: return (W * 0.58 + 40 * math.sin(t * 0.7), H * 0.60 + 18 * math.sin(t * 1.3), 120 + 6 * math.sin(t * 5))
    if t < 34.5:
        k = (t - 28) / 6.5
        return (lerp(W * 0.58, W * 0.30, smooth(k)) + 30 * math.sin(t), H * 0.60 - 40 * smooth(k), lerp(120, 70, k))
    if t < SCARE: return None  # se fue
    if t < SCARE + 2.2:
        k = (t - SCARE) / 0.35
        return (W / 2, H * 0.46, lerp(250, 2300, smooth(k)))
    if t < 47: return (W / 2 + 25 * math.sin(t * 3), H * 0.50, 520 + 30 * math.sin(t * 6))
    return (W * 0.55 + 30 * math.sin(t), H * 0.60, 140)

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.getlength(test) <= maxw: cur = test
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def caption(d, t):
    for a, b, txt, hl in GUION:
        if a <= t < b:
            fade = min(1, (t - a) / 0.35, (b - t) / 0.35)
            if fade <= 0: return
            size = 92 if len(txt) < 30 else 76
            font = F(size)
            lines = wrap(txt, font, W - 140)
            y0 = int(H * 0.74) - (len(lines) - 1) * size // 2
            for i, ln in enumerate(lines):
                x = (W - font.getlength(ln)) / 2; y = y0 + i * int(size * 1.18)
                for wd in ln.split(" "):
                    is_hl = hl and any(h.strip("…") in wd for h in hl.split())
                    col = (255, 70, 60) if is_hl else (240, 240, 235)
                    c = tuple(int(v * fade) for v in col)
                    d.text((x, y), wd, font=font, fill=c, stroke_width=8, stroke_fill=(0, 0, 0))
                    x += font.getlength(wd + " ")
            return

def frame(t):
    # cámara: zoom lento + paneo
    z = 1.0 + 0.10 * (t / DUR)
    if 28 <= t < 34.5: px = -60 * smooth((t - 28) / 6.5)
    else: px = 0 if t < 28 else -60
    if 34.5 <= t < SCARE: px += 160 * smooth((t - 34.5) / 5)  # "te das vuelta"
    elif t >= SCARE: px += 160
    shake = (rng.uniform(-14, 14), rng.uniform(-14, 14)) if SCARE <= t < SCARE + 0.6 else (0, 0)
    Wb, Hb = SKY.size
    cw, ch = W / z, H / z
    cx = Wb / 2 + px + shake[0]; cy = Hb / 2 + shake[1]
    box = (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
    im = SKY.crop(box).resize((W, H), Image.BILINEAR)
    # parallax: el suelo se mueve un poco más
    gbox = (int(cx - cw / 2 + px * 0.5), int(cy - ch / 2), int(cx + cw / 2 + px * 0.5), int(cy + ch / 2))
    gr = GROUND.crop(gbox).resize((W, H), Image.BILINEAR)
    lp = luz_pos(t)
    if lp and lp[2] < 900:  # luz detrás del primer plano
        add_glow(im, lp, t)
    im.paste(gr, (0, 0), gr)
    for fog, sp, yy in ((FOG1, 18, int(H * 0.55)), (FOG2, -11, int(H * 0.70))):
        off = int((t * sp) % W)
        strip = fog.crop((off, 0, off + W, fog.size[1]))
        im.paste(Image.new("RGB", (W, strip.size[1]), (150, 155, 175)), (0, yy), strip)
    if lp and lp[2] >= 900:
        add_glow(im, lp, t)
    # viñeta
    im = ImageChops.multiply(im, VIGNETTE)
    d = ImageDraw.Draw(im)
    if SCARE - 0.15 <= t < SCARE:  # silencio en negro antes del susto
        d.rectangle([0, 0, W, H], fill=(0, 0, 0))
    if SCARE <= t < SCARE + 0.12:
        d.rectangle([0, 0, W, H], fill=(255, 250, 230))
    caption(d, t)
    if t >= 47:
        k = smooth((t - 47) / 0.6)
        d.text((W / 2, 300), "LEYENDAS", font=F(int(110 * k) or 1, True), fill=(255, 70, 60), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
        d.text((W / 2, 420), "ARGENTINAS #1", font=F(int(78 * k) or 1, True), fill=(235, 235, 225), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
        d.text((W / 2, H * 0.86), "Contalo en los comentarios", font=F(60), fill=(200, 200, 200), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    if t < 0.4:
        im = Image.blend(Image.new("RGB", (W, H)), im, t / 0.4)
    return im

def add_glow(im, lp, t):
    x, y, s = lp
    flick = 1 + 0.08 * math.sin(t * 23) + 0.05 * math.sin(t * 37)
    s = int(s * 2.4 * flick)
    if s < 8: return
    g = GLOW.resize((s, s), Image.BILINEAR)
    layer = Image.new("RGB", (W, H)); mask = Image.new("L", (W, H))
    layer.paste(g.convert("RGB"), (int(x - s / 2), int(y - s / 2)))
    mask.paste(g.split()[-1], (int(x - s / 2), int(y - s / 2)))
    im.paste(ImageChops.screen(im, layer), (0, 0), mask)

def make_vignette():
    y, x = np.mgrid[-1:1:complex(H), -1:1:complex(W)]
    r = np.sqrt((x * 0.9) ** 2 + (y * 0.75) ** 2)
    v = np.clip(1.25 - r * 0.75, 0.25, 1) * 255
    return Image.fromarray(np.dstack([v, v, v]).astype(np.uint8))
VIGNETTE = make_vignette()

# ---------- audio ----------
def audio(path):
    sr = 44100; n = int(DUR * sr); t = np.arange(n) / sr
    r = np.random.default_rng(3)
    noise = r.standard_normal(n)
    k = 400; wind = np.convolve(noise, np.ones(k) / k, mode="same")
    wind = wind / (np.abs(wind).max() + 1e-9) * (0.25 + 0.15 * np.sin(2 * np.pi * 0.11 * t) + 0.1 * np.sin(2 * np.pi * 0.37 * t))
    drone = 0.10 * np.sin(2 * np.pi * 55 * t) + 0.07 * np.sin(2 * np.pi * 55.7 * t) + 0.05 * np.sin(2 * np.pi * 82.4 * t)
    a = wind * 0.9 + drone * np.clip(t / 6, 0, 1)
    # tono de la luz
    eerie = 0.035 * np.sin(2 * np.pi * (880 + 12 * np.sin(2 * np.pi * 5 * t)) * t)
    luz = ((t > 11.5) & (t < 34.5)) | ((t > SCARE) & (t < 47))
    a += eerie * luz
    # latidos
    for b in np.arange(34.6, SCARE - 0.3, 0.75):
        for off, amp in ((0, 0.55), (0.18, 0.35)):
            i0 = int((b + off) * sr); m = int(0.16 * sr); tt = np.arange(m) / sr
            a[i0:i0 + m] += amp * np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 28)
    # silencio antes del susto
    i1, i2 = int((SCARE - 0.4) * sr), int(SCARE * sr)
    a[i1:i2] *= np.linspace(1, 0.02, i2 - i1)
    # golpe del susto
    i0 = int(SCARE * sr); m = int(1.6 * sr); tt = np.arange(m) / sr
    hit = 0.9 * r.standard_normal(m) * np.exp(-tt * 6) + 0.9 * np.sin(2 * np.pi * 40 * tt) * np.exp(-tt * 2.5)
    hit += 0.3 * np.sin(2 * np.pi * (1200 - 600 * tt) * tt) * np.exp(-tt * 3)
    a[i0:i0 + m] += hit[: n - i0]
    a = np.tanh(a * 1.1) * 0.85
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        pts = [1.5, 8.0, 14.0, 31.0, 37.0, SCARE + 0.25, 44.0, 50.0]
        ims = [frame(s).resize((270, 480)) for s in pts]
        c = Image.new("RGB", (270 * 4, 960))
        for i, im in enumerate(ims): c.paste(im, ((i % 4) * 270, (i // 4) * 480))
        c.save("preview_terror.jpg"); sys.exit()
    audio("/tmp/terror.wav")
    tmp = out + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", "/tmp/terror.wav", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
                          "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for fi in range(int(DUR * FPS)):
        p.stdin.write(frame(fi / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out); print("ok", out)
