# El Hareketleri Tanıma Sistemi

Bu proje, kamera ile gerçek zamanlı olarak el hareketlerini tanıyan basit bir sistemdir. MediaPipe el izleme kütüphanesi kullanılarak geliştirilmiştir.

## ✨ Özellikler

- ✅ Gerçek zamanlı el hareketi tanıma
- ✅ Çeşitli temel el hareketlerini algılama (başparmak yukarı/aşağı, barış işareti, vb.)
- ✅ Basit ve anlaşılır kullanıcı arayüzü
- ✅ Görselleştirilen el iskeleti
- ✅ Tanınan hareketler için eylemler
- ✅ Çoklu platform desteği (Windows, Linux, macOS)

## 📋 Desteklenen Hareketler

Şu hareketler tanınabilir:

- 👍 **Başparmak Yukarı**: Sadece başparmak açık, yukarı doğru
- 👎 **Başparmak Aşağı**: Sadece başparmak açık, aşağı doğru
- ✌️ **Barış İşareti**: İşaret ve orta parmak açık, V şeklinde
- 👌 **Tamam İşareti**: Başparmak ve işaret parmağı birleşik, diğerleri açık
- ✊ **Yumruk**: Tüm parmaklar kapalı
- 🖐️ **Açık El**: Tüm parmaklar açık
- 👆 **İşaret**: Sadece işaret parmağı açık
- ❤️ **Kalp**: El parmaklarıyla oluşturulan kalp şekli
- 🤘 **Rock İşareti**: İşaret parmağı ve serçe parmak açık

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.7 veya üzeri
- OpenCV
- MediaPipe
- NumPy

### Bağımlılıkları Kurma

```bash
# Gerekli Python paketlerini yükleyin
pip install -r requirements.txt
```

### Çalıştırma

Kolay bir şekilde çalıştırmak için, dizinde bulunan başlatma betiğini kullanabilirsiniz:

```bash
# Betik ile başlatma (önerilir)
./run_demo.sh

# Özel parametreler ile başlatma
./run_demo.sh --camera 1 --resolution 1280x720

# Web uygulamasını başlatma

./run_web_app.sh

# manuel başlatma
python src\web_app.py
```

Alternatif olarak, Python betiğini doğrudan çalıştırabilirsiniz:

```bash
# Doğrudan Python betiğini çalıştırma
python3 src/gesture_demo.py --flip
```

## 🎮 Kullanım

1. Programı başlattığınızda, kameranızın görüntüsü açılacaktır
2. Elinizi kamera görüş alanına getirin
3. Sistem, elinizin hareketini tanıyacak ve ekranda gösterecektir
4. Çıkmak için 'q' tuşuna basın

## ⚙️ Komut Satırı Parametreleri

Uygulamayı özelleştirmek için aşağıdaki parametreleri kullanabilirsiniz:

- `--camera-id 0` : Kullanılacak kamera ID'si (varsayılan: 0)
- `--resolution 640x480` : Kamera çözünürlüğü (varsayılan: 640x480)
- `--flip` : Görüntüyü yatay çevirir (ayna etkisi)
- `--no-actions` : Eylemleri devre dışı bırakır

## 🔧 Yazılım Mimarisi

Bu uygulama üç ana bileşenden oluşur:

1. **GestureRecognizer**: El hareketlerini algılama ve tanıma
2. **GestureActions**: Tanınan hareketlere göre eylemler gerçekleştirme
3. **Demo Uygulaması**: Kullanıcı arayüzü ve ana program döngüsü

## 💡 Geliştirme

### Yeni Hareketler Ekleme

Yeni hareketler eklemek için, `src/gesture_recognizer.py` dosyasındaki `recognize_gesture` metodunu düzenleyin:

```python
# Örnek: Yeni bir hareket ekleme
if fingers_extended == [1, 0, 0, 1, 1]:  # Başparmak, yüzük ve serçe açık
    return "telefon", 0.85  # Telefon hareketi
```

Ayrıca, hareketi görselleştirmek için aynı dosyadaki `GESTURES` sözlüğüne ekleyin:

```python
self.GESTURES = {
    # ... mevcut hareketler ...
    "telefon": "Telefon İşareti",
}
```

### Yeni Eylemler Ekleme

Yeni bir eylem eklemek için, `src/gesture_actions.py` dosyasını düzenleyin:

1. Eylem metodunu ekleyin:
```python
def action_telefon(self, confidence):
    print(f"📞 Telefon açılıyor (Güven: {confidence:.2f})")
    self._play_sound("telefon.wav")
```

2. Eylemi sözlüklere kaydedin:
```python
self.actions = {
    # ... mevcut eylemler ...
    "telefon": self.action_telefon,
}

self.action_descriptions = {
    # ... mevcut açıklamalar ...
    "telefon": "Telefon açılıyor 📞",
}
```

## 📜 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👥 İletişim

Herhangi bir sorun, öneri veya geri bildirim için lütfen iletişime geçin.

---

**Not**: En iyi sonuçlar için, iyi aydınlatılmış bir ortamda, arka planınızın çok karmaşık olmadığı bir konumda kullanın. 
