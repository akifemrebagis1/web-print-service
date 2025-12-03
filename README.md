# 🖨️ Web Print Service - Ağ Yazdırma Servisi v2.0

**Ağ desteği olmayan yazıcılarınızı ağ yazıcısına dönüştürün!**

Bu uygulama, USB ile bilgisayara bağlı olan ve ağ desteği bulunmayan yazıcıları, web arayüzü üzerinden ağdaki tüm cihazlardan (telefon, tablet, diğer bilgisayarlar) kullanılabilir hale getirir.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## 🎯 Ne İşe Yarar?

Birçok yazıcı (özellikle bütçe dostu modeller) ağ bağlantısı özelliğine sahip değildir. Bu yazıcılar sadece USB ile bağlı oldukları bilgisayardan yazdırabilir. **Web Print Service** bu sorunu çözer:

```
📱 Telefon/Tablet  ──┐
💻 Dizüstü         ──┼── WiFi ──▶ 🖥️ Sunucu Bilgisayar ──▶ USB ──▶ 🖨️ Yazıcı
🖥️ Diğer PC       ──┘
```

### Kullanım Senaryoları

- 📱 **Telefondan yazdırma**: Fotoğraflarınızı veya belgelerinizi doğrudan telefonunuzdan yazdırın
- 💼 **Ofis kullanımı**: Tek bir yazıcıyı birden fazla bilgisayardan kullanın
- 🏠 **Ev kullanımı**: Ailenizle yazıcıyı paylaşın
- 🖼️ **Fotoğraf baskısı**: Layout seçenekleriyle tek sayfaya birden fazla fotoğraf sığdırın

## ✨ Özellikler

- 🌐 **Ağ Üzerinden Yazdırma**: Aynı ağdaki tüm cihazlardan erişim
- 📄 **Tek Dosya Yazdırma**: PDF ve resim dosyalarını kolayca yazdırın
- 📚 **Çoklu Dosya Desteği**: Birden fazla dosyayı toplu olarak işleyin
- 🔗 **Dosya Birleştirme**: Birden fazla resmi tek bir PDF'te birleştirin
- 🎨 **Layout Seçenekleri**: 1, 2, 4, 6 veya 9 kopya tek sayfada
- 📱 **Responsive Tasarım**: Mobil cihazlardan da kullanılabilir
- 🖥️ **Cross-Platform**: Windows, Linux ve macOS desteği
- ⚡ **Hızlı İşlem**: Optimize edilmiş resim ve PDF işleme
- 🔄 **Tüm Yazıcılarla Uyumlu**: Sistem varsayılan yazıcısını kullanır

## 📋 Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- USB bağlantılı herhangi bir yazıcı

### İşletim Sistemi Desteği

| İşletim Sistemi | Durum | Not |
|-----------------|-------|-----|
| Windows 10/11 | ✅ Tam Destek | pywin32 gerekli |
| Linux | ✅ Tam Destek | CUPS gerekli |
| macOS | ✅ Tam Destek | CUPS (varsayılan) |

## 🚀 Kurulum

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/YOUR_USERNAME/web-print-service.git
cd web-print-service
```

### 2. Sanal Ortam Oluşturun (Önerilen)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Uygulamayı Başlatın

```bash
python app.py
```

Uygulama varsayılan olarak `http://localhost:5000` adresinde çalışacaktır.

## 📖 Kullanım

### Web Arayüzü

1. Tarayıcınızda `http://localhost:5000` adresine gidin
2. **Tek Dosya** veya **Çoklu Dosya** sekmesini seçin
3. Dosyanızı sürükle-bırak ile veya tıklayarak yükleyin
4. Layout seçeneğini belirleyin (1, 2, 4, 6 veya 9)
5. "Yazdırmayı Başlat" butonuna tıklayın

### 📱 Diğer Cihazlardan Erişim

Aynı WiFi ağındaki telefonunuzdan, tabletinizden veya başka bir bilgisayardan:

1. Uygulama başlatıldığında konsolda gösterilen IP adresini not edin:
   ```
   🌐 Ağ erişimi: http://192.168.1.100:5000
   ```
2. Diğer cihazınızın tarayıcısında bu adresi açın
3. Dosyalarınızı yükleyin ve yazdırın!

## ⏰ Windows Başlangıçta Otomatik Çalıştırma

Windows Görev Zamanlayıcısı kullanarak bilgisayar her açıldığında uygulamayı otomatik başlatabilirsiniz:

### Yöntem 1: Batch Dosyası ile (Önerilen)

1. Proje klasöründeki `start_print_service.bat` dosyasını kullanın
2. Windows Görev Zamanlayıcısı'nı açın (`taskschd.msc`)
3. "Temel Görev Oluştur" seçin
4. Ad: "Web Print Service"
5. Tetikleyici: "Bilgisayar başladığında"
6. Eylem: "Program başlat"
7. Program: `start_print_service.bat` dosyasının tam yolu
8. "Başlangıç konumu" alanına proje klasörünün yolunu girin

### Yöntem 2: PowerShell ile Tek Komutla

```powershell
# Görev oluşturma (Yönetici olarak çalıştırın)
$action = New-ScheduledTaskAction -Execute "pythonw.exe" -Argument "app.py" -WorkingDirectory "C:\path\to\web-print-service"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Limited
Register-ScheduledTask -TaskName "WebPrintService" -Action $action -Trigger $trigger -Principal $principal
```

### Yöntem 3: Başlangıç Klasörü

1. `Win + R` tuşlarına basın, `shell:startup` yazın
2. `start_print_service.bat` dosyasının kısayolunu bu klasöre kopyalayın

## 🔧 Yapılandırma

### Environment Variables (Ortam Değişkenleri)

`.env` dosyası oluşturarak özelleştirebilirsiniz:

```env
# Flask ayarları
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here

# Sunucu ayarları
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Dosya ayarları
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=104857600

# Tarayıcı ayarları
AUTO_OPEN_BROWSER=False
```

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `FLASK_ENV` | development | Ortam türü (development/production) |
| `FLASK_DEBUG` | False | Debug modu |
| `SECRET_KEY` | Rastgele | Flask secret key |
| `FLASK_HOST` | 0.0.0.0 | Sunucu host (0.0.0.0 = tüm ağ) |
| `FLASK_PORT` | 5000 | Sunucu port |
| `MAX_CONTENT_LENGTH` | 104857600 | Maksimum dosya boyutu (100MB) |
| `AUTO_OPEN_BROWSER` | False | Tarayıcıyı otomatik aç |

## 📁 Proje Yapısı

```
web-print-service/
├── app.py                    # Ana Flask uygulaması
├── config.py                 # Konfigürasyon ayarları
├── layout_handler.py         # PDF ve resim layout işlemleri
├── requirements.txt          # Python bağımlılıkları
├── start_print_service.bat   # Windows başlatma scripti
├── .env.example              # Örnek environment değişkenleri
├── .gitignore                # Git ignore dosyası
├── README.md                 # Bu dosya
├── LICENSE                   # MIT Lisansı
├── templates/
│   └── index.html            # Web arayüzü
└── uploads/                  # Yüklenen dosyalar (git'e dahil değil)
```

## 🔌 API Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/` | GET | Ana sayfa (web arayüzü) |
| `/upload` | POST | Tek dosya yükleme ve yazdırma |
| `/upload-multiple` | POST | Çoklu dosya yükleme ve yazdırma |
| `/status` | GET | Sistem ve yazıcı durumu |
| `/debug-printer` | GET | Yazıcı debug bilgileri |
| `/cleanup-all` | GET | Geçici dosyaları temizle |

## 📄 Desteklenen Dosya Formatları

- **PDF**: .pdf
- **Resimler**: .jpg, .jpeg, .png, .bmp, .gif, .tiff

## 🖨️ Yazıcı Uyumluluğu

Bu uygulama **tüm yazıcılarla** çalışır. Sistem varsayılan yazıcınızı otomatik olarak algılar ve kullanır.

### Test Edilen Yazıcılar

- Canon PIXMA serisi
- HP DeskJet/LaserJet serisi
- Epson EcoTank serisi
- Brother serisi
- Samsung Xpress serisi
- Ve diğer tüm Windows/Linux/macOS uyumlu yazıcılar

### Yazıcı Ayarları

Varsayılan yazıcınızı değiştirmek için:
- **Windows**: Ayarlar → Yazıcılar ve tarayıcılar → Varsayılan olarak ayarla
- **Linux**: `lpoptions -d printer_name`
- **macOS**: Sistem Tercihleri → Yazıcılar ve Tarayıcılar

## 🐛 Sorun Giderme

### Yazıcı bulunamıyor
1. Yazıcının açık ve bilgisayara bağlı olduğundan emin olun
2. Yazıcı sürücüsünün yüklü olduğunu kontrol edin
3. `/debug-printer` endpoint'ini ziyaret edin
4. Windows'ta pywin32'nin doğru kurulduğundan emin olun:
   ```bash
   pip install --upgrade pywin32
   ```

### Ağdan erişilemiyor
1. Windows Güvenlik Duvarı'nda 5000 portuna izin verin
2. Cihazların aynı WiFi ağında olduğundan emin olun
3. IP adresini doğru yazdığınızdan emin olun

### Port kullanımda hatası
Farklı bir port kullanın:
```bash
set FLASK_PORT=5001
python app.py
```

### Dosya yükleme hatası
- Dosya boyutunun 100MB'ı geçmediğinden emin olun
- Desteklenen formatlardan biri olduğunu kontrol edin

## 🔒 Güvenlik Notları

- Bu uygulama yerel ağ kullanımı için tasarlanmıştır
- İnternete açmayın, sadece güvendiğiniz yerel ağda kullanın
- Üretim ortamında `SECRET_KEY` environment variable'ını ayarlayın

## 🤝 Katkıda Bulunma

1. Bu projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🙏 Teşekkürler

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Pillow](https://pillow.readthedocs.io/) - Resim işleme
- [ReportLab](https://www.reportlab.com/) - PDF oluşturma
- [pywin32](https://github.com/mhammond/pywin32) - Windows API

---

**⭐ Bu proje işinize yaradıysa yıldız vermeyi unutmayın!**
