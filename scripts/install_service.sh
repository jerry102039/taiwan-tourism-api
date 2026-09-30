#!/usr/bin/env bash
# 將 Taiwan Tourism API 安裝為 systemd 服務（適用 Ubuntu / Debian / RHEL 等使用 systemd 的 Linux）
#
# 用法：
#   sudo bash scripts/install_service.sh              # 安裝並啟動
#   sudo bash scripts/install_service.sh --uninstall  # 停止並移除服務
#
# 可用環境變數覆寫預設值（需搭配 sudo -E 或寫在 sudo 之後）：
#   sudo PORT=9000 API_KEY=my-secret bash scripts/install_service.sh
#
#   SERVICE_NAME  服務名稱          （預設 taiwan-tourism-api）
#   SERVICE_USER  執行服務的使用者  （預設為執行 sudo 的使用者）
#   HOST          監聽位址          （預設 0.0.0.0）
#   PORT          監聽埠號          （預設 8000）
#   API_KEY       寫入操作的 API Key（預設沿用 app/config.py 的 ntub-iot-2026）
#   PYTHON        建立 venv 的 Python（預設 python3，需 3.11 以上）
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-taiwan-tourism-api}"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-$(id -un)}}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
PYTHON="${PYTHON:-python3}"

# 專案根目錄 = 本腳本所在目錄的上一層
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_FILE="/etc/default/${SERVICE_NAME}"

info() { echo -e "\033[1;32m==>\033[0m $*"; }
die()  { echo -e "\033[1;31m錯誤：\033[0m $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "請使用 sudo 執行：sudo bash $0 $*"
command -v systemctl >/dev/null || die "找不到 systemctl，此系統未使用 systemd"

# ---------- 解除安裝 ----------
if [[ "${1:-}" == "--uninstall" ]]; then
    info "停止並移除服務 $SERVICE_NAME"
    systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$UNIT_FILE"
    systemctl daemon-reload
    info "已移除 $UNIT_FILE（保留 $ENV_FILE、$VENV_DIR 與資料庫，如不需要請手動刪除）"
    exit 0
fi

id "$SERVICE_USER" >/dev/null 2>&1 || die "使用者 $SERVICE_USER 不存在"
command -v "$PYTHON" >/dev/null || die "找不到 $PYTHON，請先安裝 Python 3.11 以上"
"$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 11))' \
    || die "Python 版本需 3.11 以上（目前：$("$PYTHON" -V 2>&1)）"

# ---------- 建立虛擬環境並安裝套件 ----------
info "專案目錄：$APP_DIR（執行使用者：$SERVICE_USER）"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    info "建立虛擬環境 $VENV_DIR"
    sudo -u "$SERVICE_USER" "$PYTHON" -m venv "$VENV_DIR" \
        || die "建立 venv 失敗；Debian / Ubuntu 請先執行：sudo apt install python3-venv"
fi
info "安裝相依套件"
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --quiet --upgrade pip
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# 服務使用者需能寫入 data/（SQLite 資料庫）
chown -R "$SERVICE_USER": "$APP_DIR/data"

# ---------- 環境變數檔（已存在則保留，避免覆蓋使用者修改） ----------
if [[ ! -f "$ENV_FILE" ]]; then
    info "建立環境變數檔 $ENV_FILE"
    {
        echo "# $SERVICE_NAME 環境變數，修改後執行：sudo systemctl restart $SERVICE_NAME"
        echo "HOST=$HOST"
        echo "PORT=$PORT"
        if [[ -n "${API_KEY+x}" ]]; then echo "API_KEY=$API_KEY"; else echo "#API_KEY=ntub-iot-2026"; fi
        echo "#DB_FILE=$APP_DIR/data/tourism.db"
    } > "$ENV_FILE"
    chmod 640 "$ENV_FILE"
    chown root:"$(id -gn "$SERVICE_USER")" "$ENV_FILE"
else
    info "沿用既有的 $ENV_FILE"
fi

# ---------- systemd unit ----------
info "寫入 $UNIT_FILE"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=Taiwan Tourism Open Data RESTful API (FastAPI)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$(id -gn "$SERVICE_USER")
WorkingDirectory=$APP_DIR
Environment=PYTHONUNBUFFERED=1
Environment=HOST=$HOST
Environment=PORT=$PORT
EnvironmentFile=-$ENV_FILE
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host \${HOST} --port \${PORT} --proxy-headers
Restart=on-failure
RestartSec=5

# 基本安全強化
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF

# ---------- 啟動 ----------
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME"

sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    info "服務已啟動 ✅  http://$(hostname -I 2>/dev/null | awk '{print $1}'):$(. "$ENV_FILE"; echo "${PORT:-8000}")/docs"
else
    systemctl status "$SERVICE_NAME" --no-pager || true
    die "服務啟動失敗，請查看：journalctl -u $SERVICE_NAME -e"
fi

cat <<EOF

常用指令：
  sudo systemctl status  $SERVICE_NAME     # 查看狀態
  sudo systemctl restart $SERVICE_NAME     # 重新啟動
  sudo systemctl stop    $SERVICE_NAME     # 停止
  journalctl -u $SERVICE_NAME -f           # 即時查看日誌
  sudo nano $ENV_FILE                      # 修改 PORT / API_KEY 等設定
EOF
