#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

VENV_PATH=${VENV_PATH:-"$REPO_ROOT/.venv_stt_local"}
MODEL_DIR=${MODEL_DIR:-"$HOME/models/faster-whisper-medium"}
STT_PORT=${STT_PORT:-8001}

if [ ! -d "$MODEL_DIR" ]; then
  echo "[run_stt_local] ERROR: Modelo no encontrado en $MODEL_DIR" >&2
  echo "Descarga los pesos de faster-whisper (p.ej. medium, large-v3) y actualiza MODEL_DIR." >&2
  exit 1
fi

python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"

pip install --upgrade pip >/dev/null
CUDA_INDEX_URL=${CUDA_INDEX_URL:-"https://download.pytorch.org/whl/cu121"}
DEVICE_PREF=$(echo "${STT_DEVICE:-auto}" | tr '[:upper:]' '[:lower:]')

if command -v nvidia-smi >/dev/null 2>&1 || [ "$DEVICE_PREF" = "cuda" ]; then
  echo "[run_stt_local] Installing CUDA-enabled CTranslate2 from $CUDA_INDEX_URL"
  pip install --quiet --upgrade --extra-index-url "$CUDA_INDEX_URL" \
    'ctranslate2>=4.2,<5'
else
  pip install --quiet --upgrade 'ctranslate2>=4.2,<5'
fi

pip install --quiet --upgrade \
  faster-whisper \
  fastapi \
  "uvicorn[standard]" \
  python-multipart \
  soundfile

export STT_MODEL=${STT_MODEL:-"$MODEL_DIR"}
export STT_DEVICE=${STT_DEVICE:-auto}
export STT_COMPUTE=${STT_COMPUTE:-auto}
export STT_VAD=${STT_VAD:-1}

add_ld_path() {
  local dir="$1"
  [ -d "$dir" ] || return 1
  case ":${LD_LIBRARY_PATH:-}:" in
    *:"$dir":*) return 0 ;;
    *)
      export LD_LIBRARY_PATH="$dir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
      echo "[run_stt_local] Añadiendo $dir a LD_LIBRARY_PATH" >&2
      ;;
  esac
}

ensure_cudnn_path() {
  local hint
  if [ -n "${CUDA_CUDNN_PATH:-}" ]; then
    add_ld_path "$CUDA_CUDNN_PATH" && return 0
  fi

  local candidates=(
    "/usr/local/cuda/lib64"
    "/usr/local/cuda/lib"
    "/usr/local/cuda-12.1/lib64"
    "/usr/local/cuda-12/lib64"
    "/usr/lib/x86_64-linux-gnu"
    "/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib"
    "/usr/local/lib/python3.11/dist-packages/nvidia/cudnn/lib"
    "/usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib"
  )

  for dir in "${candidates[@]}"; do
    if [ -d "$dir" ]; then
      for f in $dir/libcudnn_ops.so*; do
        [ -f "$f" ] || continue
        add_ld_path "$dir"
        return 0
      done
    fi
  done

  hint=$(find /usr/local -maxdepth 5 -type f -name 'libcudnn_ops.so*' 2>/dev/null | head -n 1)
  if [ -n "$hint" ]; then
    add_ld_path "$(dirname "$hint")"
    return 0
  fi

  return 1
}

if [ "$DEVICE_PREF" = "cuda" ] || { [ "$DEVICE_PREF" = "auto" ] && command -v nvidia-smi >/dev/null 2>&1; }; then
  if ! ensure_cudnn_path; then
    echo "[run_stt_local] ADVERTENCIA: no se encontraron bibliotecas cuDNN (libcudnn_ops). CUDA puede fallar." >&2
  fi
fi

cd "$REPO_ROOT"

echo "[run_stt_local] Escuchando en http://0.0.0.0:$STT_PORT/stt"
echo "[run_stt_local] Modelo: $STT_MODEL | Device: $STT_DEVICE | Compute: $STT_COMPUTE"

export PYTHONPATH="$REPO_ROOT/site"
uvicorn services.stt.stt_service:app \
    --host 0.0.0.0 \
    --port "$STT_PORT"
