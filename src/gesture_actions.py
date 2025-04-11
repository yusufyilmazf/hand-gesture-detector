#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import subprocess
import platform
import cv2
import numpy as np

class GestureActions:
    """
    Tanınan el hareketlerine göre eylemler gerçekleştiren sınıf.
    """
    
    def __init__(self):
        """
        GestureActions sınıfını başlatır.
        """
        # Son gerçekleştirilen eylem ve zaman damgası
        self.last_action = None
        self.last_action_time = 0
        
        # Aynı hareketin tekrar tetiklenmesi için gereken minimum süre (saniye)
        self.action_cooldown = 2.0
        
        # Eylem tanımları (hareket_adı -> fonksiyon eşleştirmesi)
        self.actions = {
            "thumbs_up": self.action_thumbs_up,
            "thumbs_down": self.action_thumbs_down,
            "peace": self.action_peace,
            "ok": self.action_ok,
            "fist": self.action_fist,
            "open_hand": self.action_open_hand,
            "pointing": self.action_pointing,
            "heart": self.action_heart,
            "rock": self.action_rock,
            "pinch": self.action_pinch,
            "gun": self.action_gun,
            "count_one": self.action_count_one,
            "count_two": self.action_count_two,
            "phone": self.action_phone
        }
        
        # Eylem açıklamaları - Türkçe karakter sorunları için özel karakterleri değiştir
        self.action_descriptions = {
            "thumbs_up": "Begenme islemi yapildi 👍",
            "thumbs_down": "Begenmeme islemi yapildi 👎",
            "peace": "Baris mesaji gonderildi ✌️",
            "ok": "Onay islemi yapildi 👌",
            "fist": "Durduruldu ✊",
            "open_hand": "Merhaba! 🖐️",
            "pointing": "Isaret ediliyor 👆",
            "heart": "Kalp gonderildi ❤️",
            "rock": "Rock isareti 🤘",
            "pinch": "Hassas tutma/secme islemi 👌",
            "gun": "Silah isareti 👉",
            "count_one": "Bir 1️⃣",
            "count_two": "Iki 2️⃣",
            "phone": "Telefon acildi ☎️"
        }
        
        # Eylem geçmişi
        self.action_history = []
        self.max_history = 10
        
        # Arka plan iş parçacığı için bayrak
        self.running = True
        
        # Ses dosyaları için yollar
        self.sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sounds")
        os.makedirs(self.sounds_dir, exist_ok=True)
        
        # Ses çalma komutu (platform bağımlı)
        if platform.system() == "Windows":
            self.play_sound_cmd = "start"  # Windows için
        elif platform.system() == "Darwin":
            self.play_sound_cmd = "afplay"  # macOS için
        else:
            # Linux için
            if self._command_exists("paplay"):
                self.play_sound_cmd = "paplay"
            elif self._command_exists("aplay"):
                self.play_sound_cmd = "aplay"
            else:
                self.play_sound_cmd = None
                print("Uyari: Desteklenen ses calma komutu bulunamadi! Ses calma devre disi.")
    
    def _command_exists(self, cmd):
        """
        Verilen komutun sistemde var olup olmadığını kontrol eder.
        """
        return subprocess.call("type " + cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
    
    def process_gesture(self, gesture_name, confidence):
        """
        Tanınan hareketi işler ve uygun eylemi gerçekleştirir.
        
        Args:
            gesture_name: Tanınan hareketin adı
            confidence: Tanıma güveni
            
        Returns:
            action_performed: Eylem gerçekleştirildi mi?
            action_description: Gerçekleştirilen eylemin açıklaması
        """
        # Eğer hareket tanınmadıysa veya güven düşükse
        if gesture_name == "unknown" or confidence < 0.6:
            return False, ""
        
        # Eğer hareket için bir eylem tanımlanmışsa
        if gesture_name in self.actions:
            current_time = time.time()
            
            # Aynı hareket için soğuma süresi kontrolü
            if self.last_action == gesture_name and current_time - self.last_action_time < self.action_cooldown:
                return False, ""
            
            # Eylemi çağır
            action_thread = threading.Thread(
                target=self.actions[gesture_name], 
                args=(confidence,)
            )
            action_thread.daemon = True
            action_thread.start()
            
            # Son eylemi güncelle
            self.last_action = gesture_name
            self.last_action_time = current_time
            
            # Eylem geçmişine ekle
            self.action_history.append((gesture_name, self.action_descriptions.get(gesture_name, ""), current_time))
            if len(self.action_history) > self.max_history:
                self.action_history.pop(0)
            
            return True, self.action_descriptions.get(gesture_name, "Eylem gerceklestirildi")
        
        return False, ""
    
    def get_action_history(self):
        """
        Eylem geçmişini döndürür.
        
        Returns:
            action_history: Eylem geçmişi listesi
        """
        return self.action_history
    
    def action_thumbs_up(self, confidence):
        """
        Başparmak yukarı eylemini gerçekleştirir.
        """
        print(f"👍 Begenme islemi yapildi (Guven: {confidence:.2f})")
        self._play_sound("thumbs_up.wav")
    
    def action_thumbs_down(self, confidence):
        """
        Başparmak aşağı eylemini gerçekleştirir.
        """
        print(f"👎 Begenmeme islemi yapildi (Guven: {confidence:.2f})")
        self._play_sound("thumbs_down.wav")
    
    def action_peace(self, confidence):
        """
        Barış işareti eylemini gerçekleştirir.
        """
        print(f"✌️ Baris mesaji gonderildi (Guven: {confidence:.2f})")
        self._play_sound("peace.wav")
    
    def action_ok(self, confidence):
        """
        Tamam işareti eylemini gerçekleştirir.
        """
        print(f"👌 Onay islemi yapildi (Guven: {confidence:.2f})")
        self._play_sound("ok.wav")
    
    def action_fist(self, confidence):
        """
        Yumruk eylemini gerçekleştirir.
        """
        print(f"✊ Durduruldu (Guven: {confidence:.2f})")
        self._play_sound("fist.wav")
    
    def action_open_hand(self, confidence):
        """
        Açık el eylemini gerçekleştirir.
        """
        print(f"🖐️ Merhaba! (Guven: {confidence:.2f})")
        self._play_sound("open_hand.wav")
    
    def action_pointing(self, confidence):
        """
        İşaret eylemini gerçekleştirir.
        """
        print(f"👆 Isaret ediliyor (Guven: {confidence:.2f})")
        self._play_sound("pointing.wav")
    
    def action_heart(self, confidence):
        """
        Kalp işareti eylemini gerçekleştirir.
        """
        print(f"❤️ Kalp gonderildi (Guven: {confidence:.2f})")
        self._play_sound("heart.wav")
    
    def action_rock(self, confidence):
        """
        Rock işareti eylemini gerçekleştirir.
        """
        print(f"🤘 Rock isareti (Guven: {confidence:.2f})")
        self._play_sound("rock.wav")
    
    def action_pinch(self, confidence):
        """
        Tutma hareketi eylemini gerçekleştirir.
        """
        print(f"👌 Tutma hareketi (Guven: {confidence:.2f})")
        self._play_sound("pinch.wav")
    
    def action_gun(self, confidence):
        """
        Silah işareti eylemini gerçekleştirir.
        """
        print(f"👉 Silah isareti (Guven: {confidence:.2f})")
        self._play_sound("gun.wav")
    
    def action_count_one(self, confidence):
        """
        Bir sayısı eylemini gerçekleştirir.
        """
        print(f"Bir 1️⃣ (Guven: {confidence:.2f})")
        self._play_sound("count_one.wav")
    
    def action_count_two(self, confidence):
        """
        İki sayısı eylemini gerçekleştirir.
        """
        print(f"Iki 2️⃣ (Guven: {confidence:.2f})")
        self._play_sound("count_two.wav")
    
    def action_phone(self, confidence):
        """
        Telefon açma eylemini gerçekleştirir.
        """
        print(f"Telefon acildi ☎️ (Guven: {confidence:.2f})")
        self._play_sound("phone.wav")
    
    def _play_sound(self, sound_file):
        """
        Belirtilen ses dosyasını çalar.
        
        Args:
            sound_file: Çalınacak ses dosyasının adı
        """
        if self.play_sound_cmd is None:
            return
        
        sound_path = os.path.join(self.sounds_dir, sound_file)
        
        # Ses dosyası yoksa sessizce başarısız ol
        if not os.path.exists(sound_path):
            print(f"Uyari: Ses dosyasi bulunamadi: {sound_path}")
            return
        
        try:
            if platform.system() == "Windows":
                # Windows
                subprocess.Popen(
                    [self.play_sound_cmd, sound_path], 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
            else:
                # macOS veya Linux
                subprocess.Popen(
                    [self.play_sound_cmd, sound_path], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
        except Exception as e:
            print(f"Ses calma hatasi: {e}")
    
    def visualize_actions(self, frame, show_history=True):
        """
        Gerçekleştirilen eylemleri görselleştirir.
        
        Args:
            frame: Görselleştirmenin yapılacağı kare
            show_history: Eylem geçmişi gösterilsin mi?
            
        Returns:
            frame: Görselleştirme eklenmiş kare
        """
        # Bu uygulamada artık görsel olarak eylem geçmişi göstermiyoruz
        # Çünkü kullanıcı arayüzünü sadeleştirdik
        return frame
    
    def cleanup(self):
        """
        Kaynakları temizler.
        """
        self.running = False 