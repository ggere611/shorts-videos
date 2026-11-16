"""Modela las 6 mascotas en 3D (Blender/bpy) y renderiza sus gestos como sprites.
Uso: python3 mascotas3d.py salida_dir [char1,char2] [pose1,pose2] [px]
"""
import bpy, math, sys, os
from mathutils import Vector

CH = {
 "oso":       dict(body="#A86B3C", dark="#8A5530", belly="#E8B98C", my=137, eyes=(78, 122, 96, 1.0)),
 "toro":      dict(body="#E0603C", dark="#B8462A", belly="#F7C9A8", my=152, eyes=(78, 122, 96, 1.0)),
 "rana":      dict(body="#6CC24A", dark="#4E9E32", belly="#D6F2C2", my=128, eyes=(70, 130, 74, 0.86)),
 "monstruo":  dict(body="#8E5CF0", dark="#6C3FD0", belly="#C8B0FA", my=142, eyes=(100, None, 98, 1.36)),
 "gato":      dict(body="#F2A541", dark="#D2852A", belly="#FFE2B8", my=138, eyes=(78, 122, 98, 1.0)),
 "carpincho": dict(body="#B07A4A", dark="#8A5A33", belly="#D9B48A", my=150, eyes=(80, 120, 96, 0.82)),
}
POSES = {  # look x, look y, brazo izq, brazo der (None=abajo, grados=arriba), boca, ojos
 "alentando":       (0, 0, None, None, "sonrisa", "abiertos"),
 "alentando_blink": (0, 0, None, None, "sonrisa", "cerrados"),
 "act_izq":         (-1, 0, None, None, "sonrisa", "abiertos"),
 "act_der":         (1, 0, None, None, "sonrisa", "abiertos"),
 "act_arriba":      (0, 1, None, None, "sonrisa", "abiertos"),
 "act_izq_h":       (-1, 0, None, None, "abierta", "abiertos"),
 "act_der_h":       (1, 0, None, None, "abierta", "abiertos"),
 "act_habla_c":     (0, 0, None, None, "abierta", "abiertos"),
 "act_saluda1":     (0, 0, None, 10, "sonrisa", "abiertos"),
 "act_saluda2":     (0, 0, None, 48, "sonrisa", "abiertos"),
 "act_sorpresa":    (0, 0.5, 25, 25, "abierta", "abiertos"),
 "act_triste":      (0, -1, None, None, "triste", "abiertos"),
 "festejando":      (0, 0, 20, 20, "abierta", "felices"),
}
INK = "#14213D"
def rgb(h, a=1):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x ** 2.2 for x in c) + (a,)
def X(x): return (x - 100) / 50
def Z(y): return (190 - y) / 50
_m = {}
def mat(col, rough=0.38, emit=0):
    k = (col, rough, emit)
    if k in _m: return _m[k]
    m = bpy.data.materials.new(col); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb(col); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = rgb(col); b.inputs["Emission Strength"].default_value = emit
    _m[k] = m; return m
def sph(loc, sc, col, rot=(0, 0, 0), rough=0.38, emit=0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=40, ring_count=20, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = sc if isinstance(sc, tuple) else (sc, sc, sc)
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat(col, rough, emit)); return o
def cone(loc, r, h, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r, radius2=r * 0.12, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(mat(col)); return o
def arco(p0, p1, p2, col, grosor=0.04):
    cu = bpy.data.curves.new("a", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = grosor; cu.bevel_resolution = 6
    s = cu.splines.new("BEZIER"); s.bezier_points.add(2)
    for bp, p in zip(s.bezier_points, (p0, p1, p2)):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    cu.use_fill_caps = True
    o = bpy.data.objects.new("a", cu); bpy.context.collection.objects.link(o); o.data.materials.append(mat(col, 0.5)); return o

def construir(char, pose):
    bpy.ops.wm.read_factory_settings(use_empty=True); _m.clear()
    c = CH[char]; lookx, looky, aL, aR, boca, ojos = POSES[pose]
    sc = bpy.context.scene
    # cuerpo: cubo redondeado
    alto = {"rana": 1.05, "carpincho": 1.32}.get(char, 1.36); cz = {"rana": 1.12, "carpincho": 1.36}.get(char, 1.42)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, cz)); body = bpy.context.object
    body.scale = (1.5, 1.2, alto * 1.22); md = body.modifiers.new("s", "SUBSURF"); md.levels = md.render_levels = 3
    bpy.ops.object.shade_smooth(); body.data.materials.append(mat(c["body"]))
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    def frente(x, z):
        hit, loc, *_ = sc.ray_cast(dg, Vector((x, -6, z)), Vector((0, 1, 0)))
        return loc.y if hit else -0.6
    # panza
    if char != "toro": sph((0, frente(0, 0.75) + 0.42, 0.78), (0.78, 0.5, 0.56), c["belly"])
    # pies y brazos
    for s in (-1, 1):
        sph((s * 0.46, -0.28, 0.13), (0.34, 0.5, 0.17), c["dark"])
        a = aL if s < 0 else aR
        if a is None: sph((s * 1.3, -0.1, cz - 0.28), (0.2, 0.22, 0.42), c["dark"], rot=(0, s * -0.22, 0))
        else:
            r = math.radians(a); sph((s * (1.22 + 0.5 * math.sin(r)), -0.1, cz + 0.38 + 0.5 * math.cos(r)), (0.2, 0.22, 0.46), c["dark"], rot=(0, s * r, 0))
    # ojos
    lx, rx, ly, es = c["eyes"]
    for ex in ([lx] if rx is None else [lx, rx]):
        x, z, r = X(ex), Z(ly), 0.4 * es
        y = frente(x, z) + r * 0.45 if char != "rana" else -0.55
        if char == "rana": sph((x, y + 0.12, z - 0.02), r * 1.28, c["body"])
        if ojos == "abiertos":
            sph((x, y, z), r, "#FFFFFF", rough=0.15)
            px, pz = x + lookx * r * 0.42, z + looky * r * 0.36 - 0.02
            py = y - math.sqrt(max(0.01, r * r - (px - x) ** 2 - (pz - z) ** 2)) + r * 0.18
            sph((px, py, pz), (r * 0.52, r * 0.3, r * 0.52), INK, rough=0.2)
            sph((px + r * 0.17, py - r * 0.27, pz + r * 0.2), r * 0.15, "#FFFFFF", emit=1.2)
        else:
            sph((x, y, z), r, c["body"])
            k = -1 if ojos == "felices" else 1
            arco((x - r * 0.6, y - r * 0.82, z + k * r * 0.12), (x, y - r * 1.02, z - k * r * 0.2), (x + r * 0.6, y - r * 0.82, z + k * r * 0.12), INK, 0.045)
    # cachetes
    for s in (-1, 1):
        x, z = s * 0.86, Z(124); sph((x, frente(x, z) + 0.02, z), (0.2, 0.05, 0.13), "#FF8FA3", rough=0.7)
    # boca / hocico
    mz = Z(c["my"]); my = frente(0, mz)
    if char in ("toro", "carpincho"):
        sph((0, my + 0.1, mz + 0.16), (0.52, 0.3, 0.34), c["belly"] if char == "toro" else c["dark"])
        for s in (-1, 1): sph((s * 0.17, my - 0.17, mz + 0.27), (0.06, 0.03, 0.045), INK)
        my -= 0.19; mz -= 0.02
    elif char in ("oso", "gato"):
        sph((0, frente(0, mz + 0.3) - 0.02, mz + 0.3), (0.12, 0.07, 0.08), INK if char == "oso" else "#FF8FA3", rough=0.25)
    if boca == "abierta":
        sph((0, my + 0.02, mz - 0.03), (0.17, 0.07, 0.19), INK, rough=0.6); sph((0, my - 0.03, mz - 0.13), (0.11, 0.04, 0.07), "#FF7A8A")
    else:
        k = 1 if boca == "sonrisa" else -1
        arco((-0.22, my - 0.02, mz + k * 0.05), (0, my - 0.05, mz - k * 0.07), (0.22, my - 0.02, mz + k * 0.05), INK)
    # rasgos propios
    top = cz + alto * 0.98
    if char == "oso":
        for s in (-1, 1):
            sph((s * 0.95, 0, top - 0.12), (0.36, 0.2, 0.36), c["body"]); sph((s * 0.95, -0.14, top - 0.12), (0.2, 0.1, 0.2), c["belly"])
    if char == "gato":
        for s in (-1, 1):
            cone((s * 0.82, 0, top + 0.08), 0.4, 0.75, c["body"], rot=(0, s * 0.28, 0)); cone((s * 0.82, -0.2, top + 0.02), 0.22, 0.45, "#FF8FA3", rot=(0, s * 0.28, 0))
            for dz in (0.06, -0.06):
                arco((s * 0.5, frente(s * 0.5, mz + 0.2) - 0.03, mz + 0.2 + dz), (s * 0.95, -1.0, mz + 0.2 + dz * 2), (s * 1.4, -0.85, mz + 0.22 + dz * 4), INK, 0.014)
    if char == "toro":
        for s in (-1, 1):
            cone((s * 0.95, 0, top + 0.02), 0.2, 0.75, "#FFF3D6", rot=(0, s * 0.75, 0)); sph((s * 1.32, 0, cz + 0.72), (0.26, 0.12, 0.16), c["dark"], rot=(0, s * 0.4, 0))
        arco((-0.14, my - 0.22, mz - 0.1), (0, my - 0.3, mz - 0.26), (0.14, my - 0.22, mz - 0.1), "#F4C542", 0.035)
    if char == "monstruo":
        for s in (-1, 1): cone((s * 0.62, 0, top + 0.15), 0.2, 0.6, "#F4C542", rot=(0, s * 0.3, 0))
        for s, dz in ((-0.9, 0.2), (0.95, -0.35), (-0.7, -0.75)): sph((s, frente(s, cz + dz) + 0.04, cz + dz), (0.12, 0.04, 0.12), c["dark"])
    if char == "carpincho":
        for s in (-1, 1): sph((s * 0.82, 0, top - 0.02), (0.2, 0.12, 0.2), c["dark"])
    # luz y cámara
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    for loc, e, s in (((-3.5, -5, 6), 900, 5), ((4.5, -4, 2.5), 260, 6), ((0, 4, 5), 400, 4)):
        bpy.ops.object.light_add(type="AREA", location=loc); l = bpy.context.object; l.data.energy = e; l.data.size = s
        l.rotation_euler = (Vector((0, 0, 1.4)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.camera_add(location=(0, -10, 3.2)); cam = bpy.context.object; cam.data.type = "ORTHO"; cam.data.ortho_scale = 4.5
    t = math.radians(8); cam.rotation_euler = (math.pi / 2 - t, 0, 0)
    cam.location = (0, -10, 1.84 + 10 * math.tan(t)); sc.camera = cam

def render(char, pose, out, px=640):
    construir(char, pose); sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = 28; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = px; sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = os.path.join(out, f"{char}_{pose}.png"); bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    chars = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] != "all" else list(CH)
    poses = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] != "all" else list(POSES)
    px = int(sys.argv[4]) if len(sys.argv) > 4 else 640
    for c_ in chars:
        for p in poses: render(c_, p, out, px)
