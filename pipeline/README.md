# Pipeline En Cristiano
1. `bash pipeline/setup.sh`
2. Añadir el episodio nuevo al final de `pipeline/episodios.py` (mismo formato; plantillas: title, items, big, bars, crowd, cta; props en `engine.py` → PROPS).
3. `cd pipeline && python3 engine.py voice N && python3 engine.py preview N t1,t2 && python3 engine.py build N`
4. Copiar `pipeline/out/<slug>.mp4` a `videos/`, commit y push.
5. Programar en Metricool (marca 7778310) con media `https://raw.githubusercontent.com/Encristiano/en-cristiano-videoss/main/videos/<slug>.mp4`.
