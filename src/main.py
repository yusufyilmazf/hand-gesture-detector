import os
import argparse
import pickle
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model

# Kendi modüllerimizi içe aktarın
from data_processor import prepare_data_for_training
from model import create_model, train_model, evaluate_model, plot_training_history, load_trained_model
from predictor import ASLPredictor, start_webcam_prediction, predict_from_image

def train(args):
    """
    Modeli eğiten fonksiyon.
    
    Args:
        args: Komut satırı argümanları
    """
    print(f"Veri seti yükleniyor: {args.data_dir}")
    
    # Veriyi hazırla
    X_train, X_test, y_train, y_test, label_encoder, num_classes = prepare_data_for_training(
        args.data_dir,
        image_size=(args.image_size, args.image_size),
        test_size=args.test_size,
        apply_augmentation=args.augment
    )
    
    # Model giriş şeklini belirle
    if args.grayscale:
        input_shape = (args.image_size, args.image_size, 1)
    else:
        input_shape = (args.image_size, args.image_size, 3)
    
    # Modeli oluştur
    print("Model oluşturuluyor...")
    model = create_model(input_shape, num_classes)
    model.summary()
    
    # Modeli eğit
    print("Model eğitiliyor...")
    history, trained_model = train_model(
        model,
        X_train, y_train,
        X_test, y_test,
        batch_size=args.batch_size,
        epochs=args.epochs,
        model_save_path=args.model_path
    )
    
    # Eğitim geçmişini çizdir
    plot_training_history(history)
    
    # Modeli değerlendir
    print("Model değerlendiriliyor...")
    evaluate_model(trained_model, X_test, y_test)
    
    # Etiket kodlayıcıyı kaydet
    label_encoder_path = os.path.join(os.path.dirname(args.model_path), 'label_encoder.pkl')
    with open(label_encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    
    print(f"Model kaydedildi: {args.model_path}")
    print(f"Etiket kodlayıcı kaydedildi: {label_encoder_path}")

def predict(args):
    """
    Tahmin yapan fonksiyon.
    
    Args:
        args: Komut satırı argümanları
    """
    # Etiket kodlayıcıyı yükle
    label_encoder_path = os.path.join(os.path.dirname(args.model_path), 'label_encoder.pkl')
    
    # Eğer etiket kodlayıcı bulunamazsa, varsayılan olarak yeni oluştur
    try:
        with open(label_encoder_path, 'rb') as f:
            label_encoder = pickle.load(f)
        print(f"Etiket kodlayıcı yüklendi: {label_encoder_path}")
    except FileNotFoundError:
        print(f"Uyarı: Etiket kodlayıcı bulunamadı: {label_encoder_path}")
        if args.force_create_encoder:
            print("Elle etiket kodlayıcı oluşturuluyor...")
            from sklearn.preprocessing import LabelEncoder
            
            # ASL için etiketler (A-Z, 0-9)
            labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
                     'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 
                     'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 
                     'u', 'v', 'w', 'x', 'y', 'z']
            
            # Etiket kodlayıcıyı oluştur
            label_encoder = LabelEncoder()
            label_encoder.fit(labels)
            
            # Etiket kodlayıcıyı kaydet
            os.makedirs(os.path.dirname(label_encoder_path), exist_ok=True)
            with open(label_encoder_path, 'wb') as f:
                pickle.dump(label_encoder, f)
            
            print(f"Etiket kodlayıcı oluşturuldu ve kaydedildi: {label_encoder_path}")
        else:
            print("Etiket kodlayıcı olmadan devam edilemiyor. --force-create-encoder parametresi ile yeni bir etiket kodlayıcı oluşturabilirsiniz.")
            return
    
    # Tahmin ediciyi oluştur - artık image_size parametresi model tarafından otomatik belirlenir
    predictor = ASLPredictor(
        args.model_path,
        label_encoder,
        use_grayscale=args.grayscale
    )
    
    if args.image_path:
        # Tek görüntüden tahmin yap
        predict_from_image(predictor, args.image_path)
    else:
        # Webcam'den tahmin yap
        start_webcam_prediction(predictor, camera_id=args.camera_id)

def main():
    """
    Ana fonksiyon.
    """
    parser = argparse.ArgumentParser(description='İşaret Dili Tanıma Uygulaması')
    
    subparsers = parser.add_subparsers(dest='command', help='Komut')
    
    # Eğitim komutu
    train_parser = subparsers.add_parser('train', help='Modeli eğit')
    train_parser.add_argument('--data-dir', type=str, 
                             default='../datasets/asl',
                             help='Veri seti dizini')
    train_parser.add_argument('--model-path', type=str, 
                             default='../models/asl_model.h5',
                             help='Model kaydetme yolu')
    train_parser.add_argument('--image-size', type=int, default=64,
                             help='Görüntü boyutu')
    train_parser.add_argument('--batch-size', type=int, default=32,
                             help='Batch boyutu')
    train_parser.add_argument('--epochs', type=int, default=30,
                             help='Eğitim dönem sayısı')
    train_parser.add_argument('--test-size', type=float, default=0.2,
                             help='Test seti oranı')
    train_parser.add_argument('--augment', action='store_true',
                             help='Veri çoğaltma uygula')
    train_parser.add_argument('--grayscale', action='store_true',
                             help='Görüntüleri gri tonlama olarak işle')
    
    # Tahmin komutu
    predict_parser = subparsers.add_parser('predict', help='Tahmin yap')
    predict_parser.add_argument('--model-path', type=str, 
                               default='../models/asl_model.h5',
                               help='Model yolu')
    predict_parser.add_argument('--image-path', type=str,
                               help='Tahmin edilecek görüntü yolu (belirtilmezse webcam kullanılır)')
    predict_parser.add_argument('--camera-id', type=int, default=0,
                               help='Kamera ID')
    predict_parser.add_argument('--grayscale', action='store_true',
                               help='Görüntüleri gri tonlama olarak işle (eski modeller için)')
    predict_parser.add_argument('--force-create-encoder', action='store_true',
                               help='Etiket kodlayıcı bulunamazsa yeni bir tane oluştur')
    
    args = parser.parse_args()
    
    if args.command == 'train':
        train(args)
    elif args.command == 'predict':
        predict(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 