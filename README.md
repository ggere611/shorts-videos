# shorts-videos

Videos para el canal de YouTube (Shorts infantiles), publicados automáticamente por n8n.

## Cómo funciona
- `cola.json`: lista de videos con `archivo`, `titulo`, `descripcion`, `tags` y `estado`.
  - `pendiente`: generado, esperando el ok.
  - `aprobado`: n8n publica uno por día a las 20:00 (hora Argentina).
  - `publicar_ya`: n8n lo publica en la próxima revisión (cada 5 minutos), a cualquier hora.
  - `publicado`: ya está en YouTube.
- `nichos.py colores|calculo salida.mp4`: generadores de otros nichos.
- `generar_tabla.py N salida.mp4`: genera el short de la tabla del N (agregar `preview` para ver cuadros sueltos).
- n8n lee `cola.json` desde la API de GitHub cada 5 minutos, publica, lo anota en la planilla "Publicaciones" y baja el MP4 de este repo.

- `cuentos.py pelota salida.mp4 [preview]`: cuentos entre mascotas con narrador (voz Piper, se baja sola) y avatares que actúan (sprites `mascotas/*_act_*.png`: miradas, saludo, sorpresa, triste).
- `nichos.py aventura|intruso|laberinto|movete|seequivoca|seequivoca2|animales_en|deportes_en|colores2 salida.mp4`: demás formatos.

- `mascotas3d.py salida_dir [chars] [poses] [px]`: modela las 6 mascotas en 3D con Blender (`pip install bpy`) y renderiza sus gestos a `mascotas3d/`.
- `episodios.py linterna|globo|ruido salida.mp4 [preview]`: serie de aventuras 3D con narrador; cada episodio es una lista de escenas en `EPISODIOS`. `MASC_DIR=mascotas3d python3 cuentos.py pelota ...` para la pelota en 3D.

- `memes.py sueno|parcial|plata salida.mp4 [preview]`: memes originales (no infantiles) con las mascotas 3D. En la cola van con `para_ninos: false`, `categoria: "23"` y estado `espera_config` hasta que el flujo de n8n soporte esos campos.

## Videos no infantiles y clips con IA (17/11/2026)
- El flujo de publicación ya lee `para_ninos` (false = no es contenido para niños) y `categoria` (por defecto 27) de cada item de `cola.json`.
- Flujo n8n nuevo "Generar clips con Higgsfield" (id `3T0wzfDggpvmtOXx`): cada 10 min toma UN item con estado `generar` y campo `prompt`, pide el clip a la API de Higgsfield, espera y lo guarda en Google Drive (raíz) como `CLIP_IA_<archivo>`.
  Campos opcionales: `modelo` (por defecto `alibaba/wan-3.0/text-to-video`), `duracion` (5), `resolucion` (`480p`). Formato 9:16, sin audio.
  Cada archivo se pide una sola vez (se anota antes de pedir, para no cobrar doble). Después se edita (texto, sonido) y pasa a `pendiente`.
- Credencial n8n "Higgsfield API (pegar clave)": cabecera `Authorization` con valor `Key <clave>`; la clave la pega Geremias.
- Desde el 17/11 el flujo "Generar clips con Higgsfield" también **publica en YouTube** el clip generado (título, descripción, tags, `categoria` y `para_ninos` del item), además de guardarlo en Drive. Un item `generar` = un video generado y publicado sin revisión. Estado `generado` = ya procesado, n8n lo ignora.
