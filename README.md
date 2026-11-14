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
