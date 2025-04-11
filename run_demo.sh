#!/bin/bash

# El Hareketleri Demo Uygulaması Başlatma Betiği

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}     El Hareketleri Tanıma Demo Uygulaması${NC}"
echo -e "${BLUE}====================================================${NC}"
echo -e "${YELLOW}Bu uygulama MediaPipe kullanarak temel el hareketlerini tanır.${NC}"
echo 
echo -e "${BLUE}Desteklenen hareketler:${NC}"
echo -e " - ${GREEN}Başparmak Yukarı/Aşağı${NC}"
echo -e " - ${GREEN}Barış İşareti${NC}"
echo -e " - ${GREEN}Tamam İşareti${NC}"
echo -e " - ${GREEN}Yumruk${NC}"
echo -e " - ${GREEN}Açık El${NC}"
echo -e " - ${GREEN}İşaret${NC}"
echo -e " - ${GREEN}Kalp${NC}"
echo -e " - ${GREEN}Rock İşareti${NC}"
echo 

# Bağımlılıkları kontrol et
echo -e "${BLUE}Gerekli bağımlılıklar kontrol ediliyor...${NC}"
python3 -c "import cv2, numpy, mediapipe" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Gerekli Python bağımlılıkları eksik. Yükleniyor...${NC}"
    pip3 install -r requirements.txt
else
    echo -e "${GREEN}Tüm bağımlılıklar mevcut.${NC}"
fi

# Parametreleri tanımla
CAMERA_ID=0
RESOLUTION="640x480"
FLIP=true

# Parametreleri ayarla
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --camera)
        CAMERA_ID="$2"
        shift
        shift
        ;;
        --resolution)
        RESOLUTION="$2"
        shift
        shift
        ;;
        --no-flip)
        FLIP=false
        shift
        ;;
        --no-actions)
        NO_ACTIONS="--no-actions"
        shift
        ;;
        *)
        echo -e "${RED}Bilinmeyen parametre: $1${NC}"
        exit 1
        ;;
    esac
done

# Kamera erişimini kontrol et
echo -e "${BLUE}Kamera $CAMERA_ID erişimi kontrol ediliyor...${NC}"
python3 -c "import cv2; cap = cv2.VideoCapture($CAMERA_ID); print('OK' if cap.isOpened() else 'FAIL'); cap.release()" | grep -q "OK"
if [ $? -ne 0 ]; then
    echo -e "${RED}Kamera $CAMERA_ID erişilemez! Başka bir kamera ID deneyin.${NC}"
    echo -e "${YELLOW}Kullanım: $0 --camera [ID] --resolution [WIDTHxHEIGHT] [--no-flip] [--no-actions]${NC}"
    exit 1
fi

# Flip parametresini ayarla
FLIP_ARG=""
if [ "$FLIP" = true ]; then
    FLIP_ARG="--flip"
fi

echo
echo -e "${GREEN}Uygulama başlatılıyor...${NC}"
echo -e "${BLUE}Parametreler:${NC}"
echo -e " - Kamera ID: ${YELLOW}$CAMERA_ID${NC}"
echo -e " - Çözünürlük: ${YELLOW}$RESOLUTION${NC}"
echo -e " - Yatay Çevirme: ${YELLOW}$FLIP${NC}"
echo -e " - Eylemler: ${YELLOW}$([ -z "$NO_ACTIONS" ] && echo "Etkin" || echo "Devre Dışı")${NC}"
echo 
echo -e "${RED}Çıkmak için 'q' tuşuna basın.${NC}"
echo -e "${BLUE}====================================================${NC}"

# Ses dosyaları klasörünü kontrol et
SOUNDS_DIR="./sounds"
if [ ! -d "$SOUNDS_DIR" ]; then
    echo -e "${YELLOW}Ses dosyaları klasörü oluşturuluyor...${NC}"
    mkdir -p "$SOUNDS_DIR"
fi

# Uygulamayı başlat
python3 src/gesture_demo.py --camera-id $CAMERA_ID --resolution $RESOLUTION $FLIP_ARG $NO_ACTIONS 