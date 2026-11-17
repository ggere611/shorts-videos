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
