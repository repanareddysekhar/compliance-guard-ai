#!/bin/sh
set -eu

MODEL="${LLM_MODEL:-llama3.2:3b}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"

if [ -z "$MODEL" ]; then
  echo "ERROR: LLM_MODEL is empty. Set LLM_MODEL=llama3.2:3b in .env"
  exit 1
fi

echo "Waiting for Ollama at ${OLLAMA_HOST}..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

echo "Pulling model: ${MODEL}"
ollama pull "${MODEL}"

echo "Installed models:"
ollama list
echo "Model ${MODEL} is ready."
