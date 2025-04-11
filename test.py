import os
import sys
import argparse

def main():
    """
    Test betiği ana fonksiyonu.
    """
    parser = argparse.ArgumentParser(description='İşaret Dili Tanıma Uygulaması Test Betiği')
    parser.add_argument('--test-image', type=str, help='Test edilecek görüntü yolu')
    parser.add_argument('--data-dir', type=str, default='../datasets/asl',
                       help='Veri seti dizini')
    parser.add_argument('--quick-train', action='store_true',
                       help='Hızlı eğitim modu (daha az epoch)')
    
    args = parser.parse_args()
    
    # Çalışma dizinini src/ olarak ayarla
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    
    if not os.path.exists(src_dir):
        print(f"Hata: src dizini bulunamadı: {src_dir}")
        return
    
    # Daha önce eğitilmiş bir model var mı kontrol et
    model_path = os.path.join(script_dir, 'models', 'asl_model.h5')
    model_exists = os.path.exists(model_path)
    
    if not model_exists or args.quick_train:
        # Modeli eğit
        print("Model eğitiliyor...")
        
        train_cmd = [
            "python", os.path.join(src_dir, "main.py"), "train",
            "--data-dir", args.data_dir,
            "--model-path", model_path
        ]
        
        if args.quick_train:
            train_cmd.extend(["--epochs", "5", "--batch-size", "64"])
        
        # Komutu çalıştır
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        os.system(" ".join(train_cmd))
    
    # Tahmin yap
    if args.test_image:
        # Belirli bir görüntü üzerinde tahmin yap
        print(f"Görüntü üzerinde tahmin yapılıyor: {args.test_image}")
        predict_cmd = [
            "python", os.path.join(src_dir, "main.py"), "predict",
            "--model-path", model_path,
            "--image-path", args.test_image
        ]
        os.system(" ".join(predict_cmd))
    else:
        # Webcam üzerinde tahmin yap
        print("Webcam üzerinde tahmin yapılıyor...")
        predict_cmd = [
            "python", os.path.join(src_dir, "main.py"), "predict",
            "--model-path", model_path
        ]
        os.system(" ".join(predict_cmd))

if __name__ == "__main__":
    main() 