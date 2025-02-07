#!/bin/bash
set -e

# Démarrer Nginx
echo "Démarrage de Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Démarrer Qdrant
echo "Démarrage de Qdrant..."
/usr/local/bin/qdrant &
QDRANT_PID=$!

# Démarrer le Backend
echo "Démarrage du Backend..."
cd /home/user/app/backend
uv sync
uv run fastapi app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Démarrer le Frontend
echo "Démarrage du Frontend..."
cd /home/user/app/frontend
uv sync
uv run streamlit run app/main.py --server.port 8501 --server.address=0.0.0.0 &
FRONTEND_PID=$!

# Fonction pour gérer la terminaison des processus
terminate_processes() {
    echo "Arrêt des services..."
    kill -TERM $NGINX_PID
    kill -TERM $QDRANT_PID
    kill -TERM $BACKEND_PID
    kill -TERM $FRONTEND_PID
    wait $NGINX_PID
    wait $QDRANT_PID
    wait $BACKEND_PID
    wait $FRONTEND_PID
    echo "Services arrêtés."
}

# Capturer les signaux d'arrêt pour nettoyer correctement
trap terminate_processes SIGTERM SIGINT

# Attendre que les processus se terminent
wait $NGINX_PID
wait $QDRANT_PID
wait $BACKEND_PID
wait $FRONTEND_PID
