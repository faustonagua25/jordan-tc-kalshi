# JORDAN TC — Kalshi Scanner

Aplicación Streamlit de solo lectura para explorar mercados públicos abiertos de Kalshi.

## Archivos
- `app.py`: aplicación web.
- `requirements.txt`: dependencias.

## Publicar con Streamlit Community Cloud
1. Crea una cuenta en GitHub.
2. Crea un repositorio llamado `jordan-tc-kalshi`.
3. Sube `app.py` y `requirements.txt` a la raíz del repositorio.
4. Entra en https://share.streamlit.io/ y autoriza GitHub.
5. Crea una app seleccionando el repositorio, rama `main` y archivo `app.py`.
6. Pulsa Deploy.

## Ejecutar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Importante
- Solo consulta datos públicos; no requiere claves API.
- No envía órdenes ni accede a la cuenta Kalshi.
- Los filtros de spread y volumen solo identifican mercados para revisar.
- La probabilidad implícita del mercado no es una predicción propia ni una garantía de acierto.
- La API puede cambiar, limitar solicitudes o devolver campos vacíos.
