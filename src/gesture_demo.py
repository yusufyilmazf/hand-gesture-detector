#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import mediapipe as mp
import time
import argparse
import locale
import os
from gesture_recognizer import GestureRecognizer
from gesture_actions import GestureActions

def main():
    """
    Temel el hareketlerini tanıyan demo uygulaması.
    """
    # Türkçe karakter desteği için locale ayarla
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        print("Türkçe dil desteği etkinleştirildi.")
    except locale.Error:
        try:
            # Alternatif olarak, daha genel bir Türkçe locale deneyin
            locale.setlocale(locale.LC_ALL, 'tr_TR')
            print("Türkçe dil desteği etkinleştirildi (alternatif).")
        except locale.Error:
            # Türkçe locale bulunamazsa, varsayılan UTF-8 kullan
            try:
                locale.setlocale(locale.LC_ALL, '')  # Sistem varsayılanı
                print("Sistem varsayılan dil desteği kullanılıyor.")
            except locale.Error:
                print("Uyarı: Dil desteği ayarlanamadı. Türkçe karakterlerde sorun olabilir.")
    
    # OpenCV'nin Türkçe karakter desteği için FONT_HERSHEY_COMPLEX kullanılabilir
    # veya ASCII olmayan karakterler için putText yerine freetype kullanılabilir
    
    # Argüman ayrıştırıcı
    parser = argparse.ArgumentParser(description='El Hareketi Tanıma Demo Uygulaması')
    parser.add_argument('--camera-id', type=int, default=0, help='Kamera ID')
    parser.add_argument('--flip', action='store_true', help='Görüntüyü yatay çevir (ayna etkisi)')
    parser.add_argument('--resolution', type=str, default='640x480', help='Çözünürlük (WxH formatında)')
    parser.add_argument('--no-actions', action='store_true', help='Eylemleri devre dışı bırak')
    parser.add_argument('--simple-ui', action='store_true', help='Basit kullanıcı arayüzü kullan')
    parser.add_argument('--dark-mode', action='store_true', help='Koyu tema kullan')
    parser.add_argument('--single-hand', action='store_true', help='Sadece tek el algılama modu')
    args = parser.parse_args()
    
    # Varsayılan olarak basit UI ve koyu tema kullan
    simple_ui = True
    dark_mode = True
    
    # Çözünürlüğü ayarla
    try:
        width, height = map(int, args.resolution.split('x'))
    except ValueError:
        print(f"Hatalı çözünürlük formatı: {args.resolution}. 'WxH' formatında olmalı (örn. 640x480)")
        width, height = 640, 480
    
    # Kamerayı başlat
    print(f"Kamera {args.camera_id} başlatılıyor...")
    cap = cv2.VideoCapture(args.camera_id)
    
    # Kamera açılamadıysa hata ver
    if not cap.isOpened():
        print(f"Hata: Kamera {args.camera_id} açılamadı!")
        return
    
    # Kamera özelliklerini ayarla
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Gerçek çözünürlüğü al
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Kamera başarıyla açıldı!")
    print(f"Çözünürlük: {actual_width}x{actual_height}, FPS: {fps}")
    
    # MediaPipe el izleme modülünü başlat
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    
    # El hareket tanıyıcıyı başlat
    gesture_recognizer = GestureRecognizer()
    
    # Eylemleri başlat (eğer devre dışı bırakılmadıysa)
    if not args.no_actions:
        gesture_actions = GestureActions()
        print("Eylemler etkinleştirildi.")
    else:
        gesture_actions = None
        print("Eylemler devre dışı bırakıldı.")
    
    # MediaPipe Hands modelini başlat - iki el tanıma için ayarlandı
    max_hands = 1 if args.single_hand else 2  # Tek el modu veya çift el modu
    hands_mode = "Tek el" if args.single_hand else "Çift el"
    print(f"{hands_mode} tanıma modu etkinleştirildi.")
    
    hands = mp_hands.Hands(
        static_image_mode=False,  # Video akışı için False
        max_num_hands=max_hands,  # İki el tespiti
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1  # 0=Lite, 1=Full
    )
    
    # FPS sayacı için değişkenler
    frame_count = 0
    start_time = time.time()
    fps_display = 0
    
    # Pencere oluştur
    window_name = "El Hareketi Tanima Demo"  # Türkçe karakter sorunu için ı -> i
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, actual_width, actual_height)
    
    # Tanınan son hareketi sakla
    current_gesture = None
    current_confidence = 0
    
    # Kalp tespiti için değişkenler
    left_hand_landmarks = None
    right_hand_landmarks = None
    heart_detected = False
    
    # Son eylem bilgisi
    last_action_text = ""
    last_action_time = 0
    action_display_duration = 3.0  # saniye
    
    # Basit kullanıcı arayüzü için font ve renkler
    # Türkçe karakter sorunları için FONT_HERSHEY_SIMPLEX yerine FONT_HERSHEY_COMPLEX kullanılabilir
    main_font = cv2.FONT_HERSHEY_COMPLEX
    main_color = (0, 255, 0)  # Yeşil
    shadow_color = (0, 0, 0)  # Siyah
    highlight_color = (255, 255, 0)  # Sarı
    
    # Renk teması (koyu mod)
    bg_color = (10, 10, 10)  # Çok koyu gri, neredeyse siyah
    panel_color = (40, 40, 40)  # Koyu gri
    text_color = (255, 255, 255)  # Beyaz
    
    print("Demo başlatıldı! Çıkmak için 'q' tuşuna basın.")
    
    try:
        while cap.isOpened():
            # Kameradan kare oku
            ret, frame = cap.read()
            
            if not ret:
                print("Kamera karesi okunamadı!")
                break
            
            # Görüntüyü çevir (ayna etkisi)
            if args.flip:
                frame = cv2.flip(frame, 1)
            
            # RGB formatına dönüştür (MediaPipe RGB bekler)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # İşlemeyi verimli hale getirmek için görüntüyü değişmez olarak işaretle
            rgb_frame.flags.writeable = False
            
            # El tespiti yap
            results = hands.process(rgb_frame)
            
            # Görüntüyü tekrar yazılabilir hale getir ve BGR'a çevir
            rgb_frame.flags.writeable = True
            
            # FPS hesapla
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time > 1.0:  # Her 1 saniyede bir güncelle
                fps_display = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
            
            # Arayüzü temizle
            overlay = frame.copy()
            # Yarı saydam arka plan oluştur - daha koyu ve belirgin yap
            cv2.rectangle(overlay, (0, 0), (actual_width, 120), bg_color, -1)
            alpha = 0.7  # Daha az saydam yap (0.5 -> 0.7)
            cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
            
            # Panel kenarlarını belirginleştir
            cv2.rectangle(frame, (0, 0), (actual_width, 120), panel_color, 2)
            
            # FPS metnini ekle (sadece köşede küçük olarak)
            cv2.putText(frame, f"FPS: {fps_display:.1f}", 
                      (actual_width - 100, 20), main_font, 0.5, text_color, 1)
            
            # El tespit modu bilgisini ekle
            hand_mode_text = "Mod: " + hands_mode
            cv2.putText(frame, hand_mode_text, 
                      (10, 20), main_font, 0.5, text_color, 1)
            
            # İki el arasında kalp tespiti için değişkenleri sıfırla
            left_hand_landmarks = None
            right_hand_landmarks = None
            heart_detected = False
            
            # Eğer el tespit edildiyse
            if results.multi_hand_landmarks:
                # Her el için
                multi_hand_landmarks = results.multi_hand_landmarks
                
                # Elleri belirleme (Sağ/Sol)
                if len(multi_hand_landmarks) == 2 and not args.single_hand:
                    # İki el varsa, hangi el sol/sağ olduğunu belirleme 
                    hand1_x = multi_hand_landmarks[0].landmark[0].x
                    hand2_x = multi_hand_landmarks[1].landmark[0].x
                    
                    # Ekranda solda görünen el (flip varsa gerçekte sağ el)
                    if hand1_x < hand2_x:
                        left_hand_landmarks = multi_hand_landmarks[0]
                        right_hand_landmarks = multi_hand_landmarks[1]
                    else:
                        left_hand_landmarks = multi_hand_landmarks[1]
                        right_hand_landmarks = multi_hand_landmarks[0]
                    
                    # İki elle kalp tespiti
                    heart_detected = check_heart_gesture_two_hands(left_hand_landmarks, right_hand_landmarks)
                    if heart_detected:
                        current_gesture = "heart"
                        current_confidence = 0.95  # İki elle kalp daha yüksek güven
                        
                        # Eylemi işle (eğer etkinse)
                        if gesture_actions:
                            action_performed, action_desc = gesture_actions.process_gesture("heart", current_confidence)
                            if action_performed:
                                last_action_text = action_desc
                                last_action_time = time.time()
                
                # Tek elde tanıma için
                for idx, hand_landmarks in enumerate(multi_hand_landmarks):
                    # El iskeletini çiz
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())
                    
                    # İki elle kalp tespit edilmediyse, normal tanıma
                    if not heart_detected:
                        # Hareketi tanı
                        gesture_name, confidence = gesture_recognizer.recognize_gesture(hand_landmarks)
                        
                        # Mevcut hareketi güncelle
                        if gesture_name != "unknown" and confidence > 0.6:
                            current_gesture = gesture_name
                            current_confidence = confidence
                            
                            # Eylemi işle (eğer etkinse)
                            if gesture_actions:
                                action_performed, action_desc = gesture_actions.process_gesture(gesture_name, confidence)
                                if action_performed:
                                    last_action_text = action_desc
                                    last_action_time = time.time()
            else:
                # El tespit edilemedi
                cv2.putText(frame, "El tespit edilemedi", 
                          (int(actual_width/2) - 120, 30), main_font, 0.7, shadow_color, 2)
                cv2.putText(frame, "El tespit edilemedi", 
                          (int(actual_width/2) - 120, 30), main_font, 0.7, (0, 0, 255), 1)
                current_gesture = None
                current_confidence = 0
            
            # Mevcut hareketi büyük olarak göster (eğer varsa)
            if current_gesture:
                # Hareket adını Türkçe olarak al
                gesture_display_name = gesture_recognizer.GESTURES.get(current_gesture, "Bilinmeyen Hareket")
                
                # ASCII olmayan karakterleri temizle veya değiştir
                # Bu sadece geçici bir çözüm, daha iyi bir yol FreeType2 kullanmak olacaktır
                gesture_display_name = gesture_display_name.replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c").replace("ı", "i")
                
                # Ekranın üst orta kısmında büyük yazı ile göster (gölgeli)
                text = f"{gesture_display_name}"
                text_size = cv2.getTextSize(text, main_font, 1.2, 2)[0]
                text_x = (actual_width - text_size[0]) // 2
                
                # Gölge metin
                cv2.putText(frame, text, 
                          (text_x, 60), main_font, 1.2, shadow_color, 3)
                # Ana metin
                cv2.putText(frame, text, 
                          (text_x, 60), main_font, 1.2, main_color, 2)
                
                # Güven değerini daha küçük göster
                confidence_text = f"Guven: %{int(current_confidence * 100)}"  # Türkçe karakterleri değiştir
                conf_text_size = cv2.getTextSize(confidence_text, main_font, 0.6, 1)[0]
                conf_x = (actual_width - conf_text_size[0]) // 2
                
                cv2.putText(frame, confidence_text, 
                          (conf_x, 90), main_font, 0.6, highlight_color, 1)
            
            # Son eylemi göster (eğer etkinse)
            if gesture_actions and last_action_text:
                current_time = time.time()
                if current_time - last_action_time < action_display_duration:
                    # ASCII olmayan karakterleri temizle veya değiştir
                    clean_action_text = last_action_text
                    clean_action_text = clean_action_text.replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c").replace("ı", "i")
                    
                    # Ekranın ortasında büyük yazı ile son eylemi göster
                    action_text_size = cv2.getTextSize(clean_action_text, main_font, 1.0, 2)[0]
                    action_x = (actual_width - action_text_size[0]) // 2
                    action_y = actual_height - 40
                    
                    # Gölge ve ana metin
                    cv2.putText(frame, clean_action_text, 
                              (action_x, action_y), main_font, 1.0, shadow_color, 4)
                    cv2.putText(frame, clean_action_text, 
                              (action_x, action_y), main_font, 1.0, (0, 255, 255), 2)
            
            # Kullanım bilgilerini ekle (sadece alt kısımda küçük olarak)
            instruction_text = "'q' tusu ile cikis"  # Türkçe karakterleri değiştir
            cv2.putText(frame, instruction_text, 
                      (10, actual_height - 10), main_font, 0.5, (200, 200, 200), 1)
            
            # Sonuçları göster
            cv2.imshow(window_name, frame)
            
            # Çıkış için 'q' tuşuna basılmasını kontrol et
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Kullanıcı çıkışı...")
                break
    
    except KeyboardInterrupt:
        print("Kullanıcı programı durdurdu!")
    
    except Exception as e:
        print(f"Hata: {e}")
    
    finally:
        # Kaynakları serbest bırak
        print("Temizleniyor...")
        if gesture_actions:
            gesture_actions.cleanup()
        cap.release()
        cv2.destroyAllWindows()
        print("Demo sonlandırıldı.")


def check_heart_gesture_two_hands(left_hand_landmarks, right_hand_landmarks):
    """
    İki el kullanarak kalp hareketi yapılıp yapılmadığını kontrol eder.
    
    Args:
        left_hand_landmarks: Sol el landmark noktaları
        right_hand_landmarks: Sağ el landmark noktaları
        
    Returns:
        bool: Kalp hareketi yapılıyorsa True, değilse False
    """
    if left_hand_landmarks is None or right_hand_landmarks is None:
        return False
    
    # Sol elin başparmak ve işaret parmağı uçları
    left_thumb_tip = left_hand_landmarks.landmark[4]
    left_index_tip = left_hand_landmarks.landmark[8]
    
    # Sağ elin başparmak ve işaret parmağı uçları
    right_thumb_tip = right_hand_landmarks.landmark[4]
    right_index_tip = right_hand_landmarks.landmark[8]
    
    # Her elin başparmak ve işaret parmağı arasındaki mesafe
    left_distance = ((left_thumb_tip.x - left_index_tip.x)**2 + 
                    (left_thumb_tip.y - left_index_tip.y)**2)**0.5
    
    right_distance = ((right_thumb_tip.x - right_index_tip.x)**2 + 
                     (right_thumb_tip.y - right_index_tip.y)**2)**0.5
    
    # İki elin birbirine yakınlığı
    hand_distance = ((left_thumb_tip.x - right_thumb_tip.x)**2 + 
                    (left_thumb_tip.y - right_thumb_tip.y)**2)**0.5
    
    # Başparmakların Y konumu (ekranda aşağı)
    thumbs_down = (left_thumb_tip.y > left_hand_landmarks.landmark[0].y and 
                  right_thumb_tip.y > right_hand_landmarks.landmark[0].y)
    
    # Kalp hareketi: 
    # 1. Her elin başparmak ve işaret parmakları açık olmalı (kısa mesafe)
    # 2. İki el birbirine yakın olmalı
    # 3. İki elin başparmakları aşağı doğru olmalı
    if left_distance < 0.15 and right_distance < 0.15 and hand_distance < 0.3 and thumbs_down:
        return True
    
    return False


if __name__ == "__main__":
    main() 