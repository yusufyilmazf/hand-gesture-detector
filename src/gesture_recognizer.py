import cv2
import numpy as np
import mediapipe as mp
import math

# MediaPipe el izleme modüllerini başlat
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

class GestureRecognizer:
    """
    Temel el hareketlerini (kalp, başparmak yukarı, başparmak aşağı, ok vb.) tanımak için sınıf.
    """
    
    def __init__(self):
        """
        Hareket tanıma sınıfını başlatır.
        """
        # El noktaları indeksleri:
        # MediaPipe el izleme noktaları: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
        # 0: Bilek
        # 1-4: Başparmak (1: taban, 4: uç)
        # 5-8: İşaret parmağı
        # 9-12: Orta parmak
        # 13-16: Yüzük parmağı
        # 17-20: Serçe parmak
        
        # Parmak uçları
        self.FINGER_TIPS = [4, 8, 12, 16, 20]  # Başparmak, işaret, orta, yüzük, serçe
        
        # Parmak orta eklemleri
        self.FINGER_MIDDLE = [3, 7, 11, 15, 19]  # Başparmak, işaret, orta, yüzük, serçe
        
        # Parmak taban eklemleri
        self.FINGER_BASE = [2, 6, 10, 14, 18]  # Başparmak, işaret, orta, yüzük, serçe
        
        # Başparmak özel bölümleri
        self.THUMB_CMC = 1  # Başparmak taban eklemi (carpometacarpal)
        self.THUMB_MCP = 2  # Başparmak orta eklemi (metacarpophalangeal)
        self.THUMB_IP = 3   # Başparmak iç eklemi (interphalangeal)
        self.THUMB_TIP = 4  # Başparmak ucu
        
        # Bilek
        self.WRIST = 0
        
        # Tanınabilecek hareketler - Türkçe karakter sorunlarını önlemek için ASCII karakterlere çevir
        self.GESTURES = {
            "thumbs_up": "Basparmak Yukari",
            "thumbs_down": "Basparmak Asagi",
            "peace": "Baris Isareti",
            "ok": "Tamam Isareti",
            "fist": "Yumruk",
            "open_hand": "Acik El",
            "pointing": "Isaret",
            "heart": "Kalp",
            "rock": "Rock Isareti",
            "pinch": "Tutma Hareketi",
            "gun": "Silah Isareti",
            "count_one": "Bir",
            "count_two": "Iki",
            "phone": "Telefon"
        }
        
        # Hareket tanıma için güven eşikleri
        self.angle_threshold = 60  # Derece cinsinden
        self.distance_threshold = 0.1  # Normalize edilmiş mesafe
    
    def recognize_gesture(self, hand_landmarks, img_shape=None):
        """
        El landmark noktalarından hareketi tanır.
        
        Args:
            hand_landmarks: MediaPipe el landmark noktaları
            img_shape: Görüntü boyutu (isteğe bağlı)
            
        Returns:
            gesture_name: Tanınan hareketin adı
            confidence: Tanıma güveni
        """
        if hand_landmarks is None:
            return "unknown", 0.0
        
        # Parmak açıklıklarını kontrol et
        fingers_extended = self._count_fingers_extended(hand_landmarks)
        
        # Başparmak yönünü kontrol et
        thumb_direction = self._check_thumb_direction(hand_landmarks)
        
        # Özel el hareketlerini kontrol et
        
        # Başparmak Yukarı: Sadece başparmak açık, diğerleri kapalı ve başparmak yukarı yönde
        if fingers_extended == [1, 0, 0, 0, 0] and thumb_direction == "up":
            return "thumbs_up", 0.9
        
        # Başparmak Aşağı: Sadece başparmak açık, diğerleri kapalı ve başparmak aşağı yönde
        if fingers_extended == [1, 0, 0, 0, 0] and thumb_direction == "down":
            return "thumbs_down", 0.9
        
        # Barış İşareti: İşaret ve orta parmak açık, diğerleri kapalı
        if fingers_extended == [0, 1, 1, 0, 0]:
            # İşaret ve orta parmağın ayrılma açısını kontrol et
            angle = self._calculate_angle_between_fingers(hand_landmarks, 8, 12)
            if angle > 20:  # Parmakların ayrılma açısı
                return "peace", 0.85
        
        # Tamam İşareti: Başparmak ve işaret parmağı birleşik, diğerleri açık
        if fingers_extended[0] == 1:  # Başparmak açık
            # Başparmak ve işaret parmağı uçları arasındaki mesafeyi kontrol et
            distance = self._calculate_distance(hand_landmarks, 4, 8)
            if distance < 0.07:  # Daha hassas mesafe kontrolü
                return "ok", 0.85
        
        # Yumruk: Tüm parmaklar kapalı
        if fingers_extended == [0, 0, 0, 0, 0]:
            return "fist", 0.85
        
        # Açık El: Tüm parmaklar açık
        if fingers_extended == [1, 1, 1, 1, 1]:
            # Parmaklar arasındaki açının çok dar olmamasını kontrol et
            angles = []
            for i in range(1, 5):  # İşaret-serçe arası parmaklar
                angles.append(self._calculate_angle_between_fingers(hand_landmarks, 
                                                                  self.FINGER_TIPS[i-1], 
                                                                  self.FINGER_TIPS[i]))
            avg_angle = sum(angles) / len(angles)
            if avg_angle > 15:  # Ortalama parmak açıklığı
                return "open_hand", 0.8
        
        # İşaret: Sadece işaret parmağı açık
        if fingers_extended == [0, 1, 0, 0, 0]:
            return "pointing", 0.85
        
        # Rock İşareti: Sadece serçe parmak ve işaret parmağı açık
        if fingers_extended == [0, 1, 0, 0, 1]:
            return "rock", 0.85
        
        # Tutma Hareketi: Başparmak ve işaret parmağı uçları yakın
        if fingers_extended[1] == 1:  # İşaret parmağı açık
            # Başparmak ve işaret parmağı uçları arasındaki mesafeyi kontrol et
            distance = self._calculate_distance(hand_landmarks, 4, 8)
            if distance < 0.1:  # Normalize edilmiş mesafe
                return "pinch", 0.8
        
        # Silah İşareti: Başparmak yukarı, işaret parmağı açık, diğerleri kapalı
        if fingers_extended == [1, 1, 0, 0, 0] and thumb_direction == "up":
            angle = self._calculate_angle_between_fingers(hand_landmarks, 4, 8)
            if angle > 45:  # Başparmak ve işaret arasındaki açı
                return "gun", 0.85
        
        # Bir Sayma: Sadece işaret parmağı açık, elin yönü yukarı
        if fingers_extended == [0, 1, 0, 0, 0]:
            # İşaret parmağı yukarı doğru mu?
            index_tip = hand_landmarks.landmark[8]
            wrist = hand_landmarks.landmark[0]
            if index_tip.y < wrist.y:  # Parmak ucu bilekten yukarıda
                return "count_one", 0.9
        
        # İki Sayma: İşaret ve orta parmak açık, diğerleri kapalı
        if fingers_extended == [0, 1, 1, 0, 0]:
            # İşaret ve orta parmak yukarı doğru mu?
            index_tip = hand_landmarks.landmark[8]
            middle_tip = hand_landmarks.landmark[12]
            wrist = hand_landmarks.landmark[0]
            if index_tip.y < wrist.y and middle_tip.y < wrist.y:
                # Parmakların arasındaki açı küçük mü? (Bitişik sayma)
                angle = self._calculate_angle_between_fingers(hand_landmarks, 8, 12)
                if angle < 15:  # Parmaklar birbirine yakın
                    return "count_two", 0.9
        
        # Telefon İşareti: Başparmak ve serçe parmak açık, diğerleri kapalı
        if fingers_extended == [1, 0, 0, 0, 1]:
            # "Alo" pozisyonu
            thumb_tip = hand_landmarks.landmark[4]
            pinky_tip = hand_landmarks.landmark[20]
            ear_region = hand_landmarks.landmark[0].y - 0.1  # Kulak bölgesi tahmini
            
            # Başparmak ağız bölgesinde, serçe parmak kulak bölgesinde mi?
            if pinky_tip.y < ear_region:
                return "phone", 0.85
        
        # Kalp İşareti: Bu biraz karmaşık, başparmaklar ve işaret parmakları belirli bir şekilde
        # Kalp için özel bir hesaplama yapılabilir
        is_heart = self._check_heart_gesture(hand_landmarks)
        if is_heart:
            return "heart", 0.75
        
        # Tanınamadı
        return "unknown", 0.4
    
    def _count_fingers_extended(self, hand_landmarks):
        """
        Açık parmakları sayar.
        
        Args:
            hand_landmarks: MediaPipe el landmark noktaları
            
        Returns:
            extended_fingers: Her parmağın açık (1) veya kapalı (0) olduğunu gösteren liste
        """
        extended_fingers = []
        
        # Başparmak kontrolü (diğer parmaklardan farklı)
        # Başparmak CMC-MCP-IP açısını kontrol et
        finger_points = [hand_landmarks.landmark[self.THUMB_CMC],
                         hand_landmarks.landmark[self.THUMB_MCP],
                         hand_landmarks.landmark[self.THUMB_IP],
                         hand_landmarks.landmark[self.THUMB_TIP]]
        
        # Başparmak açılma yönünü kontrol et
        wrist_x = hand_landmarks.landmark[self.WRIST].x
        thumb_tip_x = hand_landmarks.landmark[self.THUMB_TIP].x
        
        # Sağ el için başparmak açıklığı kontrolü
        if wrist_x > thumb_tip_x:  # Sağ el
            extended_fingers.append(1 if finger_points[3].x < finger_points[1].x else 0)
        else:  # Sol el
            extended_fingers.append(1 if finger_points[3].x > finger_points[1].x else 0)
        
        # Diğer parmaklar (işaret, orta, yüzük, serçe) için
        for i in range(1, 5):
            finger_points = [
                hand_landmarks.landmark[self.FINGER_BASE[i]],  # Taban
                hand_landmarks.landmark[self.FINGER_MIDDLE[i]],  # Orta
                hand_landmarks.landmark[self.FINGER_TIPS[i]]   # Uç
            ]
            
            # Parmak ucu, orta eklemden daha yukarıdaysa parmak açıktır
            # Not: Y koordinatı ekranda yukarıdan aşağıya artar, yani daha küçük y daha yukarıdadır
            if finger_points[2].y < finger_points[1].y:
                extended_fingers.append(1)
            else:
                extended_fingers.append(0)
        
        return extended_fingers
    
    def _check_thumb_direction(self, hand_landmarks):
        """
        Başparmağın yönünü kontrol eder.
        
        Args:
            hand_landmarks: MediaPipe el landmark noktaları
            
        Returns:
            direction: Başparmağın yönü ('up', 'down', 'left', 'right')
        """
        thumb_tip = hand_landmarks.landmark[self.THUMB_TIP]
        thumb_base = hand_landmarks.landmark[self.THUMB_CMC]
        
        # Başparmak ucunun tabana göre konumu
        dx = thumb_tip.x - thumb_base.x
        dy = thumb_tip.y - thumb_base.y
        
        # Baskın yönü belirle
        if abs(dy) > abs(dx):  # Dikey hareket daha belirgin
            return "up" if dy < 0 else "down"
        else:  # Yatay hareket daha belirgin
            return "right" if dx > 0 else "left"
    
    def _calculate_angle_between_fingers(self, hand_landmarks, tip_idx1, tip_idx2):
        """
        İki parmak ucu arasındaki açıyı hesaplar.
        
        Args:
            hand_landmarks: MediaPipe el landmark noktaları
            tip_idx1: İlk parmak ucu indeksi
            tip_idx2: İkinci parmak ucu indeksi
            
        Returns:
            angle: İki parmak arasındaki açı (derece)
        """
        wrist = hand_landmarks.landmark[self.WRIST]
        tip1 = hand_landmarks.landmark[tip_idx1]
        tip2 = hand_landmarks.landmark[tip_idx2]
        
        # İki parmak ve bilek arasındaki vektörler
        v1 = [tip1.x - wrist.x, tip1.y - wrist.y]
        v2 = [tip2.x - wrist.x, tip2.y - wrist.y]
        
        # Vektörlerin modülleri
        v1_mag = math.sqrt(v1[0]**2 + v1[1]**2)
        v2_mag = math.sqrt(v2[0]**2 + v2[1]**2)
        
        # Vektörler arasındaki açının kosinüsü
        cos_angle = (v1[0]*v2[0] + v1[1]*v2[1]) / (v1_mag * v2_mag)
        
        # Kosinüs değerini -1 ile 1 arasında sınırla (sayısal hatalardan kaçınmak için)
        cos_angle = max(-1, min(1, cos_angle))
        
        # Açıyı derece cinsinden hesapla
        angle = math.degrees(math.acos(cos_angle))
        
        return angle
    
    def _calculate_distance(self, hand_landmarks, idx1, idx2):
        """
        İki landmark noktası arasındaki normalize edilmiş mesafeyi hesaplar.
        
        Args:
            hand_landmarks: MediaPipe el landmark noktaları
            idx1: İlk nokta indeksi
            idx2: İkinci nokta indeksi
            
        Returns:
            distance: İki nokta arasındaki normalize edilmiş mesafe
        """
        point1 = hand_landmarks.landmark[idx1]
        point2 = hand_landmarks.landmark[idx2]
        
        # 3D mesafe hesapla
        distance = math.sqrt((point1.x - point2.x)**2 + 
                           (point1.y - point2.y)**2 + 
                           (point1.z - point2.z)**2)
        
        return distance
    
    def _check_heart_gesture(self, hand_landmarks):
        """
        Kalp işareti olup olmadığını kontrol eder.
        Bu genellikle başparmaklar ve işaret parmakları ile yapılır.
        
        Args:
            hand_landmarks: MediaPipe el landmark noktaları
            
        Returns:
            is_heart: Kalp işareti ise True, değilse False
        """
        # Not: Bu basit bir implementasyon. Gerçek bir kalp hareketi tanıma için
        # iki el birden gerekir veya başparmak ve işaret parmağı özel konumlandırılmalıdır.
        # Bu basit sürümde, başparmak ve serçe parmağın yönü ve konumunu kontrol ediyoruz
        
        # Parmak uçları
        thumb_tip = hand_landmarks.landmark[self.THUMB_TIP]
        pinky_tip = hand_landmarks.landmark[self.FINGER_TIPS[4]]
        
        # Bilek
        wrist = hand_landmarks.landmark[self.WRIST]
        
        # Başparmak ve serçe parmak aşağı doğru mu?
        if thumb_tip.y > wrist.y and pinky_tip.y > wrist.y:
            # Parmakların konumları birbirine yakın mı?
            distance = self._calculate_distance(hand_landmarks, self.THUMB_TIP, self.FINGER_TIPS[4])
            
            # Parmakların yönü içe doğru mu?
            thumb_dir = self._check_thumb_direction(hand_landmarks)
            is_inward = (thumb_dir == "right" and thumb_tip.x < wrist.x) or (thumb_dir == "left" and thumb_tip.x > wrist.x)
            
            # İşaret ve orta parmaklar kapalı mı?
            fingers_extended = self._count_fingers_extended(hand_landmarks)
            if fingers_extended[1] == 0 and fingers_extended[2] == 0:
                return distance < 0.15 and is_inward
        
        return False
        
    def visualize_gesture(self, frame, hand_landmarks, gesture_name):
        """
        El hareketi tanımayı görselleştirir.
        
        Args:
            frame: Kamera karesi
            hand_landmarks: MediaPipe el landmark noktaları
            gesture_name: Tanınan hareketin adı
            
        Returns:
            frame: Görselleştirme eklenmiş kare
        """
        # El iskeletini çiz
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())
        
        # Tanınan hareketi ekle
        gesture_display_name = self.GESTURES.get(gesture_name, "Bilinmeyen Hareket")
        cv2.putText(frame, f"Hareket: {gesture_display_name}", 
                  (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)
        
        # Parmak açık/kapalı durumu
        fingers_extended = self._count_fingers_extended(hand_landmarks)
        fingers_text = "Parmaklar: " + "".join(["🖐️" if f else "👊" for f in fingers_extended])
        cv2.putText(frame, fingers_text, 
                  (10, 60), cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 0, 0), 2)
        
        return frame 