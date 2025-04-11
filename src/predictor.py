import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import mediapipe as mp  # MediaPipe kütüphanesi

# MediaPipe el izleme modüllerini başlat
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

class ASLPredictor:
    def __init__(self, model_path, label_encoder, image_size=(64, 64), use_grayscale=False):
        """
        ASL İşaret Dili Tahmin Edici sınıfı.
        
        Args:
            model_path: Eğitilmiş model dosya yolu
            label_encoder: Etiket kodlayıcı
            image_size: Görüntü boyutu
            use_grayscale: Gri tonlama kullanılsın mı?
        """
        self.model = load_model(model_path)
        self.label_encoder = label_encoder
        self.class_names = label_encoder.classes_
        self.use_grayscale = use_grayscale
        
        # Modelin beklediği giriş şeklini kontrol et
        self.expected_input_shape = self.model.input_shape[1:]
        
        # Otomatik olarak modelin beklediği görüntü boyutunu kullan
        self.image_size = (self.expected_input_shape[0], self.expected_input_shape[1])
        
        # Model özetini yazdır
        print("Model yüklendi:")
        print(f"Giriş boyutu: {self.model.input_shape}")
        print(f"Çıkış boyutu: {self.model.output_shape}")
        print(f"Sınıf sayısı: {len(self.class_names)}")
        
        # Eğer use_grayscale belirtilmemişse, modelin kanal sayısına bakarak otomatik belirle
        if self.expected_input_shape[-1] == 1:
            self.use_grayscale = True
            print("Model gri tonlamalı görüntü bekliyor (1 kanal)")
        else:
            print(f"Model {self.expected_input_shape[-1]} kanallı görüntü bekliyor")
        
        print(f"Model için görüntü boyutu: {self.image_size} olarak ayarlandı")
        
        # Sınıf ağırlıkları - yanlış pozitif oranını azaltmak için
        # 'b' harfi için daha sıkı bir eşik değeri kullanacağız
        self.class_weights = {}
        for class_name in self.class_names:
            self.class_weights[class_name] = 1.0
        
        # 'b' harfi için daha yüksek güven gerektir (ağırlığı azalt)
        if 'b' in self.class_weights:
            self.class_weights['b'] = 0.7  # b harfi için 0.7 çarpanı uygula
        
        # 'a', 'c', 'bye' için ağırlıkları artır (hafifçe teşvik et)
        problem_classes = ['a', 'c', 'bye', 'o']
        for cls in problem_classes:
            if cls in self.class_weights:
                self.class_weights[cls] = 1.2
        
        print("Sınıf ağırlıkları yapılandırıldı")
        
        # Minimum güven eşikleri
        self.min_confidence = 0.4  # Genel minimum güven
        self.class_thresholds = {
            'b': 0.7,  # 'b' tahminleri için daha yüksek eşik
        }
        
        print("Minimum güven eşikleri yapılandırıldı")
    
    def preprocess_image(self, image):
        """
        Görüntüyü ön işlemden geçirir.
        
        Args:
            image: İşlenecek görüntü
            
        Returns:
            processed_image: İşlenmiş görüntü
        """
        # Modelin beklediği boyuta yeniden boyutlandır
        resized = cv2.resize(image, self.image_size)
        
        # Modelin beklentisine göre işle
        if self.use_grayscale:
            # Gri tonlamaya dönüştür
            if len(resized.shape) == 3 and resized.shape[2] == 3:
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                # Tek kanallı olarak yeniden şekillendir
                processed = gray.reshape(self.image_size[0], self.image_size[1], 1)
            else:
                processed = resized
        else:
            # Renkli görüntü (3 kanal)
            processed = resized
        
        # Normalize et
        normalized = processed.astype('float32') / 255.0
        
        # Batch boyutunu ekle
        batch = np.expand_dims(normalized, axis=0)
        
        return batch
    
    def predict(self, image):
        """
        Görüntüyü tahmin eder.
        
        Args:
            image: Tahmin edilecek görüntü
            
        Returns:
            predicted_class: Tahmin edilen sınıf
            confidence: Tahmin güveni
            all_predictions: Tüm tahminler ve güven değerleri (sıralı)
        """
        # Görüntüyü işle
        processed_image = self.preprocess_image(image)
        
        # Tahmin yap
        predictions = self.model.predict(processed_image, verbose=0)[0]
        
        # Tahminlere ağırlık uygula
        weighted_predictions = predictions.copy()
        for i, class_name in enumerate(self.class_names):
            if class_name in self.class_weights:
                weighted_predictions[i] *= self.class_weights[class_name]
        
        # Tahminleri güven değerine göre sırala
        sorted_indices = np.argsort(weighted_predictions)[::-1]  # En yüksekten en düşüğe
        
        # En yüksek olasılıklı sınıfı bul
        top_index = sorted_indices[0]
        confidence = predictions[top_index]  # Orijinal (ağırlıksız) güven değeri
        predicted_class = self.label_encoder.inverse_transform([top_index])[0]
        
        # Sınıf-spesifik güven eşiğini kontrol et
        threshold = self.class_thresholds.get(predicted_class, self.min_confidence)
        
        # Eğer güven eşiğinin altındaysa veya 'b' tahminini doğrulamak istiyorsak
        if confidence < threshold or predicted_class == 'b':
            # İlk 3 tahmini hesapla
            top_3_indices = sorted_indices[:3]
            top_3_classes = self.label_encoder.inverse_transform(top_3_indices)
            top_3_confidences = predictions[top_3_indices]
            
            # b harfi için özel kontrol
            if predicted_class == 'b':
                # Eğer 2. tahmin 'a', 'c' veya 'bye' ise ve yeterince yüksek güvene sahipse
                if top_3_classes[1] in ['a', 'c', 'bye', 'o'] and top_3_confidences[1] > 0.25:
                    # Güvenler arasındaki fark yeterince az ise, 2. tahmini kullan
                    confidence_diff = top_3_confidences[0] - top_3_confidences[1]
                    if confidence_diff < 0.2:  # %20'den az fark varsa
                        predicted_class = top_3_classes[1]
                        confidence = top_3_confidences[1]
        
        # Tüm tahminleri hazırla
        all_predictions = []
        for idx in sorted_indices[:5]:  # İlk 5 tahmini döndür
            all_predictions.append({
                'class': self.label_encoder.inverse_transform([idx])[0],
                'confidence': float(predictions[idx]),
                'weighted_confidence': float(weighted_predictions[idx])
            })
        
        return predicted_class, confidence, all_predictions

def hand_detection(frame):
    """
    Kare içindeki el bölgesini tespit eder.
    
    Args:
        frame: Kamera karesi
        
    Returns:
        hand_region: El bölgesi
        roi_box: El bölgesinin koordinatları (x, y, w, h)
        hand_detected: El tespit edildi mi?
        hand_landmarks: El iskeletinin nokta bilgileri (varsa)
    """
    # Geliştirilmiş ROI (İlgi Bölgesi) kırpma
    height, width = frame.shape[:2]
    
    # MediaPipe ile el tespiti
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,  # Sadece bir el tespiti yapıyoruz
        min_detection_confidence=0.5,  # 0.5 minimum güven eşiği
        model_complexity=1  # Orta seviye karmaşıklık (0=hızlı, 1=orta, 2=yüksek kalite)
    ) as hands:
        
        # BGR -> RGB dönüşümü (MediaPipe RGB formatı bekler)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # İşlemeyi verimli hale getirmek için görüntüyü değişmez olarak işaretle
        rgb_frame.flags.writeable = False
        
        # El tespiti yap
        results = hands.process(rgb_frame)
        
        # Görüntüyü tekrar yazılabilir hale getir
        rgb_frame.flags.writeable = True
    
    # MediaPipe ile el tespit edildi mi?
    mp_hand_detected = results.multi_hand_landmarks is not None
    
    # Eğer el tespit edilmediyse standart merkez bölgeyi kullan
    if not mp_hand_detected:
        # Standart merkez bölge için koordinatlar
    box_size = min(height, width) // 2
    x = (width - box_size) // 2
    y = (height - box_size) // 2
        roi = frame[y:y+box_size, x:x+box_size].copy() if y+box_size <= height and x+box_size <= width else np.zeros((box_size, box_size, 3), dtype=np.uint8)
        roi_box = (x, y, box_size, box_size)
        hand_landmarks = None
        return roi, roi_box, False, hand_landmarks
    
    # El noktalarının sınırlarını belirle
    landmarks = results.multi_hand_landmarks[0].landmark
    landmark_points = []
    
    for landmark in landmarks:
        # Koordinatları piksel konumlarına dönüştür
        landmark_x = int(landmark.x * width)
        landmark_y = int(landmark.y * height)
        landmark_points.append((landmark_x, landmark_y))
    
    # El sınırlarını belirle (biraz boşluk bırakarak)
    padding = 30  # El bölgesi etrafında daha fazla boşluk bırak
    min_x = max(0, min([pt[0] for pt in landmark_points]) - padding)
    min_y = max(0, min([pt[1] for pt in landmark_points]) - padding)
    max_x = min(width, max([pt[0] for pt in landmark_points]) + padding)
    max_y = min(height, max([pt[1] for pt in landmark_points]) + padding)
    
    # Karesel bir bölge elde etmek için
    box_size = max(max_x - min_x, max_y - min_y)
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    
    # Kare bölgeyi belirle
    x = max(0, center_x - box_size // 2)
    y = max(0, center_y - box_size // 2)
    box_size = min(box_size, min(width - x, height - y))
    
    # Görüntü sınırları dışına çıkmadığından emin ol
    if x + box_size > width:
        x = width - box_size
    if y + box_size > height:
        y = height - box_size
    
    # İlgili bölgeyi kırp
    roi = frame[y:y+box_size, x:x+box_size].copy() if y+box_size <= height and x+box_size <= width else np.zeros((box_size, box_size, 3), dtype=np.uint8)
    
    # Kare koordinatları
    roi_box = (x, y, box_size, box_size)
    
    # Hand landmarks bilgisini döndürmek için
    hand_landmarks = results.multi_hand_landmarks[0]
    
    return roi, roi_box, True, hand_landmarks

def start_webcam_prediction(predictor, camera_id=0, flip_image=True, exit_key='q'):
    """
    Webcam görüntüsünden gerçek zamanlı tahmin yapar.
    
    Args:
        predictor: ASLPredictor nesnesi
        camera_id: Kamera ID'si
        flip_image: Görüntü yatay çevrilsin mi?
        exit_key: Çıkış tuşu
    """
    print(f"Kamera {camera_id} açılıyor...")
    
    # Kamerayı başlat
    cap = cv2.VideoCapture(camera_id)
    
    # MediaPipe el çizim modülünü başlat
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    # Kamera açılma durumunu kontrol et
    if not cap.isOpened():
        print(f"Hata: Kamera {camera_id} açılamadı!")
        
        # Farklı kamera ID'lerini dene (0-4 arası)
        available_cameras = []
        for test_id in range(5):
            if test_id == camera_id:
                continue
                
            print(f"Alternatif kamera {test_id} deneniyor...")
            test_cap = cv2.VideoCapture(test_id)
            
            if test_cap.isOpened():
                available_cameras.append(test_id)
                print(f"Kamera {test_id} kullanılabilir durumda.")
                test_cap.release()
            else:
                print(f"Kamera {test_id} kullanılamıyor.")
        
        if available_cameras:
            print(f"Kullanılabilir kameralar: {available_cameras}")
            print(f"Lütfen --camera-id={available_cameras[0]} parametresi ile tekrar deneyin.")
        else:
            print("Hiçbir kamera bulunamadı! Lütfen kamera bağlantınızı kontrol edin.")
        
        return
    
    # Kamera açıldı, özelliklerini kontrol et
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Kamera başarıyla açıldı!")
    print(f"Kamera özellikleri: {width}x{height}, {fps} FPS")
    
    # Test amacıyla ilk kareyi al
    ret, test_frame = cap.read()
    if not ret or test_frame is None:
        print("Uyarı: İlk kare okunamadı! Kamera düzgün çalışmıyor olabilir.")
        cap.release()
        return
    
    print(f"İlk test karesi başarıyla alındı. Boyut: {test_frame.shape}")
    
    # OpenCV penceresi oluştur ve konumlandır
    window_name = "İşaret Dili Tanıma"
    debug_window = "El Bölgesi (Debug)"
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.moveWindow(window_name, 100, 100)  # Pencereyi görünür bir konuma taşı
    cv2.resizeWindow(window_name, 800, 600)  # Pencere boyutunu ayarla
    
    cv2.namedWindow(debug_window, cv2.WINDOW_NORMAL)
    cv2.moveWindow(debug_window, 900, 100)  # Debug penceresini ana pencerenin yanına yerleştir
    cv2.resizeWindow(debug_window, 400, 400)  # Debug penceresi boyutunu ayarla
    
    # Son 10 tahminin ortalamasını almak için liste
    recent_predictions = []
    smoothing_window = 10
    
    # Alternatif tahminleri izlemek için
    alt_predictions = {}  # {sınıf: sayı} şeklinde sayacı tutacak
    
    # Düzeltme kontrol sayacı
    correction_counter = {'total': 0, 'corrected': 0}
    
    # Boş çerçeve tespit sayacı
    empty_scene_counter = 0
    
    print(f"Webcam başlatıldı. Çıkmak için '{exit_key}' tuşuna basın.")
    print("NOT: Yalnızca MediaPipe el tespiti kullanılıyor, ten rengi tespiti devre dışı.")
    
    frame_count = 0
    empty_frame_count = 0
    max_empty_frames = 10  # Arka arkaya 10 boş kare alırsak hata ver
    
    try:
    while True:
        # Kare oku
        ret, frame = cap.read()
        
            if not ret or frame is None:
                empty_frame_count += 1
                print(f"Uyarı: Boş kare! ({empty_frame_count}/{max_empty_frames})")
                
                if empty_frame_count >= max_empty_frames:
                    print("Hata: Kamera veri akışı yok. Lütfen kamera bağlantınızı kontrol edin.")
            break
                
                # Kısa bir süre bekle ve tekrar dene
                cv2.waitKey(100)
                continue
            
            # Başarılı bir kare aldık, sayacı sıfırla
            empty_frame_count = 0
            frame_count += 1
            
            # İlk kare bilgisi
            if frame_count == 1:
                print(f"İlk görüntü karesi başarıyla işleniyor. Boyut: {frame.shape}")
                # Test amaçlı ilk kareyi kaydet
                test_file = "test_camera_frame.jpg"
                cv2.imwrite(test_file, frame)
                print(f"Test karesi kaydedildi: {test_file}")
        
        # Görüntüyü çevir (ayna efekti)
        if flip_image:
            frame = cv2.flip(frame, 1)
        
            # Kamera görüntü boyutunu küçült (büyük görüntüler için, daha hızlı işlem)
            display_frame = cv2.resize(frame, (0, 0), fx=0.7, fy=0.7)
            
            # El bölgesini al ve el tespit edilip edilmediğini kontrol et
            hand_roi, roi_box, hand_detected, hand_landmarks = hand_detection(frame)
            
            # Debug ekranı için elle ilgili ek bilgiler
            debug_image = hand_roi.copy()
            
            # Çerçeveyi çiz - el tespiti durumuna göre renk değiştir
        x, y, w, h = roi_box
            rect_color = (0, 255, 0) if hand_detected else (0, 0, 255)  # Yeşil veya kırmızı
            cv2.rectangle(display_frame, (int(x*0.7), int(y*0.7)), 
                        (int((x+w)*0.7), int((y+h)*0.7)), rect_color, 2)
            
            # MediaPipe el iskeletini ekle - Tüm çerçeveye çizim
            if hand_landmarks:
                # İskelet çizimini ekle
                mp_drawing.draw_landmarks(
                    display_frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())
                
                # Debug ekranı için el iskeleti
                hand_copy = debug_image.copy()
                mp_drawing.draw_landmarks(
                    hand_copy,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())
                
                # El noktaları hakkında bilgi
                cv2.putText(debug_image, "MediaPipe El Tespiti: BAŞARILI", (10, hand_copy.shape[0]-40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # El iskeletini saydam bir şekilde debug ekranına ekle
                alpha = 0.7  # Saydamlık seviyesi
                beta = 1.0 - alpha
                debug_image = cv2.addWeighted(debug_image, alpha, hand_copy, beta, 0.0)
                
                # El tespiti bilgisi
                cv2.putText(display_frame, "El tespit edildi", (10, display_frame.shape[0]-50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # El tespit edilmediyse, tahmin yapmadan geç ve kullanıcıya bilgi ver
            if not hand_detected:
                empty_scene_counter += 1
                
                # Kullanıcıya bilgi ver
                status_text = "El tespit edilemedi! Lütfen elinizi gösterin."
                cv2.putText(display_frame, status_text, 
                           (10, display_frame.shape[0]-20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Debug ekranında durum bilgisi göster
                cv2.putText(debug_image, "MediaPipe el tespit edemedi!", (10, 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Boş durum istatistiği
                cv2.putText(display_frame, f"Boş çerçeve sayısı: {empty_scene_counter}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
                
                # Son tahminleri temizle - boş çerçevede önceki tahminleri tutmamak için
                recent_predictions = []
                
                # Görüntüleri göster
                cv2.imshow(window_name, display_frame)
                cv2.imshow(debug_window, debug_image)
                
                # Devam etmeden önce tuş kontrolü
                key = cv2.waitKey(1) & 0xFF
                if key == ord(exit_key):
                    print("Kullanıcı çıkış yaptı.")
                    break
                continue
            
            # Tahmin yap (el tespit edildiğinde)
            try:
                # Yeni predict metodu 3 değer döndürüyor: tahmin, güven ve tüm tahminler
                predicted_class, confidence, all_predictions = predictor.predict(hand_roi)
                
                # Minimum güven kontrolü - düşük güvenli tahminleri gösterme
                min_display_confidence = 0.35  # %35'den düşük güvenli tahminleri gösterme
                if confidence < min_display_confidence:
                    # Düşük güvenli tahmin - gösterme
                    status_text = f"Düşük güven: {confidence:.2f} - Tekrar deneyin!"
                    cv2.putText(display_frame, status_text, (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Debug ekranında düşük güven bilgisi
                    cv2.putText(debug_image, f"Düşük güven: {confidence:.2f}", (10, 200), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Son tahminleri temizle - düşük güven durumunda önceki tahminleri tutmamak için
                    recent_predictions = []
                else:
                    # Eski versiyon uyumluluğu için
                    if isinstance(all_predictions, list):
                        # Bu, güncellenen predict metodunu kullanıyoruz
                        raw_pred = all_predictions[0]['class']  # İlk sıradaki tahmin
                        if raw_pred == 'b' and predicted_class != 'b':
                            correction_counter['total'] += 1
                            correction_counter['corrected'] += 1
                            debug_note = f"Düzeltme: b -> {predicted_class} (Güven: {confidence:.2f})"
                        elif raw_pred != 'b' and predicted_class == 'b':
                            # Bu durumda düzeltme yapmamış, b'ye çevirmişiz (istenmeyen)
                            debug_note = f"Ters Düzeltme: {raw_pred} -> b (Güven: {confidence:.2f})"
                        else:
                            debug_note = ""
                    else:
                        # Eski predict metodu (geriye uyumluluk için)
                        all_predictions = []
                        debug_note = ""
            
            # Tahminleri kaydet
            recent_predictions.append((predicted_class, confidence))
            if len(recent_predictions) > smoothing_window:
                recent_predictions.pop(0)
            
            # En sık tahmini bul
            prediction_counts = {}
            for pred, conf in recent_predictions:
                if pred in prediction_counts:
                    prediction_counts[pred] += 1
                else:
                    prediction_counts[pred] = 1
            
                    # Alternatif tahminleri hesapla (ilk 3 en yüksek tahmin)
                    sorted_predictions = sorted(prediction_counts.items(), key=lambda x: x[1], reverse=True)
                    
                    # En yaygın tahmin
                    most_common_prediction = sorted_predictions[0][0]
            prediction_ratio = prediction_counts[most_common_prediction] / len(recent_predictions)
            
            # Yeterince kararlı ise tahmini göster
                    if prediction_ratio > 0.5:  # Tahminlerin en az %50'si aynı ise
                        # Ana tahmini göster
            display_text = f"{most_common_prediction}"
                        cv2.putText(display_frame, display_text, (int(x*0.7), int(y*0.7)-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                        
                        # Alternatif tahminleri göster (en fazla 2 alternatif)
                        alt_y_pos = int(y*0.7) + int(h*0.7) + 30
                        cv2.putText(display_frame, "Alternatif tahminler:", (10, alt_y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
                        for i in range(1, min(3, len(sorted_predictions))):
                            alt_class, alt_count = sorted_predictions[i]
                            alt_ratio = alt_count / len(recent_predictions)
                            cv2.putText(display_frame, 
                                    f"{i}. {alt_class} ({alt_ratio:.2f})", 
                                    (10, alt_y_pos + i*25), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)
            
            # Güven değerini göster
            avg_confidence = np.mean([conf for pred, conf in recent_predictions if pred == most_common_prediction])
                    cv2.putText(display_frame, f"Güven: {avg_confidence:.2f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Düzeltme istatistiklerini göster
                    if correction_counter['total'] > 0:
                        correction_text = f"Düzeltme: {correction_counter['corrected']}/{correction_counter['total']}"
                        cv2.putText(display_frame, correction_text, (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
            
            # Kullanıcıya bilgi ver
                    cv2.putText(display_frame, "El işaretinizi kare içine yerleştirin", 
                            (10, display_frame.shape[0]-20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    # Debug penceresine tahmin bilgilerini ekle
                    cv2.putText(debug_image, f"Tahmin: {most_common_prediction}", (10, 25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Debug notunu ekle
                    if debug_note:
                        cv2.putText(debug_image, debug_note, (10, debug_image.shape[0]-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
                    
                    # Tüm orijinal tahminleri göster
                    if isinstance(all_predictions, list) and len(all_predictions) > 0:
                        cv2.putText(debug_image, "Raw Tahminler:", (10, 55), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
                        for i, pred_info in enumerate(all_predictions):
                            cls = pred_info['class']
                            conf = pred_info['confidence']
                            weighted = pred_info['weighted_confidence']
                            
                            # Özel renk kodlaması - 'b' kırmızı, 'a', 'c', 'bye', 'o' mavi, diğerleri beyaz
                            color = (255, 255, 255)  # beyaz
                            if cls == 'b':
                                color = (0, 0, 255)  # kırmızı
                            elif cls in ['a', 'c', 'bye', 'o']:
                                color = (255, 0, 0)  # mavi
                                
                            cv2.putText(debug_image, 
                                    f"{cls}: {conf:.2f} (w:{weighted:.2f})", 
                                    (10, 75 + i*20), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                    # Debug penceresine alternatif tahminleri ekle
                    for i in range(1, min(3, len(sorted_predictions))):
                        alt_class, alt_count = sorted_predictions[i]
                        alt_ratio = alt_count / len(recent_predictions)
                        cv2.putText(debug_image, 
                                f"Alt-{i}: {alt_class} ({alt_ratio:.2f})", 
                                (10, 180 + i*25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 2)
            
        except Exception as e:
            print(f"Tahmin hatası: {e}")
                cv2.putText(debug_image, f"Hata: {e}", (10, 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
            # Görüntüleri göster
            cv2.imshow(window_name, display_frame)
            cv2.imshow(debug_window, debug_image)
        
            # Kullanıcının görebilmesi için görüntüyü biraz beklet
        key = cv2.waitKey(1) & 0xFF
        if key == ord(exit_key):
                print("Kullanıcı çıkış yaptı.")
            break
    
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
    
    finally:
        # Kaynakları serbest bırak
        print("Kamera kapatılıyor...")
    cap.release()
    cv2.destroyAllWindows()
        print("Program sonlandırıldı.")

def predict_from_image(predictor, image_path):
    """
    Dosyadan bir görüntü üzerinde tahmin yapar.
    
    Args:
        predictor: ASLPredictor nesnesi
        image_path: Görüntü dosya yolu
        
    Returns:
        predicted_class: Tahmin edilen sınıf
        confidence: Tahmin güveni
    """
    # Görüntüyü oku
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError(f"Görüntü okunamadı: {image_path}")
    
    # Tahmin yap (güncellenmiş fonksiyonla uyumlu)
    try:
        predicted_class, confidence, all_predictions = predictor.predict(image)
    except ValueError:  # Eski versiyonla uyumluluk için
    predicted_class, confidence = predictor.predict(image)
        all_predictions = []
    
    print(f"Tahmin: {predicted_class}")
    print(f"Güven: {confidence:.4f}")
    
    if len(all_predictions) > 0:
        print("\nTüm tahminler:")
        for pred in all_predictions:
            print(f"  {pred['class']}: {pred['confidence']:.4f} (Ağırlıklı: {pred['weighted_confidence']:.4f})")
    
    # Görüntüyü göster
    cv2.putText(image, f"{predicted_class} ({confidence:.2f})", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Alternatif tahminleri göster
    if len(all_predictions) > 1:
        for i, pred in enumerate(all_predictions[1:4]):  # İlk 3 alternatif
            cv2.putText(image, f"{i+1}. {pred['class']} ({pred['confidence']:.2f})", 
                      (10, 60 + i*25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 1)
    
    cv2.imshow("Tahmin", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return predicted_class, confidence 