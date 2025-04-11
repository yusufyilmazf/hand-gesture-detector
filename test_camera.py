import cv2
import time

def test_camera(camera_id=0):
    """
    Kamera çalışmasını test eden basit bir fonksiyon.
    
    Args:
        camera_id: Kamera ID'si
    """
    print(f"Kamera {camera_id} test ediliyor...")
    
    # Kamerayı başlat
    cap = cv2.VideoCapture(camera_id)
    
    # Kamera açılabildi mi kontrol et
    if not cap.isOpened():
        print(f"Hata: Kamera {camera_id} açılamadı!")
        return False
    
    # Kamera özelliklerini al
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Kamera başarıyla açıldı! Özellikler: {width}x{height}, {fps} FPS")
    
    # Pencere oluştur
    window_name = f"Kamera {camera_id} Test"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, 100, 100)
    
    # 10 saniye için videoyu göster
    start_time = time.time()
    frame_count = 0
    
    try:
        while time.time() - start_time < 10:
            # Kare oku
            ret, frame = cap.read()
            
            if not ret:
                print("Kare okunamadı!")
                break
            
            frame_count += 1
            
            # İlk kare için detaylı bilgi yazdır
            if frame_count == 1:
                print(f"İlk kare başarıyla alındı! Boyut: {frame.shape}")
            
            # FPS bilgisini ekle
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Bilgilendirme metni ekle
            cv2.putText(frame, f"Kamera {camera_id} Test", (10, height-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Görüntüyü göster
            cv2.imshow(window_name, frame)
            
            # Çıkış kontrolü (q tuşu)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Test kullanıcı tarafından durduruldu.")
                break
    
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return False
    
    finally:
        # Kaynakları serbest bırak
        cap.release()
        cv2.destroyAllWindows()
    
    print(f"Test tamamlandı. Toplam {frame_count} kare işlendi.")
    return True

def test_all_cameras():
    """
    Sistemdeki tüm kameraları test eden fonksiyon.
    """
    print("Sistemdeki kameralar test ediliyor...")
    
    # İlk 5 kamera ID'sini dene
    available_cameras = []
    
    for camera_id in range(5):
        print(f"\nKamera {camera_id} test ediliyor...")
        cap = cv2.VideoCapture(camera_id)
        
        if cap.isOpened():
            available_cameras.append(camera_id)
            cap.release()
            print(f"Kamera {camera_id} kullanılabilir.")
        else:
            print(f"Kamera {camera_id} kullanılamıyor.")
    
    print(f"\nKullanılabilir kameralar: {available_cameras}")
    
    # Kullanıcıya hangi kamerayı test etmek istediğini sor
    if available_cameras:
        print("\nKullanılabilir bir kamerayı detaylı test etmek için seçin:")
        selected_id = available_cameras[0]  # Varsayılan olarak ilk kamerayı seç
        
        test_camera(selected_id)
    else:
        print("Hiçbir kamera bulunamadı!")

if __name__ == "__main__":
    # Tüm kameraları test et
    test_all_cameras()
    
    # Ya da belirli bir kamerayı test et
    # test_camera(0)  # Varsayılan kamerayı test et 