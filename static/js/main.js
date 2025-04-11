// El Hareketi Tanıma Web Arayüzü - Neon Modern JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elemanları
    const videoStream = document.getElementById('videoStream');
    const streamStatus = document.getElementById('streamStatus');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const cameraOffInfo = document.getElementById('cameraOffInfo');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const flipBtn = document.getElementById('flipBtn');
    const skeletonBtn = document.getElementById('skeletonBtn');
    const handsModeBtn = document.getElementById('handsModeBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const skeletonSwitch = document.getElementById('skeletonSwitch');
    const flipSwitch = document.getElementById('flipSwitch');
    const singleHandMode = document.getElementById('singleHandMode');
    const doubleHandMode = document.getElementById('doubleHandMode');
    const currentGesture = document.getElementById('currentGesture');
    const confidenceBar = document.getElementById('confidenceBar');
    const confidenceText = document.getElementById('confidenceText');
    const gestureHistory = document.getElementById('gestureHistory');
    
    // Video overlay elemanları
    const videoOverlay = document.querySelector('.video-overlay');
    const currentModeDisplay = document.getElementById('currentModeDisplay');
    const skeletonModeDisplay = document.getElementById('skeletonModeDisplay');
    const liveGestureCard = document.getElementById('liveGestureCard');
    
    // Değişkenler
    let isStreamRunning = false;
    let streamUrl = '/video_feed';
    let showSkeleton = true;
    let isImageFlipped = true;
    let handsMode = 'double';
    let gestureList = [];
    let settingsModal;
    let currentDetectedGesture = null;
    let isHistoryUpdating = false; // Geçmiş güncellemesi yapılıp yapılmadığını kontrol etmek için
    
    // Modal nesnesi
    const initializeModal = () => {
        settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
    };
    
    // Socket.io bağlantısı
    const socket = io();
    
    // Başlatma
    const init = () => {
        console.log('El hareketi tanıma sistemi başlatılıyor...');
        
        // Başlangıç ayarlarını yapma
        loadingOverlay.style.display = 'none';
        videoOverlay.style.display = 'none'; // Başlangıçta video overlay'i gizle
        
        // Başlangıç durumunda tanınan hareket panelini ve canlı kartı "El Yok" olarak ayarla
        currentGesture.querySelector('.display-4').textContent = "El Yok";
        currentGesture.querySelector('.display-4').classList.add('no-hand');
        confidenceBar.style.width = '0%';
        confidenceText.textContent = 'Güven: %0';
        confidenceBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
        
        // Canlı hareket kartını başlangıçta "El Yok" olarak ayarla (kamera açıldığında gösterilecek)
        liveGestureCard.classList.add('no-hand');
        liveGestureCard.innerHTML = `
            <i class="fas fa-hand-paper"></i>
            <span>El Yok</span>
        `;
        
        // Video yüklendiğinde kamera kapalı bilgisini gizle
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'data-loaded' && videoStream.dataset.loaded === 'true') {
                    // Kamera açıksa kamera kapalı bilgisini gizle
                    if (isStreamRunning) {
                        cameraOffInfo.classList.add('hidden');
                        videoOverlay.style.display = 'flex';
                    }
                }
            });
        });
        
        // Video stream elementini gözlemle
        observer.observe(videoStream, { attributes: true });
        
        // Kamera kapalı bilgisini göster
        if (isStreamRunning) {
            cameraOffInfo.classList.add('hidden');
            videoOverlay.style.display = 'flex';
        } else {
            cameraOffInfo.classList.remove('hidden');
        }
        
        // UI animasyonlarını başlat
        animateUI();
        
        // Tarayıcı yenilendiğinde WebSocket bağlantısını yeniden kurma
        socket.on('connect', () => {
            console.log('WebSocket bağlantısı kuruldu');
            streamStatus.classList.add('pulse-once');
            
            // Animasyonu kaldır
            setTimeout(() => {
                streamStatus.classList.remove('pulse-once');
            }, 1000);
        });
        
        // Hareket algılandığında olayları işleme
        socket.on('gesture_detected', handleGestureDetected);
        
        // Olay dinleyicileri
        startBtn.addEventListener('click', startStream);
        stopBtn.addEventListener('click', stopStream);
        flipBtn.addEventListener('click', toggleFlip);
        skeletonBtn.addEventListener('click', toggleSkeleton);
        handsModeBtn.addEventListener('click', toggleHandsMode);
        settingsBtn.addEventListener('click', openSettings);
        saveSettingsBtn.addEventListener('click', saveSettings);
        
        // Canlı hareket kartı animasyon olayı
        liveGestureCard.addEventListener('animationend', () => {
            liveGestureCard.classList.remove('gesture-changed');
        });
        
        // Ayarlar modülünü başlat
        initializeModal();
        
        // UI Bilgilerini güncelle
        updateUIDisplays();
        
        // Yer tutucu resmi göster
        createPlaceholderImage();
        
        // Sayfa yüklendikten sonra kamera durumunu kontrol et
        setTimeout(() => {
            checkCameraStatus();
        }, 500);
    };
    
    // Kamera durumunu kontrol et
    const checkCameraStatus = () => {
        console.log("Kamera durumu kontrol ediliyor...", isStreamRunning);
        if (isStreamRunning) {
            // Kamera çalışıyorsa, kapalı bilgisi gizlenmeli
            cameraOffInfo.classList.add('hidden');
            videoOverlay.style.display = 'flex';
        } else {
            // Kamera çalışmıyorsa, kapalı bilgisi görünmeli
            cameraOffInfo.classList.remove('hidden');
            videoOverlay.style.display = 'none';
        }
    };
    
    // UI Bilgilerini Güncelle
    const updateUIDisplays = () => {
        // Mod bilgilerini güncelle
        currentModeDisplay.innerHTML = `<i class="fas fa-hands"></i> <span>${handsMode === 'double' ? 'Çift El Modu' : 'Tek El Modu'}</span>`;
        skeletonModeDisplay.innerHTML = `<i class="fas fa-skeleton"></i> <span>İskelet ${showSkeleton ? 'Açık' : 'Kapalı'}</span>`;
        
        // Buton aktifliği
        flipBtn.classList.toggle('active', isImageFlipped);
        skeletonBtn.classList.toggle('active', showSkeleton);
        handsModeBtn.classList.toggle('active', handsMode === 'double');
        
        // Buton metinleri
        flipBtn.innerHTML = `<i class="fas fa-sync"></i>${isImageFlipped ? 'Çevirili' : 'Normal'}`;
        skeletonBtn.innerHTML = `<i class="fas fa-skeleton"></i>${showSkeleton ? 'İskelet Açık' : 'İskelet Kapalı'}`;
        handsModeBtn.innerHTML = `<i class="fas fa-hands"></i>${handsMode === 'double' ? 'Çift El' : 'Tek El'}`;
    };
    
    // Canlı hareket kartını güncelle
    const updateLiveGestureCard = (gestureName, confidence) => {
        if (!gestureName || gestureName === '-') {
            // El olmadığında "El Yok" mesajı göster
            liveGestureCard.style.display = 'flex';
            liveGestureCard.classList.add('active');
            liveGestureCard.classList.add('no-hand'); // "El Yok" durumu için özel sınıf
            liveGestureCard.innerHTML = `
                <i class="fas fa-hand-paper"></i>
                <span>El Yok</span>
            `;
            return;
        }
        
        const confidencePercent = Math.round(confidence * 100);
        liveGestureCard.style.display = 'flex';
        
        // "El Yok" sınıfını kaldır
        liveGestureCard.classList.remove('no-hand');
        
        // Son hareketle aynı değilse, animasyon ekle
        if (currentDetectedGesture !== gestureName) {
            liveGestureCard.classList.add('gesture-changed');
            currentDetectedGesture = gestureName;
        }
        
        // Güven skoru yüksekse active sınıfını ekle
        liveGestureCard.classList.toggle('active', confidence >= 0.8);
        
        // Hareket simgesi belirleme
        let gestureIcon = 'fa-hand';
        
        if (gestureName.includes('Başparmak Yukarı')) {
            gestureIcon = 'fa-thumbs-up';
        } else if (gestureName.includes('Başparmak Aşağı')) {
            gestureIcon = 'fa-thumbs-down';
        } else if (gestureName.includes('Barış')) {
            gestureIcon = 'fa-hand-peace';
        } else if (gestureName.includes('Tamam')) {
            gestureIcon = 'fa-check-circle';
        } else if (gestureName.includes('Kalp')) {
            gestureIcon = 'fa-heart';
        } else if (gestureName.includes('Yumruk')) {
            gestureIcon = 'fa-fist-raised';
        } else if (gestureName.includes('Açık El')) {
            gestureIcon = 'fa-hand-paper';
        } else if (gestureName.includes('İşaret')) {
            gestureIcon = 'fa-hand-point-up';
        }
        
        // İçeriği güncelle
        liveGestureCard.innerHTML = `
            <i class="fas ${gestureIcon}"></i>
            <span>${gestureName}</span>
            <div class="confidence-badge">%${confidencePercent}</div>
        `;
    };
    
    // UI animasyonları
    const animateUI = () => {
        // Düğmelere hover efekti ekle
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(btn => {
            btn.addEventListener('mouseover', () => {
                btn.classList.add('btn-hover-effect');
            });
            
            btn.addEventListener('mouseout', () => {
                btn.classList.remove('btn-hover-effect');
            });
        });
    };
    
    // Yer tutucu resim oluştur
    const createPlaceholderImage = () => {
        cameraOffInfo.classList.remove('hidden'); // Kamera kapalı bilgisini göster
        
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');
        
        // Arka plan - açık tema
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#f5f5f9');
        gradient.addColorStop(1, '#eef0f5');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Dekoratif efektler
        for (let i = 0; i < 5; i++) {
            const x = Math.random() * canvas.width;
            const y = Math.random() * canvas.height;
            const radius = Math.random() * 100 + 50;
            
            const glowGradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
            glowGradient.addColorStop(0, 'rgba(66, 133, 244, 0.05)');
            glowGradient.addColorStop(1, 'rgba(66, 133, 244, 0)');
            
            ctx.fillStyle = glowGradient;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Ortadaki kamera simgesi arka planı
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.beginPath();
        ctx.arc(canvas.width/2, canvas.height/2 - 30, 60, 0, Math.PI * 2);
        ctx.fill();
        
        // Kamera simgesi çizdirme - kenarı
        ctx.strokeStyle = '#4285F4';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.rect(canvas.width/2 - 25, canvas.height/2 - 50, 50, 40);
        ctx.stroke();
        
        // Kamera lensi
        ctx.fillStyle = '#4285F4';
        ctx.beginPath();
        ctx.arc(canvas.width/2, canvas.height/2 - 30, 15, 0, Math.PI * 2);
        ctx.fill();
        
        // Kamera gövdesi
        ctx.fillStyle = '#4285F4';
        ctx.fillRect(canvas.width/2 - 25, canvas.height/2 - 10, 50, 5);
        
        // Kamera kapalı yazısı - arka plan
        const textBgWidth = 200;
        const textBgHeight = 40;
        const textBgX = canvas.width/2 - textBgWidth/2;
        const textBgY = canvas.height/2 + 40;
        
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.beginPath();
        ctx.roundRect(textBgX, textBgY, textBgWidth, textBgHeight, 10);
        ctx.fill();
        
        // Kamera kapalı yazısı
        ctx.fillStyle = '#202124';
        ctx.font = 'bold 18px Poppins, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Kamera Kapalı', canvas.width/2, canvas.height/2 + 65);
        
        // Bilgi yazısı - arka plan
        const infoBgWidth = 340;
        const infoBgHeight = 40;
        const infoBgX = canvas.width/2 - infoBgWidth/2;
        const infoBgY = canvas.height/2 + 100;
        
        ctx.fillStyle = 'rgba(66, 133, 244, 0.1)';
        ctx.beginPath();
        ctx.roundRect(infoBgX, infoBgY, infoBgWidth, infoBgHeight, 10);
        ctx.fill();
        
        // Bilgi yazısı
        ctx.fillStyle = '#4285F4';
        ctx.font = '16px Poppins, sans-serif';
        ctx.fillText('Başlatmak için "Başlat" butonuna tıklayın', canvas.width/2, canvas.height/2 + 125);
        
        // Canvas'ı resme dönüştürüp ayarla
        try {
            const dataUrl = canvas.toDataURL('image/jpeg');
            videoStream.src = dataUrl;
        } catch (e) {
            console.error('Yer tutucu resim oluşturulamadı:', e);
        }
        
        // Video overlay'i gizle
        videoOverlay.style.display = 'none';
    };
    
    // Akışı başlat
    const startStream = () => {
        if (isStreamRunning) return;
        
        // Yükleme durumunu güncelle
        streamStatus.className = 'badge bg-warning';
        streamStatus.textContent = 'Başlatılıyor...';
        
        // Yükleme katmanını göster
        loadingOverlay.style.display = 'flex';
        
        // Kamera kapalı bilgisini gizle - classList kullanarak geçiş efekti ekle
        cameraOffInfo.classList.add('hidden');
        
        fetch('/api/start_camera', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Video akışını başlat - hemen yükleme katmanını gizle
                loadingOverlay.style.display = 'none';
                
                // Rastgele bir parametre ekleyerek önbellek sorunlarını önle
                const timestamp = new Date().getTime();
                videoStream.src = `${streamUrl}?t=${timestamp}`;
                videoStream.dataset.loaded = 'false'; // Reset load status
                
                // Kamera açıldıktan sonra tekrarlı kontrol yaparak kesinlikle kamera kapalı bilgisini kaldırma
                const checkAndHideOffInfo = () => {
                    if (isStreamRunning) {
                        cameraOffInfo.classList.add('hidden');
                        videoOverlay.style.display = 'flex';
                    }
                };
                
                // Kamera açıldıktan sonra birkaç kez kontrol et
                setTimeout(checkAndHideOffInfo, 500);
                setTimeout(checkAndHideOffInfo, 1000);
                setTimeout(checkAndHideOffInfo, 1500);
                setTimeout(checkAndHideOffInfo, 2000);
                
                // Video yüklendiğinde overlay'i göster ve kamera kapalı bilgisini gizle
                videoStream.onload = function() {
                    console.log("Video stream yüklendi");
                    // Kamera kapalı bilgisini kesinlikle gizle
                    cameraOffInfo.classList.add('hidden');
                    // Video overlay'i göster
                    videoOverlay.style.display = 'flex';
                    // Yüklendiğini işaretle
                    this.dataset.loaded = 'true';
                };
                
                // Durum bilgilerini güncelle
                isStreamRunning = true;
                streamStatus.className = 'badge bg-success';
                streamStatus.textContent = 'Çalışıyor';
                startBtn.disabled = true;
                stopBtn.disabled = false;
                
                // Video overlay'i göster, kamera kapalı bilgisini kesinlikle gizle
                videoOverlay.style.display = 'flex';
                cameraOffInfo.classList.add('hidden');
                
                // Aktif butonları vurgula
                updateUIDisplays();
                
                // Başlatma animasyonu
                streamStatus.classList.add('pulse-once');
                setTimeout(() => {
                    streamStatus.classList.remove('pulse-once');
                }, 1000);
                
                // Hata durumunda
                videoStream.onerror = (e) => {
                    console.error('Video yükleme hatası:', e);
                    handleStreamError(e);
                };
                
                // Başarı bildirimi
                showToast('success', 'Kamera Başlatıldı', 'Görüntü işleme başlatıldı, el hareketlerinizi tanımaya hazırım!');
            } else {
                handleStreamError(data.message);
            }
        })
        .catch(handleStreamError);
        
        // Yükleme katmanını en fazla 2 saniye sonra kesinlikle kaldır
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
            // Eğer kamera başlatıldıysa tekrar kontrol et ve kamera kapalı bilgisini gizle
            if (isStreamRunning) {
                cameraOffInfo.classList.add('hidden');
            }
        }, 2000);
    };
    
    // Akışı durdur
    const stopStream = () => {
        if (!isStreamRunning) return;
        
        fetch('/api/stop_camera', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                isStreamRunning = false;
                streamStatus.className = 'badge bg-danger';
                streamStatus.textContent = 'Kapalı';
                startBtn.disabled = false;
                stopBtn.disabled = true;
                
                // Video overlay'i gizle
                videoOverlay.style.display = 'none';
                
                // Kamera kapalı bilgisini göster
                cameraOffInfo.classList.remove('hidden');
                
                // UI güncellemeleri
                updateUIDisplays();
                
                // Geçiş animasyonu ekle
                videoStream.classList.add('fade-transition');
                
                // Yer tutucu resmi göster
                setTimeout(() => {
                    createPlaceholderImage();
                    videoStream.classList.remove('fade-transition');
                }, 300);
                
                // Bildirim
                showToast('info', 'Kamera Durduruldu', 'El hareketi tanıma sistemi duraklatıldı.');
            } else {
                console.error('Kamera durdurulamadı:', data.message);
                showToast('error', 'Hata', 'Kamera durdurulamadı: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Kamera durdurma hatası:', error);
            showToast('error', 'Hata', 'Kamera durdurma işlemi başarısız oldu.');
        });
    };
    
    // Akış hatası işleme
    const handleStreamError = (error) => {
        console.error('Akış hatası:', error);
        isStreamRunning = false;
        streamStatus.className = 'badge bg-danger';
        streamStatus.textContent = 'Hata';
        startBtn.disabled = false;
        stopBtn.disabled = true;
        loadingOverlay.style.display = 'none';
        videoOverlay.style.display = 'none';
        cameraOffInfo.classList.remove('hidden'); // Kamera kapalı bilgisini göster
        createPlaceholderImage(); // Tekrar ekledik
        
        const errorMessage = typeof error === 'string' 
            ? error 
            : 'Kamera akışı başlatılamadı. Lütfen kamera erişim izinlerinizi kontrol edin.';
        
        showToast('error', 'Kamera Hatası', errorMessage);
    };
    
    // Hareket algılandığında olayları işleme
    const handleGestureDetected = (data) => {
        const gestureName = data.gesture_name;
        const confidence = data.confidence;
        
        // Eğer hareket yoksa
        if (!gestureName || gestureName === '-' || gestureName === 'unknown') {
            // Canlı hareket kartını güncelle
            updateLiveGestureCard(null, 0);
            
            // Tanınan hareket panelini güncelle
            currentGesture.querySelector('.display-4').textContent = "El Yok";
            currentGesture.querySelector('.display-4').classList.add('no-hand');
            confidenceBar.style.width = '0%';
            confidenceText.textContent = 'Güven: %0';
            confidenceBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
            
            // El Yok durumunu geçmişe ekle - sadece geçmişte el yoksa veya son kayıt el yoktan farklıysa
            if (gestureList.length === 0 || gestureList[0].gesture_name !== "El Yok") {
                addToHistory({
                    gesture_name: "El Yok",
                    confidence: 0,
                    time: new Date(),
                    is_no_hand: true // El Yok durumu özel bayrağı
                });
            }
            
            return;
        }
        
        // UI elemanlarını güncelle
        if (gestureName && confidence > 0.6) {
            currentGesture.querySelector('.display-4').textContent = gestureName;
            currentGesture.querySelector('.display-4').classList.add('gesture-changed');
            // "El yok" sınıfını kaldır
            currentGesture.querySelector('.display-4').classList.remove('no-hand');
            
            // Güven çubuğunu güncelle
            const confidencePercent = Math.round(confidence * 100);
            confidenceBar.style.width = `${confidencePercent}%`;
            confidenceText.textContent = `Güven: %${confidencePercent}`;
            
            // Güven seviyesine göre renk değiştir
            if (confidence >= 0.8) {
                confidenceBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
            } else if (confidence >= 0.6) {
                confidenceBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
            } else {
                confidenceBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
            }
            
            // Canlı hareket kartını güncelle
            updateLiveGestureCard(gestureName, confidence);
            
            // Geçmişe ekle (yeni hareket ise)
            addToHistory({
                gesture_name: gestureName, // Anahtar adını 'gesture_name' olarak değiştirdik
                confidence: confidence,
                time: new Date()
            });
        }
    };
    
    // Hareket geçmişine ekle
    const addToHistory = (gesture) => {
        // Güncelleme işaretini ayarla
        isHistoryUpdating = true;
        
        // Zaten listede aynı hareket varsa güncelle
        const existingIndex = gestureList.findIndex(item => item.gesture_name === gesture.gesture_name);
        
        if (existingIndex !== -1) {
            gestureList[existingIndex] = {
                ...gesture,
                time: new Date(),
                count: (gestureList[existingIndex].count || 1) + 1
            };
        } else {
            // Yeni hareket ekle
            gestureList.unshift({
                ...gesture,
                count: 1
            });
            
            // En fazla 8 hareket sakla (performans için azalttık)
            if (gestureList.length > 8) {
                gestureList.pop();
            }
        }
        
        // Geçmiş görünümünü güncelle
        updateHistoryDisplay();
        
        // 100ms sonra güncelleme işaretini kaldır (titreşimi önler)
        setTimeout(() => {
            isHistoryUpdating = false;
        }, 100);
    };
    
    // Geçmiş görüntüsünü güncelle
    const updateHistoryDisplay = () => {
        if (gestureList.length === 0) {
            gestureHistory.innerHTML = `
                <div class="list-group-item text-center py-4">
                    <i class="fas fa-hand fa-3x mb-3 text-secondary"></i>
                    <p class="mb-0 text-secondary">Henüz hareket tanınmadı</p>
                </div>
            `;
            return;
        }
        
        // Yeni HTML oluştur
        let newHistoryHTML = '';
        
        gestureList.forEach((item, index) => {
            // Undefined kontrolü yap
            const gestureName = item.gesture_name || "Bilinmeyen Hareket";
            const confidence = item.confidence || 0;
            
            const confidencePercent = Math.round(confidence * 100);
            const timeString = formatTime(item.time);
            const countBadge = item.count > 1 ? `<span class="badge bg-secondary ms-2">x${item.count}</span>` : '';
            
            // El Yok durumu için özel stil
            const isNoHand = item.is_no_hand === true;
            const itemClass = isNoHand ? 'gesture-item no-hand-item' : 'gesture-item';
            
            // Güven seviyesine göre renk sınıfı belirle
            let confidenceClass = isNoHand ? 'bg-danger' : 'bg-warning';
            if (!isNoHand) {
                if (confidence >= 0.8) {
                    confidenceClass = 'bg-success';
                } else if (confidence >= 0.6) {
                    confidenceClass = 'bg-info';
                }
            }
            
            // Titreşim sorununu çözmek için animation-delay kaldırıldı
            newHistoryHTML += `
                <div class="list-group-item ${itemClass} d-flex justify-content-between align-items-center">
                    <div>
                        <span class="gesture-name">${gestureName}</span>${countBadge}
                        <div class="gesture-time">${timeString}</div>
                    </div>
                    ${isNoHand ? 
                        `<span class="gesture-confidence ${confidenceClass}">-</span>` : 
                        `<span class="gesture-confidence ${confidenceClass}">%${confidencePercent}</span>`
                    }
                </div>
            `;
        });
        
        // İçeriği güncelle
        gestureHistory.innerHTML = newHistoryHTML;
    };
    
    // Zamanı formatla
    const formatTime = (date) => {
        return date.toLocaleTimeString('tr-TR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };
    
    // Görüntüyü çevirme
    const toggleFlip = () => {
        isImageFlipped = !isImageFlipped;
        
        fetch('/api/flip_camera', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            // UI güncellemeleri
            updateUIDisplays();
        })
        .catch(error => {
            console.error('Çevirme hatası:', error);
            showToast('error', 'Hata', 'Görüntü çevirme işlemi başarısız oldu.');
        });
    };
    
    // İskelet göstermeyi aç/kapa
    const toggleSkeleton = () => {
        showSkeleton = !showSkeleton;
        
        fetch('/api/toggle_skeleton', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            // UI güncellemeleri
            updateUIDisplays();
        })
        .catch(error => {
            console.error('İskelet değiştirme hatası:', error);
            showToast('error', 'Hata', 'İskelet gösterme ayarı değiştirilemedi.');
        });
    };
    
    // El izleme modu değiştirme
    const toggleHandsMode = () => {
        fetch('/api/toggle_hands_mode', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            handsMode = data.mode;
            
            // UI güncellemeleri
            updateUIDisplays();
            
            // Değişiklik animasyonu ekle
            handsModeBtn.classList.add('btn-pulse');
            setTimeout(() => {
                handsModeBtn.classList.remove('btn-pulse');
            }, 500);
        })
        .catch(error => {
            console.error('El modu değiştirme hatası:', error);
            showToast('error', 'Hata', 'El izleme modu değiştirilemedi.');
        });
    };
    
    // Ayarlar penceresini aç
    const openSettings = () => {
        // Geçerli ayarları arayüzde göster
        skeletonSwitch.checked = showSkeleton;
        flipSwitch.checked = isImageFlipped;
        singleHandMode.checked = handsMode === 'single';
        doubleHandMode.checked = handsMode === 'double';
        
        settingsModal.show();
    };
    
    // Ayarları kaydet
    const saveSettings = () => {
        // İskelet gösterme ayarı değiştiyse
        if (skeletonSwitch.checked !== showSkeleton) {
            toggleSkeleton();
        }
        
        // Görüntü çevirme ayarı değiştiyse
        if (flipSwitch.checked !== isImageFlipped) {
            toggleFlip();
        }
        
        // El modu ayarı değiştiyse
        const newHandsMode = singleHandMode.checked ? 'single' : 'double';
        if (newHandsMode !== handsMode) {
            toggleHandsMode();
        }
        
        settingsModal.hide();
        
        // Ayarlar kaydedildi bildirimi
        showToast('success', 'Ayarlar', 'Ayarlarınız başarıyla kaydedildi.');
    };
    
    // Toast bildirimi göster
    const showToast = (type, title, message) => {
        // Varsa önceki bildirimi kaldır
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Yeni bildirim oluştur
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        
        // İçerik
        toast.innerHTML = `
            <div class="toast-header">
                <span>${title}</span>
                <button type="button" class="btn-close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Kapatma düğmesi olayını ekle
        toast.querySelector('.btn-close').addEventListener('click', () => {
            toast.classList.add('toast-hiding');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
        
        // Sayfaya ekle
        document.body.appendChild(toast);
        
        // Görünür yap
        setTimeout(() => {
            toast.classList.add('toast-showing');
        }, 10);
        
        // Otomatik kapat
        setTimeout(() => {
            toast.classList.add('toast-hiding');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 5000);
    };
    
    // Başlat
    init();
}); 