# İşaret Dili Tanıma Uygulaması - Kullanım Kılavuzu

Bu dokümanda, İşaret Dili Tanıma Uygulamasının nasıl kullanılacağı adım adım açıklanmaktadır.

## İçerik

1. [Kurulum](#kurulum)
2. [Model Eğitimi](#model-eğitimi)
3. [Tahmin Yapma](#tahmin-yapma)
4. [Test Betiği](#test-betiği)
5. [Parametreler](#parametreler)

## Kurulum

Uygulamayı kullanmadan önce gerekli kütüphaneleri yüklemeniz gerekmektedir:

```bash
pip install -r requirements.txt
```

## Model Eğitimi

Model eğitimi için aşağıdaki komutu kullanabilirsiniz:

```bash
python src/main.py train --data-dir ../backend/datasets/asl
```

Varsayılan olarak, model `models/asl_model.h5` dosyasına kaydedilecektir.

Ek parametreler:

- `--image-size`: Görüntü boyutu (varsayılan: 64)
- `--batch-size`: Batch boyutu (varsayılan: 32)
- `--epochs`: Eğitim dönem sayısı (varsayılan: 30)
- `--test-size`: Test seti oranı (varsayılan: 0.2)
- `--augment`: Veri çoğaltma uygula (flag)

Örnek:

```bash
python src/main.py train --data-dir ../datasets/asl --image-size 128 --batch-size 64 --epochs 50 --augment
```

## Tahmin Yapma

### Webcam ile Tahmin

Webcam ile gerçek zamanlı tahmin yapmak için:

```bash
python src/main.py predict
```

### Dosyadan Tahmin

Belirli bir görüntü dosyasından tahmin yapmak için:

```bash
python src/main.py predict --image-path <görüntü_yolu>
```

Örnek:

```bash
python src/main.py predict --image-path ../datasets/asl/a/a_1_rotate_1.jpeg
```

## Test Betiği

Uygulamayı hızlı bir şekilde test etmek için `test.py` betiğini kullanabilirsiniz:

```bash
python test.py
```

Bu betik, eğer model yoksa eğitim yapar ve ardından webcam üzerinden tahmin yapmaya başlar.

Ek parametreler:

- `--test-image`: Test edilecek görüntü yolu
- `--data-dir`: Veri seti dizini (varsayılan: ../datasets/asl)
- `--quick-train`: Hızlı eğitim modu (daha az epoch)

Örnek:

```bash
python test.py --quick-train
python test.py --test-image ../datasets/asl/b/b_1_rotate_1.jpeg
```

## Parametreler

### Eğitim Parametreleri

- `--data-dir`: Veri seti dizini
- `--model-path`: Model kaydetme yolu
- `--image-size`: Görüntü boyutu
- `--batch-size`: Batch boyutu
- `--epochs`: Eğitim dönem sayısı
- `--test-size`: Test seti oranı
- `--augment`: Veri çoğaltma uygula

### Tahmin Parametreleri

- `--model-path`: Model yolu
- `--image-path`: Tahmin edilecek görüntü yolu
- `--image-size`: Görüntü boyutu
- `--camera-id`: Kamera ID (varsayılan: 0)

## Kullanım İpuçları

1. Daha iyi sonuçlar için, el işaretinizi ekrandaki yeşil kare içinde tutun.
2. Belirli bir işareti algılamada sorun yaşıyorsanız, farklı açılardan ve mesafelerden deneyin.
3. İyi bir aydınlatma, tanıma doğruluğunu önemli ölçüde artırır.
4. Model eğitimini `--augment` parametresiyle çalıştırmak, daha iyi sonuçlar verebilir.
5. Daha yüksek bir görüntü boyutu (`--image-size`), daha doğru sonuçlar verebilir, ancak eğitim süresini artırır. 