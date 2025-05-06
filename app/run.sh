#!/bin/bash
echo "Iniciando graficos en puerto 8000"
uvicorn graficos.main:app --reload --port 8000 &

echo "Iniciando consultas en puerto 8001"
uvicorn consultas.main:app --reload --port 8001 &

echo "Iniciando api en puerto 8002"
uvicorn api.main:app --reload --port 8002 &
wait

