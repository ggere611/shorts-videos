"""Serie de aventuras entre las mascotas (3D) con narrador.
Uso: python3 episodios.py <linterna|globo|ruido> salida.mp4 [preview]
Cada episodio es una lista de escenas: texto del narrador + actores + objetos.
"""
import math, os, sys, wave
os.environ.setdefault("MASC_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mascotas3d"))
import numpy as np
from PIL import Image, ImageDraw
import nichos as N
import cuentos as Q
from nichos import W, H, INK, text_c, ease_back, paste_emoji, CORAL
from cuentos import BASE, actor, salto, camina, lerp, narrador

def mira(m): return "alentando" if m == "c" else f"act_{m}"

def estado(spec, lt, t, vd):
    """-> (sprite, x, dy, sy, ang) o None si todavía no entró."""
    char, x, acc, o = spec
    m = o.get("m", "c"); d = o.get("d", 0)
    if "luego" in o and lt >= o["luego"][0]:
        o2 = {k: v for k, v in o.items() if k not in ("luego", "d")}
        return estado((char, x, o["luego"][1], o2), lt - o["luego"][0], t, vd)
    if lt < d:
        return None if acc.startswith("entra") else (mira(m), x, 0, 1, 0)
    a = lt - d
    if acc.startswith("entra"):
        izq = acc.endswith("_i"); x0 = -260 if izq else W + 260; k = a / 1.3
        if k >= 1: return (mira(m), x, 0, 1, 0)
        xx = lerp(x0, x, k)
        if "salto" in acc: dy, sy = salto(a, 0.45, 110); return ("act_der" if izq else "act_izq", xx, dy, sy, 0)
        dy, sy, ang = camina(t); return ("act_der" if izq else "act_izq", xx, dy, sy, ang)
    if acc.startswith("sale"):
        izq = acc.endswith("_i"); dy, sy, ang = camina(t)
        return ("act_izq" if izq else "act_der", x + (-1 if izq else 1) * a * 420, dy, sy, ang)
    if acc == "salta": dy, sy = salto(a + o.get("f", 0), 0.8, 110); return ("festejando", x, dy, sy, 0)
    if acc == "sorpresa": return ("act_sorpresa", x, 70 * math.sin(min(1, a / 0.35) * math.pi), 1.04 if a < 0.35 else 1, 0)
    if acc == "triste": return ("act_triste", x, 0, 0.95, 0)
    if acc == "saluda": return ("act_saluda1" if int(t * 5) % 2 else "act_saluda2", x, 0, 1, 0)
    if acc == "niega": s = 24 * math.sin(a * 13); return ("act_izq" if s < 0 else "act_der", x + s, 0, 1, 0)
    if acc == "busca": return ("act_izq" if int(a * 1.5) % 2 else "act_der", x, abs(math.sin(t * 5)) * 10, 1, 0)
    if acc == "tiembla": return ("act_sorpresa", x + 7 * math.sin(t * 42), 0, 0.97, 0)
    if acc == "camina": dy, sy, ang = camina(t); return (mira(m), x, dy, sy, ang)
    if acc == "tira": s = math.sin(a * 11); return (mira(m), x + 16 * s, 0, 1, o.get("lado", 1) * (9 + 4 * s))
    return (mira(m), x, 0, 1, 0)

def objeto(im, d, p, lt, t, est):
    em, x, h, mov, o = p; dly = o.get("d", 0); s = o.get("s", 130)
    if lt < dly or lt > o.get("hasta", 1e9): return im
    a = lt - dly; y = BASE - h; k = 1
    if mov == "flota": y += 14 * math.sin(t * 3)
    elif mov == "aparece": k = ease_back(a / 0.3)
    elif mov == "cae": y = lerp(-200, y, a / 0.5) - (40 * abs(math.sin(a * 9)) * max(0, 1 - a) if a > 0.5 else 0)
    elif mov == "sube": y -= a * 430; x += 30 * math.sin(a * 4)
    elif mov == "va": f = min(1, a / o.get("T", 1.2)); x = lerp(x, o["x2"], f); y = lerp(y, BASE - o["h2"], f) - o.get("arco", 0) * math.sin(math.pi * f)
    elif mov == "rebota":
        f = (a / o.get("T", 1.0)) % 2; f = f if f < 1 else 2 - f
        x = x + (o["x2"] - x) * f; y -= o.get("arco", 320) * math.sin(math.pi * ((a / o.get("T", 1.0)) % 1))
    elif mov == "tiembla": x += 8 * math.sin(t * 40); k = ease_back(a / 0.2)
    elif mov == "sigue":
        e = est[o["con"]]
        if e is None: return im
        x = e[1] + o.get("dx", 0); y = BASE - h - e[2] + 10 * math.sin(t * 3)
    if mov == "luz":
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); dr = o.get("dir", 1)
        if "con" in o and est[o["con"]] is not None: x = est[o["con"]][1] + o.get("dx", 0)
        L = 760 * min(1, a / 0.25)
        od.polygon([(x, y), (x + dr * L, y - 300), (x + dr * L, y + 330)], fill=(255, 236, 130, 120))
        od.ellipse([x + dr * L - 190, BASE - 20, x + dr * L + 190, BASE + 70], fill=(255, 236, 130, 90))
        im2 = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"); im.paste(im2); return im
    if em.startswith("txt:"):
        text_c(d, (x + 6 * math.sin(t * 38), y), em[4:], s, CORAL, (255, 255, 255), 8, scale=ease_back(a / 0.2)); return im
    paste_emoji(im, em, x, y, s, k); return im

def frame(C, EP, t):
    i, lt, vd = C.escena(t); b = EP["escenas"][i]
    noche = b.get("fondo") == "noche"
    im = Image.new("RGB", (W, H), (22, 28, 58) if noche else (251, 252, 254)); d = ImageDraw.Draw(im)
    if noche:
        for j in range(26):
            sx, sy_ = (j * 397) % W, 420 + (j * 211) % 800; r = 3 + (j % 3)
            if (t * 2 + j) % 3 > 0.4: d.ellipse([sx - r, sy_ - r, sx + r, sy_ + r], fill=(240, 240, 200))
    d.ellipse([-300, BASE - 70, W + 300, BASE + 1100], fill=(34, 42, 80) if noche else (241, 245, 251))
    Q.SOMBRA = (16, 20, 44) if noche else (224, 229, 238)
    acts = b.get("a", []); est = [estado(s, lt, t, vd) for s in acts]
    props = b.get("p", [])
    for p in props:
        if p[4].get("atras"): im = objeto(im, d, p, lt, t, est)
    for s, e in zip(acts, est):
        if e is None: continue
        spr, x, dy, sy, ang = e
        actor(im, d, s[0], x, t, spr, s[3].get("s", 400), dy, sy, ang)
    for p in props:
        if not p[4].get("atras"): im = objeto(im, d, p, lt, t, est)
    d = ImageDraw.Draw(im)
    narrador(d, b["t"], lt)
    if b.get("cuenta") and lt > vd:
        q = lt - vd; c = max(1, 3 - int(q)); ph = q % 1; k = ease_back(min(1, ph / 0.3))
        d.ellipse([W / 2 - 100 * k, 640 - 100 * k, W / 2 + 100 * k, 640 + 100 * k], fill=(255, 255, 255), outline=INK, width=8)
        text_c(d, (W / 2, 640), str(c), 130, (229, 57, 53), (255, 255, 255), 4, scale=k)
    if i == 0 and lt < 2.6: text_c(d, (W / 2, 1760), EP["titulo"], 64, INK if not noche else (255, 255, 255), (255, 255, 255) if not noche else INK, 4, scale=ease_back(lt / 0.4))
    if i == len(EP["escenas"]) - 1 and lt > vd: text_c(d, (W / 2, 1760), "Mañana, otra aventura", 66, INK, (255, 255, 255), 4, scale=ease_back((lt - vd) / 0.4))
    if t < 0.4: im = Image.blend(Image.new("RGB", (W, H), (255, 255, 255)), im, t / 0.4)
    return im

def audio(C, EP, path):
    Q.mezclar_audio(C, path, seed=EP.get("seed", 71))
    grr = [(C.ini[i] + g) for i, b in enumerate(EP["escenas"]) for g in b.get("grr", [])]
    if not grr: return
    w = wave.open(path); sr = w.getframerate(); n = w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768; w.close()
    m = int(sr * 0.8); tt = np.arange(m) / sr
    g = np.sign(np.sin(2 * np.pi * 62 * tt + 6 * np.sin(2 * np.pi * 23 * tt))) * 0.5 + np.sin(2 * np.pi * 45 * tt)
    g = np.convolve(g, np.ones(24) / 24, "same") * np.sin(np.pi * tt / 0.8) ** 0.6 * 0.5
    for s in grr:
        i0 = int(s * sr); k = min(m, n - i0); a[i0:i0 + k] += g[:k]
    a = np.clip(a, -1, 1)
    with wave.open(path, "wb") as o_: o_.setnchannels(1); o_.setsampwidth(2); o_.setframerate(sr); o_.writeframes((a * 32767).astype(np.int16).tobytes())

A = lambda c, x, acc="quieto", **o: (c, x, acc, o)
P = lambda em, x, h, mov="fijo", **o: (em, x, h, mov, o)

EPISODIOS = {
 "linterna": dict(titulo="La cosa misteriosa", seed=31, escenas=[
  dict(t="El Toro encontró una cosa muy rara. ¿Qué será?", pausa=0.8,
       a=[A("toro", 420, "entra_i", m="der", s=460)], p=[P("🔦", 760, 60, "fijo", s=150)]),
  dict(t="¿Será un sombrero? Mmm... no, no es un sombrero.", pausa=0.6,
       a=[A("toro", 540, "quieto", m="arriba", s=460, luego=(2.2, "niega"))], p=[P("🔦", 0, 455, "sigue", con=0, s=150)]),
  dict(t="¿Será un micrófono? ¡La, la, la! Tampoco.", pausa=0.8,
       a=[A("toro", 400, "saluda", s=440), A("gato", 800, "entra_d", m="izq", s=400, d=0.6, luego=(2.4, "salta"))],
       p=[P("🔦", 0, 250, "sigue", con=0, dx=215, s=130), P("🎵", 560, 760, "sube", d=1.4, s=110)]),
  dict(t="¡Uy! Se hizo de noche. No se ve nada de nada.", pausa=0.8, fondo="noche",
       a=[A("toro", 380, "tiembla", s=440), A("gato", 760, "tiembla", s=400)], p=[P("🔦", 570, 60, "fijo", s=130), P("🌙", 860, 1050, "aparece", s=170)]),
  dict(t="¿Y vos? ¿Sabés para qué sirve esta cosa?", pausa=3.4, cuenta=True, fondo="noche",
       a=[A("toro", 380, "busca", s=440), A("gato", 760, "quieto", m="izq", s=400)], p=[P("🔦", 570, 60, "tiembla", s=140), P("🌙", 860, 1050, s=170)]),
  dict(t="¡Clic! ¡Es una linterna! Sirve para ver en la oscuridad.", pausa=1.2, fondo="noche",
       a=[A("toro", 300, "quieto", m="der", s=440, luego=(1.6, "salta")), A("gato", 800, "sorpresa", s=400, d=0.4, luego=(1.6, "salta"))],
       p=[P("", 0, 250, "luz", con=0, dx=250, d=0.3, atras=True), P("🔦", 0, 250, "sigue", con=0, dx=215, s=130), P("🌙", 860, 1050, s=170)]),
  dict(t="Ahora sí, a casa con la luz prendida. ¡Chau, chau!", pausa=1.8, fondo="noche",
       a=[A("gato", 300, "saluda", s=380), A("toro", 620, "camina", m="der", s=420)],
       p=[P("", 0, 240, "luz", con=1, dx=240, atras=True), P("🔦", 0, 240, "sigue", con=1, dx=205, s=125), P("🏠", 980, 150, "va", x2=900, h2=150, T=3, s=260, atras=True), P("🌙", 860, 1050, s=170)]),
 ]),
 "globo": dict(titulo="Un solo globo", seed=52, escenas=[
  dict(t="El Gato tiene un globo rojo. ¡Qué lindo globo!", pausa=0.7,
       a=[A("gato", 480, "entra_i", m="arriba", s=460)], p=[P("🎈", 0, 620, "sigue", con=0, dx=210, s=230)]),
  dict(t="Llegó el Carpincho. Él también quiere jugar con el globo.", pausa=0.6,
       a=[A("gato", 330, "quieto", m="der", s=420), A("carpincho", 800, "entra_d", m="izq", s=420, luego=(2.4, "saluda"))], p=[P("🎈", 0, 620, "sigue", con=0, dx=200, s=230)]),
  dict(t="¡Es mío! ¡No, es mío! Tiran, y tiran, y tiran...", pausa=0.6,
       a=[A("gato", 320, "tira", m="der", lado=1, s=420), A("carpincho", 770, "tira", m="izq", lado=-1, s=420)], p=[P("🎈", 545, 560, "tiembla", s=230)]),
  dict(t="¡Uy! El globo se escapó. ¡Se va, se va!", pausa=1.0,
       a=[A("gato", 320, "sorpresa", s=420, luego=(0.8, "quieto"), m="arriba"), A("carpincho", 770, "sorpresa", s=420, luego=(0.8, "quieto"), m="arriba")], p=[P("🎈", 545, 560, "sube", s=230)]),
  dict(t="Ahora ninguno tiene globo. Qué tristes están.", pausa=0.9,
       a=[A("gato", 320, "triste", s=420), A("carpincho", 770, "triste", s=420)]),
  dict(t="¿Y vos? ¿Qué pueden hacer para jugar los dos?", pausa=3.4, cuenta=True,
       a=[A("gato", 320, "quieto", m="der", s=420), A("carpincho", 770, "quieto", m="izq", s=420)]),
  dict(t="¡Miren! La Rana trae otro globo. Y esta vez, juegan por turnos.", pausa=0.8,
       a=[A("gato", 190, "sorpresa", s=330, d=0.9), A("carpincho", 500, "sorpresa", s=330, d=1.0), A("rana", 860, "entra_salto_d", m="izq", s=330)],
       p=[P("🎈", 0, 520, "sigue", con=2, dx=-120, s=200)]),
  dict(t="Primero uno, después el otro. ¡Así es más divertido! ¡Chau, chau!", pausa=2.2,
       a=[A("gato", 190, "quieto", m="arriba", s=330, luego=(4.2, "saluda")), A("carpincho", 540, "quieto", m="arriba", s=330, luego=(4.2, "saluda")), A("rana", 890, "salta", s=330, luego=(4.2, "saluda"))],
       p=[P("🎈", 190, 520, "rebota", x2=540, T=1.0, arco=360, s=200)]),
 ]),
 "ruido": dict(titulo="El ruido raro", seed=88, escenas=[
  dict(t="El Monstruito juega tranquilo con sus bloques. De pronto...", pausa=1.6, grr=[3.6],
       a=[A("monstruo", 430, "quieto", m="der", s=460, luego=(3.6, "sorpresa"))], p=[P("🧱", 760, 50, s=150), P("🧱", 760, 180, "cae", d=1.2, s=150), P("txt:¡GRRR!", 540, 900, d=3.6, s=150)]),
  dict(t="¿Qué fue ese ruido? El Monstruito tiene un poquito de miedo.", pausa=0.6,
       a=[A("monstruo", 430, "tiembla", s=460)], p=[P("🧱", 760, 50, s=150), P("🧱", 760, 180, s=150), P("❓", 700, 760, "flota", s=170)]),
  dict(t="Llegó la Rana. ¡No tengas miedo! Vamos a investigar juntos.", pausa=0.6,
       a=[A("monstruo", 330, "quieto", m="der", s=420), A("rana", 780, "entra_salto_d", m="izq", s=400, luego=(2.6, "saluda"))]),
  dict(t="Buscan atrás de la piedra... y nada. ¡Otra vez el ruido!", pausa=1.2, grr=[3.4],
       a=[A("monstruo", 220, "busca", s=340, luego=(3.4, "tiembla")), A("rana", 500, "busca", s=320, luego=(3.4, "sorpresa"))],
       p=[P("🪨", 850, 110, s=330), P("txt:¡GRRR!", 540, 900, d=3.4, s=150)]),
  dict(t="¿Y vos? ¿Qué será ese ruido?", pausa=3.4, cuenta=True,
       a=[A("monstruo", 220, "quieto", m="der", s=340), A("rana", 500, "quieto", m="der", s=320)], p=[P("🪨", 850, 110, s=330), P("❓", 850, 420, "flota", s=160)]),
  dict(t="¡Era la panza del Oso! ¡Tenía muchísima hambre!", pausa=1.4, grr=[0.9],
       a=[A("monstruo", 180, "sorpresa", s=320, luego=(1.8, "salta")), A("rana", 440, "sorpresa", s=310, luego=(1.8, "salta"), f=0.3), A("oso", 800, "entra_d", m="izq", s=420, luego=(2.0, "triste"))],
       p=[P("txt:¡GRRR!", 800, 640, d=0.9, hasta=2.6, s=110)]),
  dict(t="Entonces comparten la merienda. ¡Con amigos, no hay miedo! ¡Chau, chau!", pausa=2.0,
       a=[A("monstruo", 180, "salta", s=320, luego=(3.6, "saluda")), A("rana", 540, "salta", s=310, f=0.3, luego=(3.6, "saluda")), A("oso", 900, "salta", s=330, f=0.6, luego=(3.6, "saluda"))],
       p=[P("🍎", 360, 60, "cae", s=140), P("🍌", 720, 60, "cae", d=0.3, s=140), P("🍪", 1010, 60, "cae", d=0.6, s=120)]),
 ]),
}

if __name__ == "__main__":
    cual, out = sys.argv[1], sys.argv[2]; EP = EPISODIOS[cual]
    C = Q.Cuento([(str(i), b["t"], b.get("pausa", 0.8)) for i, b in enumerate(EP["escenas"])], cual)
    fn = lambda t: frame(C, EP, t)
    if len(sys.argv) > 3:
        pts = sorted([C.ini[k] + C.voz[k][2] * 0.5 for k in range(len(C.ini))] + [C.ini[k] + C.voz[k][2] + 0.5 for k in range(len(C.ini))])
        ims = [fn(s).resize((180, 320)) for s in pts]
        c = Image.new("RGB", (180 * len(ims), 320)); [c.paste(m, (k * 180, 0)) for k, m in enumerate(ims)]
        c.save(f"/tmp/prev_{cual}.jpg"); print("dur", round(C.dur, 1)); sys.exit()
    audio(C, EP, "/tmp/_ep.wav"); N.render(fn, C.dur, out, "/tmp/_ep.wav")
