# Étape 1 : Image de base et installation des dépendances système
FROM python:3.12-slim as base

RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Étape 2 : Création de l'utilisateur 'user' avec l'ID 1000
RUN useradd -m -u 1000 user

# Étape 3 : Définition des variables d'environnement et du répertoire de travail
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Étape 4 : Installation de 'uv' (gestionnaire de projet Python)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Étape 5 : Copie des fichiers de configuration avec les permissions appropriées
COPY --chown=user:user nginx.conf /etc/nginx/nginx.conf
COPY --chown=user:user supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Étape 6 : Copie des fichiers de l'application avec les permissions appropriées
COPY --chown=user:user . $HOME/app

# Étape 7 : Installation des dépendances Python
COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-cache

# Étape 8 : Téléchargement et installation de Qdrant
RUN curl -fsSL https://github.com/qdrant/qdrant/releases/latest/download/qdrant-linux-x86_64 -o /usr/local/bin/qdrant \
    && chmod +x /usr/local/bin/qdrant

# Étape 9 : Exposition des ports nécessaires
EXPOSE 8080 6333

# Étape 10 : Changement de l'utilisateur pour 'user'
USER user

# Étape 11 : Lancement de l'application avec supervisord
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
