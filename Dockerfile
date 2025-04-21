# ===== STAGE 1 : Build Python binary =====
FROM python:3.11-slim as builder

WORKDIR /build

# Install pyinstaller and other deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY app/ .

# Générer le binaire standalone
RUN pyinstaller --name babbox --onefile cli.py

# ===== STAGE 2 : Image finale minimale =====
FROM alpine:3.21

# Installer libstdc++ (nécessaire pour exécuter des binaires compilés Python)
RUN apk add --no-cache libstdc++

WORKDIR /app

# Copier le binaire seulement
COPY --from=builder /build/dist/babbox /usr/local/bin/babbox

# Copier les ressources JSON + styles
COPY app/commands.json /app/commands.json
COPY app/styles /app/styles

ENTRYPOINT ["babbox"]
