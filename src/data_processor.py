import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

def load_data(data_dir, image_size=(64, 64)):
    """
    Veri setindeki görüntüleri ve etiketleri yükler.
    
    Args:
        data_dir: Veri setinin yolu
        image_size: Görüntü boyutu (varsayılan: 64x64)
        
    Returns:
        images: Yüklenen görüntüler
        labels: Görüntülerin etiketleri
    """
    images = []
    labels = []
    
    # Veri seti klasöründeki tüm alt klasörleri dolaşın
    for label in sorted(os.listdir(data_dir)):
        label_dir = os.path.join(data_dir, label)
        
        # Sadece dizin olanları işleyin
        if os.path.isdir(label_dir):
            # Bu etiket için tüm görüntüleri yükleyin
            for image_file in os.listdir(label_dir):
                if image_file.endswith('.jpeg') or image_file.endswith('.jpg'):
                    image_path = os.path.join(label_dir, image_file)
                    
                    # Görüntüyü okuyun ve yeniden boyutlandırın
                    image = cv2.imread(image_path)
                    if image is None:
                        continue
                    
                    image = cv2.resize(image, image_size)
                    
                    # Görüntüyü ve etiketi listelere ekleyin
                    images.append(image)
                    labels.append(label)
    
    return np.array(images), np.array(labels)

def preprocess_data(images, labels, test_size=0.2, random_state=42):
    """
    Veri setini ön işlemden geçirir ve eğitim/test setlerine ayırır.
    
    Args:
        images: Görüntü dizisi
        labels: Etiket dizisi
        test_size: Test seti oranı
        random_state: Rastgele durum (tekrarlanabilirlik için)
        
    Returns:
        X_train, X_test: Eğitim ve test görüntüleri
        y_train, y_test: Eğitim ve test etiketleri
        label_encoder: Etiket kodlayıcı
    """
    # Görüntüleri normalize edin (0-1 aralığına)
    X = images.astype('float32') / 255.0
    
    # Etiketleri kodlayın
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)
    
    # Eğitim ve test setlerine ayırın
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    
    return X_train, X_test, y_train, y_test, label_encoder

def augment_data(images, labels):
    """
    Veri çoğaltma işlemi yapar.
    
    Args:
        images: Görüntü dizisi
        labels: Etiket dizisi
        
    Returns:
        augmented_images: Çoğaltılmış görüntüler
        augmented_labels: Çoğaltılmış etiketler
    """
    augmented_images = []
    augmented_labels = []
    
    for image, label in zip(images, labels):
        # Orijinal görüntüyü ve etiketi ekleyin
        augmented_images.append(image)
        augmented_labels.append(label)
        
        # Görüntüyü çevirin (yatay)
        flipped_h = cv2.flip(image, 1)
        augmented_images.append(flipped_h)
        augmented_labels.append(label)
        
        # Görüntüyü döndürün
        rows, cols = image.shape[:2]
        rotation_matrix = cv2.getRotationMatrix2D((cols/2, rows/2), 15, 1)
        rotated = cv2.warpAffine(image, rotation_matrix, (cols, rows))
        augmented_images.append(rotated)
        augmented_labels.append(label)
        
        # Görüntüye gürültü ekleyin
        noisy = image.copy()
        noise = np.random.normal(0, 0.05, image.shape)
        noisy = noisy + noise
        noisy = np.clip(noisy, 0, 1)
        augmented_images.append(noisy)
        augmented_labels.append(label)
    
    return np.array(augmented_images), np.array(augmented_labels)

def prepare_data_for_training(data_dir, image_size=(64, 64), test_size=0.2, apply_augmentation=True):
    """
    Eğitim için veriyi hazırlar.
    
    Args:
        data_dir: Veri setinin yolu
        image_size: Görüntü boyutu
        test_size: Test seti oranı
        apply_augmentation: Veri çoğaltma uygulansın mı?
        
    Returns:
        X_train, X_test: Eğitim ve test görüntüleri
        y_train, y_test: Eğitim ve test etiketleri
        label_encoder: Etiket kodlayıcı
        num_classes: Sınıf sayısı
    """
    # Veriyi yükle
    images, labels = load_data(data_dir, image_size)
    
    # Veriyi ön işlemden geçir
    X_train, X_test, y_train, y_test, label_encoder = preprocess_data(images, labels, test_size)
    
    # Veri çoğaltma uygula
    if apply_augmentation:
        X_train, y_train = augment_data(X_train, y_train)
    
    # Sınıf sayısını bul
    num_classes = len(label_encoder.classes_)
    
    print(f"Toplam {len(images)} görüntü yüklendi.")
    print(f"Eğitim seti: {X_train.shape[0]} örnek")
    print(f"Test seti: {X_test.shape[0]} örnek")
    print(f"Sınıf sayısı: {num_classes}")
    
    return X_train, X_test, y_train, y_test, label_encoder, num_classes 