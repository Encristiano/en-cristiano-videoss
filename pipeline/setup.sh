#!/bin/bash
# Prepara una sesión nueva para producir episodios de En Cristiano.
set -e
pip install --break-system-packages -q piper-tts pycairo soundfile numpy 2>/dev/null
mkdir -p /home/claude/tts && cd /home/claude/tts
if [ ! -f vits-piper-es_ES-davefx-medium/es_ES-davefx-medium.onnx ]; then
  curl -sSL -o davefx.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_ES-davefx-medium.tar.bz2
  tar xjf davefx.tar.bz2 && rm davefx.tar.bz2
fi
fc-list | grep -q Poppins || echo "AVISO: falta la fuente Poppins"
echo "setup ok"
