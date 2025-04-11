#!/bin/bash
# El Hareketi Tanıma Web Uygulaması Başlatma Betiği

# Dizin bilgisi
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$BASE_DIR/src"

# Renk tanımları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Başlık göster
echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}    El Hareketi Tanıma - Web Uygulaması      ${NC}"
echo -e "${BLUE}==============================================${NC}"

# Python sürüm kontrolü
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}Python3 bulundu.${NC}"
else
    echo -e "${RED}Python3 bulunamadı! Lütfen Python 3.x yükleyin.${NC}"
    exit 1
fi

# Klasör yapısını kontrol et
if [ ! -d "$BASE_DIR/templates" ]; then
    echo -e "${YELLOW}templates klasörü oluşturuluyor...${NC}"
    mkdir -p "$BASE_DIR/templates"
fi

if [ ! -d "$BASE_DIR/static" ]; then
    echo -e "${YELLOW}static klasörü oluşturuluyor...${NC}"
    mkdir -p "$BASE_DIR/static/css"
    mkdir -p "$BASE_DIR/static/js"
    mkdir -p "$BASE_DIR/static/img"
fi

# Argümanları kontrol et
HOST="0.0.0.0"
PORT="5000"
DEBUG=""
CAMERA="0"

# Komut satırı argümanlarını işle
while [[ $# -gt 0 ]]; do
    case $1 in
        --port=*)
        PORT="${1#*=}"
        shift
        ;;
        --host=*)
        HOST="${1#*=}"
        shift
        ;;
        --debug)
        DEBUG="--debug"
        shift
        ;;
        --camera=*)
        CAMERA="${1#*=}"
        shift
        ;;
        *)
        echo -e "${RED}Bilinmeyen parametre: $1${NC}"
        exit 1
        ;;
    esac
done

# Web uygulamasını başlat
echo -e "${YELLOW}Web uygulaması başlatılıyor...${NC}"
echo -e "${GREEN}http://${HOST}:${PORT} adresinde sunucu çalışacak${NC}"
echo -e "${BLUE}==============================================${NC}"
echo -e "${YELLOW}Çıkmak için Ctrl+C tuşlarına basın${NC}"

# Flask uygulamasını çalıştır
$PYTHON_CMD "$SRC_DIR/web_app.py" --host="$HOST" --port="$PORT" --camera-id="$CAMERA" $DEBUG

echo -e "${GREEN}Uygulama durduruldu.${NC}" 