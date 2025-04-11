# Temel El Hareketleri Tanıma Sistemi

Bu proje, MediaPipe el izleme kütüphanesi kullanarak temel el hareketlerini (kalp, başparmak yukarı/aşağı, barış işareti vb.) gerçek zamanlı olarak tanıyan bir sistem içerir.

## 1. Özellikler

- MediaPipe Hands modeli ile hassas el izleme 
- 10+ temel el hareketi tanıma (Başparmak Yukarı/Aşağı, Barış, Tamam, Yumruk, vb.)
- Tanınan hareketlere göre özelleştirilebilir eylemler
- Gerçek zamanlı görsel geri bildirim ve animasyonlar 
- Yüksek performanslı video işleme
- Platform bağımsız çalışma (Windows, Linux, macOS)

## 2. Desteklenen Hareketler

Sistem şu anda aşağıdaki temel el hareketlerini tanıyabilmektedir:

1. **Başparmak Yukarı (Thumbs Up)**: 👍 - Sadece başparmak açık ve yukarı yönde
2. **Başparmak Aşağı (Thumbs Down)**: 👎 - Sadece başparmak açık ve aşağı yönde
3. **Barış İşareti (Peace)**: ✌️ - İşaret ve orta parmak açık, V şeklinde
4. **Tamam İşareti (OK)**: 👌 - Başparmak ve işaret parmağı birleşik, diğerleri açık
5. **Yumruk (Fist)**: ✊ - Tüm parmaklar kapalı
6. **Açık El (Open Hand)**: 🖐️ - Tüm parmaklar açık
7. **İşaret (Pointing)**: 👆 - Sadece işaret parmağı açık
8. **Kalp (Heart)**: ❤️ - El parmaklarıyla oluşturulan kalp şekli
9. **Rock İşareti (Rock)**: 🤘 - İşaret parmağı ve serçe parmak açık
10. **Tutma (Pinch)**: 👌 - Başparmak ve işaret parmağı uçları yakın
11. **Silah İşareti (Gun)**: 👉 - Başparmak yukarı, işaret parmağı açık

## 3. Kurulum

### Gereksinimler

- Python 3.7+
- OpenCV
- MediaPipe
- NumPy

### Bağımlılıkları Yükleme

```bash
pip install opencv-python mediapipe numpy
```

veya proje dizininde:

```bash
pip install -r requirements.txt
```

## 4. Kullanım

### Hızlı Başlangıç

Kolayca başlatmak için birlikte gelen shell betiğini kullanabilirsiniz:

```bash
./run_demo.sh
```

### Manuel Başlatma

```bash
cd /path/to/project
python3 src/gesture_demo.py --flip --resolution 640x480
```

### Komut Satırı Parametreleri

- `--camera-id CAMERA_ID`: Kullanılacak kamera ID'si (varsayılan: 0)
- `--flip`: Kamera görüntüsünü yatay çevirir (ayna efekti)
- `--resolution WIDTHxHEIGHT`: Kamera çözünürlüğü (varsayılan: 640x480)
- `--no-actions`: Eylemleri devre dışı bırakır

## 5. Sistem Mimarisi

Sistem üç ana bileşenden oluşur:

1. **MediaPipe El İzleme**: El pozisyonunu ve iskeletini izler
2. **Hareket Tanıyıcı**: El konumlarından hareketi belirler 
3. **Eylem İşleyici**: Tanınan hareketlere göre eylemler gerçekleştirir

### Dosya Yapısı

```
SignLang/v3/
├── src/
│   ├── gesture_recognizer.py  # Hareket tanıma sınıfı
│   ├── gesture_actions.py     # Eylem işleyici sınıfı 
│   ├── gesture_demo.py        # Demo uygulaması
├── sounds/                    # Ses dosyaları klasörü 
├── run_demo.sh                # Kolay başlatma betiği
├── requirements.txt           # Bağımlılıklar
└── TEMEL_HAREKETLER.md        # Bu belge
```

## 6. Özelleştirme

### Yeni Hareketler Ekleme

`GestureRecognizer` sınıfında `recognize_gesture` metodunu düzenleyerek yeni hareketler ekleyebilirsiniz:

```python
# Örnek yeni hareket tanıma kodu
if fingers_extended == [1, 1, 0, 0, 1]:
    return "spider_man", 0.9
```

### Yeni Eylemler Ekleme

`GestureActions` sınıfında yeni bir eylem metodu ekleyin ve `actions` sözlüğüne kaydedin:

```python
def action_spider_man(self, confidence):
    print(f"🕸️ Ağ fırlattı! (Güven: {confidence:.2f})")
    self._play_sound("spider_man.wav")
    
# Eylemi kaydedin
self.actions["spider_man"] = self.action_spider_man
```

## 7. Sorun Giderme

- **Kamera Algılanmıyor**: Kamera ID'sini değiştirin `--camera-id 1`
- **Düşük FPS**: Çözünürlüğü düşürün `--resolution 320x240`
- **Hareket Tanıma Sorunları**: Daha iyi aydınlatma sağlayın ve kameranın önünde el hareketlerini net bir şekilde yapın

## 8. Gelecek Geliştirmeler

- İşaret dili alfabesi tanıma entegrasyonu
- Çift el hareketi desteği
- Daha fazla ve karmaşık hareket tanıma
- Özel hareketleri kaydetme ve tanıma
- Daha gelişmiş eylem yanıtları

## 9. Lisans

MIT 