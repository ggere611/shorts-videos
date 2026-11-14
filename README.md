# shorts-videos

Videos para el canal de YouTube (Shorts infantiles), publicados automáticamente por n8n.

## Cómo funciona
- `cola.json`: lista de videos con `archivo`, `titulo`, `descripcion`, `tags` y `estado`.
  - `pendiente`: generado, esperando el ok.
  - `aprobado`: n8n lo publica (uno por hora) y lo registra en la planilla "Publicaciones".
  - `publicado`: ya está en YouTube.
- `generar_tabla.py N salida.mp4`: genera el short de la tabla del N (agregar `preview` para ver cuadros sueltos).
- n8n lee `cola.json` desde la API de GitHub cada hora y baja el MP4 de este repo.
