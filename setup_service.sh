#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Cabeça de Droid - Configuração de Serviço no Linux VM   "
echo "=========================================================="

CURRENT_USER=$(whoami)
PROJECT_DIR=$(pwd)
SERVICE_NAME="cabeca-de-droid"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "[1/5] Atualizando pacotes do sistema e instalando Python venv..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3-venv python3-pip curl
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 python3-pip python3-virtualenv curl
fi

echo "[2/5] Criando ambiente virtual Python..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "[3/5] Instalando dependências..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Playwright (opcional/headless)
if command -v playwright &> /dev/null || .venv/bin/python -c "import playwright" &> /dev/null; then
    echo "[INFO] Instalando Chromium do Playwright..."
    .venv/bin/playwright install --with-deps chromium || true
fi

echo "[4/5] Configurando o arquivo de serviço systemd (${SERVICE_FILE})..."
sudo bash -c "cat <<EOF > ${SERVICE_FILE}
[Unit]
Description=Cabeça de Droid - Assistente HoYoLAB
After=network.target tailscaled.service
Wants=tailscaled.service

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=\"PYTHONUNBUFFERED=1\"
Environment=\"ALLOW_LAN=1\"
Environment=\"HOST=0.0.0.0\"
Environment=\"PORT=8000\"
ExecStart=${PROJECT_DIR}/.venv/bin/python main.py --no-browser --lan --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
EOF"

echo "[5/5] Recarregando systemd e habilitando inicialização automática..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo "=========================================================="
echo "  SUCESSO! O serviço foi instalado e iniciado."
echo "=========================================================="
echo "Comandos úteis:"
echo "  - Iniciar:    sudo systemctl start ${SERVICE_NAME}"
echo "  - Parar:      sudo systemctl stop ${SERVICE_NAME}"
echo "  - Reiniciar:  sudo systemctl restart ${SERVICE_NAME}"
echo "  - Status:     sudo systemctl status ${SERVICE_NAME}"
echo "  - Logs:       sudo journalctl -u ${SERVICE_NAME} -f"
echo "=========================================================="
