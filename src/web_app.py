#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cv2
import asyncio
import json
import threading
import numpy as np
import logging
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Union

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO

import mediapipe as mp
from gesture_recognizer import GestureRecognizer
from gesture_actions import GestureActions

# Flask uygulamasını oluştur
app = Flask(__name__)
app.config['SECRET_KEY'] = 'el_hareketi_tanima_gizli_anahtar'
socketio = SocketIO(app, cors_allowed_origins="*")

# Sınıfları başlat
gesture_recognizer = GestureRecognizer()
gesture_actions = GestureActions()

# Kamera nesnesi ve değişkenler
camera = None
camera_id = 0
frame_width = 640
frame_height = 480
flip_image = True
is_camera_running = False
is_processing = False
current_gesture = None
current_confidence = 0
heart_detected = False

# İki el izleme için değişkenler
max_hands = 2
show_skeleton = True

# MediaPipe Hands modelini başlat
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=max_hands,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

# Arayüz ayarları
main_font = cv2.FONT_HERSHEY_COMPLEX
main_color = (0, 255, 0)  # Yeşil
shadow_color = (0, 0, 0)  # Siyah
highlight_color = (255, 255, 0)  # Sarı
bg_color = (40, 40, 40)  # Koyu gri
panel_color = (70, 70, 70)  # Açık gri
text_color = (255, 255, 255)  # Beyaz

# Video akışı başlatma
def start_camera():
    global camera, is_camera_running, camera_id
    
    if camera is None:
        camera = cv2.VideoCapture(camera_id)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
    is_camera_running = True
    return camera.isOpened()

# Video akışı durdurma
def stop_camera():
    global camera, is_camera_running
    
    if camera is not None:
        is_camera_running = False
        camera.release()
        camera = None
    return True

# İki el arasında kalp tespiti
def check_heart_gesture_two_hands(left_hand_landmarks, right_hand_landmarks):
    """
    İki el kullanarak kalp hareketi yapılıp yapılmadığını kontrol eder.
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

# Görüntü işleme fonksiyonu
def process_frame():
    global camera, is_processing, current_gesture, current_confidence, heart_detected
    
    left_hand_landmarks = None
    right_hand_landmarks = None
    
    while is_camera_running:
        if camera is None or not camera.isOpened():
            time.sleep(0.1)
            continue
        
        ret, frame = camera.read()
        if not ret:
            time.sleep(0.1)
            continue
        
        # Görüntüyü çevir (ayna etkisi)
        if flip_image:
            frame = cv2.flip(frame, 1)
        
        # RGB formatına dönüştür (MediaPipe RGB bekler)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # İşlemeyi verimli hale getirmek için görüntüyü değişmez olarak işaretle
        rgb_frame.flags.writeable = False
        
        # El tespiti yap
        results = hands.process(rgb_frame)
        
        # Görüntüyü tekrar yazılabilir hale getir ve BGR'a çevir
        rgb_frame.flags.writeable = True
        
        # Arayüzü temizle
        overlay = frame.copy()
        # Yarı saydam arka plan oluştur - daha koyu ve belirgin yap
        cv2.rectangle(overlay, (0, 0), (frame_width, 120), bg_color, -1)
        alpha = 0.7  # Daha az saydam yap
        cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
        
        # Panel kenarlarını belirginleştir
        cv2.rectangle(frame, (0, 0), (frame_width, 120), panel_color, 2)
        
        # İki el arasında kalp tespiti için değişkenleri sıfırla
        left_hand_landmarks = None
        right_hand_landmarks = None
        heart_detected = False
        
        # Eğer el tespit edildiyse
        if results.multi_hand_landmarks:
            # Her el için
            multi_hand_landmarks = results.multi_hand_landmarks
            
            # Elleri belirleme (Sağ/Sol)
            if len(multi_hand_landmarks) == 2 and max_hands == 2:
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
                    
                    # Eylemi işle
                    gesture_actions.process_gesture("heart", current_confidence)
            
            # Her el için döngü
            for idx, hand_landmarks in enumerate(multi_hand_landmarks):
                # El iskeletini çiz
                if show_skeleton:
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
                        
                        # Eylemi işle
                        gesture_actions.process_gesture(gesture_name, confidence)
        else:
            # El tespit edilemedi mesajını kaldırıyoruz
            current_gesture = None
            current_confidence = 0
        
        # Mevcut hareketi büyük olarak göster (eğer varsa)
        if current_gesture:
            # Hareket adını Türkçe olarak al
            gesture_display_name = gesture_recognizer.GESTURES.get(current_gesture, "Bilinmeyen Hareket")
            
            # ASCII olmayan karakterleri temizle veya değiştir
            gesture_display_name = gesture_display_name.replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c").replace("ı", "i")
            
            # WebSocket ile hareketi gönder
            socketio.emit('gesture_detected', {
                'gesture': current_gesture,
                'gesture_name': gesture_display_name,
                'confidence': float(current_confidence)
            })
        
        # JPEG formatında kodla
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        frame_bytes = buffer.tobytes()
        
        # Kare gönder
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Flask rotaları
@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video akışı"""
    global is_processing, is_camera_running
    
    # Kamera açık değilse aç
    if not is_camera_running:
        if not start_camera():
            return "Kamera başlatılamadı!", 500
    
    is_processing = True
    
    # İlk kareyi daha hızlı göndermek için blank bir kare oluştur
    blank_frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', blank_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    blank_bytes = buffer.tobytes()
    
    # Hızlı bir ilk yanıt oluştur ve gerçek video akışını başlat
    def generate():
        # İlk kare olarak boş bir kare gönder (hızlı başlangıç için)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + blank_bytes + b'\r\n')
        
        # Gerçek video akışını başlat
        yield from process_frame()
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start_camera', methods=['POST'])
def api_start_camera():
    """Kamerayı başlat API"""
    global is_processing
    
    if not is_camera_running:
        if start_camera():
            is_processing = True
            # İşleme iş parçacığını başlat
            processing_thread = threading.Thread(target=lambda: None)
            processing_thread.daemon = True
            processing_thread.start()
            return jsonify({"success": True, "message": "Kamera başlatıldı"})
        else:
            return jsonify({"success": False, "message": "Kamera başlatılamadı!"}), 500
    
    return jsonify({"success": True, "message": "Kamera zaten çalışıyor"})

@app.route('/api/stop_camera', methods=['POST'])
def api_stop_camera():
    """Kamerayı durdur API"""
    global is_processing
    
    if is_camera_running:
        is_processing = False
        if stop_camera():
            return jsonify({"success": True, "message": "Kamera durduruldu"})
        else:
            return jsonify({"success": False, "message": "Kamera durdurulamadı!"}), 500
    
    return jsonify({"success": True, "message": "Kamera zaten durdurulmuş"})

@app.route('/api/toggle_hands_mode', methods=['POST'])
def api_toggle_hands_mode():
    """El izleme modunu değiştir API"""
    global max_hands, hands
    
    # Modu değiştir
    max_hands = 1 if max_hands == 2 else 2
    
    # Hands nesnesini yeniden oluştur
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=max_hands,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )
    
    return jsonify({
        "success": True, 
        "message": f"El izleme modu: {'Çift El' if max_hands == 2 else 'Tek El'}",
        "mode": "double" if max_hands == 2 else "single"
    })

@app.route('/api/toggle_skeleton', methods=['POST'])
def api_toggle_skeleton():
    """İskelet gösterimini aç/kapa API"""
    global show_skeleton
    
    show_skeleton = not show_skeleton
    
    return jsonify({
        "success": True, 
        "message": f"İskelet gösterimi: {'Açık' if show_skeleton else 'Kapalı'}",
        "skeleton": show_skeleton
    })

@app.route('/api/flip_camera', methods=['POST'])
def api_flip_camera():
    """Kamera görüntüsünü çevir API"""
    global flip_image
    
    flip_image = not flip_image
    
    return jsonify({
        "success": True, 
        "message": f"Kamera çevirme: {'Açık' if flip_image else 'Kapalı'}",
        "flipped": flip_image
    })

@socketio.on('connect')
def handle_connect():
    """WebSocket bağlantısı kurulduğunda"""
    print('WebSocket bağlantısı kuruldu')

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket bağlantısı kesildiğinde"""
    print('WebSocket bağlantısı kesildi')

# Ana fonksiyon
if __name__ == '__main__':
    # Argüman ayrıştırıcı
    parser = argparse.ArgumentParser(description='El Hareketi Tanıma Web Uygulaması')
    parser.add_argument('--port', type=int, default=5000, help='Web sunucu portu')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Web sunucu host adresi')
    parser.add_argument('--camera-id', type=int, default=0, help='Kamera ID')
    parser.add_argument('--debug', action='store_true', help='Debug modu')
    args = parser.parse_args()
    
    # Kamera ID'sini ayarla
    camera_id = args.camera_id
    
    # Şablonlar ve statik dosyalar için klasörler
    app_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(app_dir, '..', 'templates')
    static_dir = os.path.join(app_dir, '..', 'static')
    
    # Klasörler yoksa oluştur
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # Flask uygulama ayarları
    app.template_folder = templates_dir
    app.static_folder = static_dir
    
    print(f"Web uygulaması başlatılıyor... http://{args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug) 