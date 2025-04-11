import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt

def create_model(input_shape, num_classes):
    """
    CNN modeli oluşturur.
    
    Args:
        input_shape: Giriş görüntüsünün boyutu (yükseklik, genişlik, kanal)
        num_classes: Sınıf sayısı
        
    Returns:
        model: Oluşturulan CNN modeli
    """
    model = Sequential()
    
    # İlk evrişim bloğu
    model.add(Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=input_shape))
    model.add(BatchNormalization())
    model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.25))
    
    # İkinci evrişim bloğu
    model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.25))
    
    # Üçüncü evrişim bloğu
    model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
    model.add(BatchNormalization())
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.25))
    
    # Düzleştirme ve tam bağlantı katmanları
    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))
    
    # Modeli derle
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_model(model, X_train, y_train, X_test, y_test, batch_size=32, epochs=30, model_save_path='models/asl_model.h5'):
    """
    Modeli eğitir.
    
    Args:
        model: Eğitilecek model
        X_train, y_train: Eğitim verileri
        X_test, y_test: Test verileri
        batch_size: Batch boyutu
        epochs: Eğitim dönem sayısı
        model_save_path: Modelin kaydedileceği yol
        
    Returns:
        history: Eğitim geçmişi
        model: Eğitilmiş model
    """
    # Etiketleri one-hot kodlamasına dönüştürün
    y_train_categorical = to_categorical(y_train)
    y_test_categorical = to_categorical(y_test)
    
    # Model kontrol noktası
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    checkpoint = ModelCheckpoint(
        model_save_path,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
    
    # Erken durdurma
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    )
    
    # Öğrenme oranı azaltma
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=5,
        min_lr=1e-6,
        verbose=1
    )
    
    # Modeli eğitin
    history = model.fit(
        X_train, y_train_categorical,
        batch_size=batch_size,
        epochs=epochs,
        validation_data=(X_test, y_test_categorical),
        callbacks=[checkpoint, early_stopping, reduce_lr]
    )
    
    return history, model

def evaluate_model(model, X_test, y_test):
    """
    Modeli değerlendirir.
    
    Args:
        model: Değerlendirilecek model
        X_test, y_test: Test verileri
        
    Returns:
        test_loss: Test kaybı
        test_acc: Test doğruluğu
    """
    y_test_categorical = to_categorical(y_test)
    test_loss, test_acc = model.evaluate(X_test, y_test_categorical, verbose=1)
    print(f"Test doğruluğu: {test_acc:.4f}")
    print(f"Test kaybı: {test_loss:.4f}")
    
    return test_loss, test_acc

def plot_training_history(history, save_path='models/training_history.png'):
    """
    Eğitim geçmişini görselleştirir.
    
    Args:
        history: Eğitim geçmişi
        save_path: Grafiğin kaydedileceği yol
    """
    # Eğitim ve doğrulama doğruluğu
    plt.figure(figsize=(12, 4))
    
    # Doğruluk grafiği
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Eğitim Doğruluğu')
    plt.plot(history.history['val_accuracy'], label='Doğrulama Doğruluğu')
    plt.title('Model Doğruluğu')
    plt.ylabel('Doğruluk')
    plt.xlabel('Dönem')
    plt.legend()
    
    # Kayıp grafiği
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Eğitim Kaybı')
    plt.plot(history.history['val_loss'], label='Doğrulama Kaybı')
    plt.title('Model Kaybı')
    plt.ylabel('Kayıp')
    plt.xlabel('Dönem')
    plt.legend()
    
    plt.tight_layout()
    
    # Grafiği kaydet
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()

def load_trained_model(model_path):
    """
    Eğitilmiş modeli yükler.
    
    Args:
        model_path: Model dosya yolu
        
    Returns:
        model: Yüklenen model
    """
    model = load_model(model_path)
    print(f"Model '{model_path}' dosyasından yüklendi.")
    return model 