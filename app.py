"""
Web Print Service - Ağ Üzerinden Yazdırma Servisi v2.0

Bu uygulama, ağ desteği olmayan yazıcılara ağ üzerinden yazdırma imkanı sağlar.
Herhangi bir USB yazıcıyı web arayüzü üzerinden ağdaki tüm cihazlardan kullanılabilir hale getirir.
PDF ve resim dosyalarını çeşitli layout seçenekleriyle yazdırma imkanı sunar.

Özellikler:
    - Ağ desteği olmayan yazıcıları ağ yazıcısına dönüştürme
    - Tek ve çoklu dosya yazdırma
    - Layout seçenekleri (1, 2, 4, 6, 9 kopya)
    - Dosya birleştirme
    - Otomatik yazıcı algılama (sistem varsayılan yazıcısı)
    - Cross-platform destek (Windows, Linux, macOS)
    - Mobil cihazlardan yazdırma desteği

Kullanım:
    python app.py

Gereksinimler:
    - Python 3.8+
    - Flask
    - Pillow
    - reportlab
    - pywin32 (Windows için)
"""

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, send_from_directory, session
import os
import secrets
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from layout_handler import create_layout_pdf, create_multi_file_pdf
from config import get_config
import platform
import subprocess
import tempfile
import socket
import time
from pathlib import Path
import json
import webbrowser
import logging

# Konfigürasyonu yükle
config = get_config()

# Logging ayarları
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask uygulamasını oluştur
app = Flask(__name__)

# Konfigürasyon ayarlarını uygula
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['TEMPLATES_FOLDER'] = config.TEMPLATES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.secret_key = config.SECRET_KEY

# Oturum çerezi güvenlik bayrakları.
# SameSite=Strict, çerezin siteler arası isteklerde gönderilmesini engeller;
# bu da cookie tabanlı CSRF'in büyük kısmını kapatır.
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Kimlik doğrulaması gerektirmeyen yollar (giriş ekranı ve statik dosyalar)
_PUBLIC_PATHS = {'/login'}


def _token_is_valid(candidate):
    """Erişim token'ını sabit zamanlı karşılaştırır."""
    if not candidate:
        return False
    return secrets.compare_digest(str(candidate), config.ACCESS_TOKEN)


def _request_origin_is_same_site():
    """Durum değiştiren istekler için Origin/Referer kontrolü.

    SameSite=Strict çerezine ek bir savunma katmanı. Origin başlığı yoksa
    Referer'a bakılır; ikisi de yoksa istek reddedilir.
    """
    origin = request.headers.get('Origin') or request.headers.get('Referer')
    if not origin:
        return False
    try:
        return urlparse(origin).netloc == request.host
    except ValueError:
        return False


@app.before_request
def require_authentication():
    """Tüm endpoint'leri token tabanlı kimlik doğrulamasının arkasına alır.

    Servis varsayılan olarak 0.0.0.0 üzerinden tüm yerel ağı dinlediği için
    kimlik doğrulaması olmadan dosya yükleme, yazdırma ve silme uçları
    ağdaki herkese açık kalıyordu.
    """
    path = request.path

    # Statik dosyalar ve giriş ekranı serbest
    if path in _PUBLIC_PATHS or path.startswith('/static/'):
        return None

    # Zaten doğrulanmış oturum
    if session.get('authenticated'):
        # Durum değiştiren isteklerde CSRF kontrolü
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if not _request_origin_is_same_site():
                return jsonify({
                    'success': False,
                    'message': 'İstek reddedildi: geçersiz kaynak (CSRF koruması).'
                }), 403
        return None

    # Token ile ilk doğrulama: ?token=... veya X-Auth-Token başlığı
    supplied = request.args.get('token') or request.headers.get('X-Auth-Token')
    if _token_is_valid(supplied):
        session['authenticated'] = True
        session.permanent = False
        # Token'ı URL'de bırakmamak için temiz adrese yönlendir
        if request.method == 'GET' and request.args.get('token'):
            return redirect(request.path)
        return None

    # Doğrulanmamış istek
    if request.method == 'GET' and request.accept_mimetypes.accept_html:
        return redirect(url_for('login'))
    return jsonify({
        'success': False,
        'message': 'Yetkisiz istek. Geçerli bir erişim token\'ı gerekli.'
    }), 401


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Basit token giriş ekranı."""
    error = ''
    if request.method == 'POST':
        if _token_is_valid(request.form.get('token')):
            session['authenticated'] = True
            return redirect(url_for('index'))
        error = 'Geçersiz token.'

    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yazdırma Servisi — Giriş</title>
<style>
 body{{font-family:system-ui,sans-serif;display:flex;align-items:center;
 justify-content:center;height:100vh;margin:0;background:#f4f4f5}}
 form{{background:#fff;padding:32px;border-radius:12px;
 box-shadow:0 1px 3px rgba(0,0,0,.1);min-width:280px}}
 h1{{font-size:18px;margin:0 0 16px}}
 input{{width:100%;padding:10px;border:1px solid #d4d4d8;border-radius:6px;
 box-sizing:border-box;font-size:15px}}
 button{{width:100%;margin-top:12px;padding:10px;border:0;border-radius:6px;
 background:#18181b;color:#fff;font-size:15px;cursor:pointer}}
 .err{{color:#b91c1c;font-size:13px;margin-top:10px}}
</style></head><body>
<form method="post">
  <h1>🖨️ Yazdırma Servisi</h1>
  <input type="password" name="token" placeholder="Erişim token'ı"
         autocomplete="current-password" autofocus>
  <button type="submit">Giriş</button>
  {'<div class="err">' + error + '</div>' if error else ''}
</form></body></html>"""

# İzin verilen dosya uzantıları
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

# Klasörleri oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMPLATES_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Dosya uzantısını al"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def get_local_ip():
    """Yerel IP adresini al"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def test_file_access(file_path):
    """Dosya erişim kontrolü"""
    try:
        if not os.path.exists(file_path):
            return False, f"Dosya bulunamadı: {file_path}"
        if not os.access(file_path, os.R_OK):
            return False, f"Dosya okunamıyor: {file_path}"
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, f"Dosya boş: {file_path}"
        return True, f"Dosya erişilebilir ({file_size} bytes)"
    except Exception as e:
        return False, f"Dosya kontrol hatası: {e}"


def debug_printer_info():
    """Yazıcı bilgilerini detaylı şekilde göster"""
    try:
        if platform.system() == "Windows":
            import win32print
            print("\n" + "="*50)
            print("YAZICI DETAYLI BİLGİLER")
            print("="*50)
            # Tüm yazıcıları listele
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            print(f"Toplam yazıcı sayısı: {len(printers)}")
            for i, printer in enumerate(printers):
                print(f"\n{i+1}. Yazıcı: {printer[2]}")
                try:
                    # Yazıcı durumunu detaylı kontrol et
                    printer_handle = win32print.OpenPrinter(printer[2])
                    printer_info = win32print.GetPrinter(printer_handle, 2)
                    win32print.ClosePrinter(printer_handle)
                    print(f"   Durum: {printer_info['Status']}")
                    print(f"   Port: {printer_info['pPortName']}")
                    print(f"   Sürücü: {printer_info['pDriverName']}")
                    print(f"   Konum: {printer_info['pLocation']}")
                except Exception as e:
                    print(f"   Hata: {e}")
            # Varsayılan yazıcı
            try:
                default_printer = win32print.GetDefaultPrinter()
                print(f"\n🖨️ Varsayılan yazıcı: {default_printer}")
                # Varsayılan yazıcının durumunu kontrol et
                printer_handle = win32print.OpenPrinter(default_printer)
                printer_info = win32print.GetPrinter(printer_handle, 2)
                win32print.ClosePrinter(printer_handle)
                print(f"   Durum Kodu: {printer_info['Status']}")
                if printer_info['Status'] == 0:
                    print("   ✅ Yazıcı hazır")
                else:
                    print(
                        f"   ❌ Yazıcı problemi (Kod: {printer_info['Status']})")
            except Exception as e:
                print(f"❌ Varsayılan yazıcı hatası: {e}")
            print("="*50)
        elif platform.system() == "Linux":
            print("\n" + "="*50)
            print("LINUX YAZICI BİLGİLERİ")
            print("="*50)
            try:
                result = subprocess.run(
                    ['lpstat', '-p'], capture_output=True, text=True)
                print(result.stdout)
                result = subprocess.run(
                    ['lpstat', '-d'], capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                print(f"Linux yazıcı bilgisi hatası: {e}")
        else:
            print(f"Bu işletim sistemi desteklenmiyor: {platform.system()}")
    except ImportError:
        print("❌ win32print modülü bulunamadı!")
        print("Çözüm: pip install pywin32")
    except Exception as e:
        print(f"❌ Yazıcı bilgi hatası: {e}")


def print_pdf_with_multiple_methods(file_path, printer_name):
    """PDF dosyası için çoklu yazdırma yöntemi"""
    print(f"🔄 PDF yazdırma yöntemleri deneniyor: {file_path}")
    # Yöntem 1: Adobe Acrobat Reader
    try:
        print("   Adobe Reader deneniyor...")
        result = subprocess.run([
            'AcroRd32.exe', '/p', '/h', file_path
        ], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            time.sleep(3)  # Yazdırma işleminin başlaması için bekle
            return True, "Adobe Reader ile yazdırıldı"
    except FileNotFoundError:
        print("   Adobe Reader bulunamadı")
    except Exception as e:
        print(f"   Adobe Reader hatası: {e}")
    # Yöntem 2: Microsoft Edge (Windows 10/11)
    try:
        print("   Microsoft Edge deneniyor...")
        result = subprocess.run([
            'msedge.exe', '--headless', '--print-to-pdf', '--run-all-compositor-stages-before-draw', file_path
        ], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return True, "Microsoft Edge ile yazdırıldı"
    except FileNotFoundError:
        print("   Edge bulunamadı")
    except Exception as e:
        print(f"   Edge hatası: {e}")
    # Yöntem 3: SumatraPDF (eğer yüklüyse)
    try:
        print("   SumatraPDF deneniyor...")
        result = subprocess.run([
            'SumatraPDF.exe', '-print-to-default', file_path
        ], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return True, "SumatraPDF ile yazdırıldı"
    except FileNotFoundError:
        print("   SumatraPDF bulunamadı")
    except Exception as e:
        print(f"   SumatraPDF hatası: {e}")
    # Yöntem 4: PowerShell ile yazdırma
    try:
        print("   PowerShell deneniyor...")
        ps_command = f'Start-Process -FilePath "{file_path}" -Verb Print -WindowStyle Hidden'
        result = subprocess.run([
            'powershell', '-Command', ps_command
        ], capture_output=True, text=True, timeout=20)
        if result.returncode == 0:
            time.sleep(3)
            return True, "PowerShell ile yazdırıldı"
        else:
            print(f"   PowerShell stderr: {result.stderr}")
    except Exception as e:
        print(f"   PowerShell hatası: {e}")
    return False, "PDF yazdırma başarısız - tüm yöntemler denendi"


def print_image_with_multiple_methods(file_path, printer_name):
    """Resim dosyası için çoklu yazdırma yöntemi"""
    print(f"🔄 Resim yazdırma yöntemleri deneniyor: {file_path}")
    # Yöntem 1: Windows Photo Viewer
    try:
        print("   Windows Photo Viewer deneniyor...")
        result = subprocess.run([
            'rundll32.exe', 'shimgvw.dll,ImageView_PrintTo',
            file_path, printer_name
        ], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            time.sleep(2)
            return True, "Windows Photo Viewer ile yazdırıldı"
    except Exception as e:
        print(f"   Photo Viewer hatası: {e}")

    # Yöntem 2: PIL ile doğrudan yazdırma
    try:
        print("   PIL ile doğrudan yazdırma deneniyor...")
        from PIL import Image, ImageWin
        import win32print
        import win32ui
        # Resmi aç
        image = Image.open(file_path)
        # Yazıcı DC'sini oluştur
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        # Yazdırma başlat
        hdc.StartDoc(os.path.basename(file_path))
        hdc.StartPage()
        # Resmi çiz
        dib = ImageWin.Dib(image)
        x, y = image.size
        dib.draw(hdc.GetHandleOutput(), (0, 0, x, y))
        # Yazdırma bitir
        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
        return True, "PIL ile doğrudan yazdırıldı"
    except ImportError:
        print("   PIL modülü bulunamadı")
    except Exception as e:
        print(f"   PIL hatası: {e}")

    # Yöntem 3: Ghostscript ile PDF'e dönüştürüp yazdırma
    try:
        print("   Ghostscript yöntemi deneniyor...")
        # Önce görüntüyü PDF'e dönüştür
        temp_pdf = tempfile.mktemp(suffix='.pdf')
        from PIL import Image
        img = Image.open(file_path)
        img_rgb = img.convert('RGB')
        img_rgb.save(temp_pdf, 'PDF', resolution=100.0)

        # Şimdi PDF'i yazdır
        import win32api
        result = win32api.ShellExecute(
            0, "print", temp_pdf, f'/d:"{printer_name}"', ".", 0
        )
        time.sleep(3)
        # Geçici dosyayı temizle
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)

        if result > 32:
            return True, "Ghostscript yöntemi ile yazdırıldı"
    except Exception as e:
        print(f"   Ghostscript hatası: {e}")

    # Yöntem 4: Command line printing
    try:
        print("   Command line yazdırma deneniyor...")
        if platform.system() == "Windows":
            # Windows için lpr kullan
            # GÜVENLİK: shell=True kaldırıldı. Windows'ta shell=True + liste
            # argümanı, listeyi cmd.exe komut satırına birleştirir ve
            # file_path içindeki kabuk metakarakterleri yorumlanır.
            result = subprocess.run([
                'print', '/d:' + printer_name, file_path
            ], capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                return True, "Command line ile yazdırıldı"
        else:
            # Linux/Mac için lpr kullan
            result = subprocess.run([
                'lpr', '-P', printer_name, file_path
            ], capture_output=True, text=True)
            if result.returncode == 0:
                return True, "lpr ile yazdırıldı"
    except Exception as e:
        print(f"   Command line hatası: {e}")

    return False, "Resim yazdırma başarısız - tüm otomatik yöntemler denendi"


def advanced_print_pdf(output_pdf):
    """Gelişmiş yazdırma fonksiyonu - tüm sorunları çözer"""
    system = platform.system()
    file_ext = Path(output_pdf).suffix.lower()
    print(f"\n🖨️ Gelişmiş yazdırma başlatılıyor...")
    print(f"📄 Dosya: {output_pdf}")
    print(f"📋 Tip: {file_ext}")
    print(f"💻 Sistem: {system}")
    # Dosya erişim kontrolü
    accessible, msg = test_file_access(output_pdf)
    if not accessible:
        return False, msg
    print(f"✅ {msg}")
    if system == "Windows":
        try:
            import win32print
            import win32api
            # Varsayılan yazıcı
            default_printer = win32print.GetDefaultPrinter()
            print(f"🖨️ Hedef yazıcı: {default_printer}")
            # Yazıcı durum kontrolü
            try:
                handle = win32print.OpenPrinter(default_printer)
                printer_info = win32print.GetPrinter(handle, 2)
                win32print.ClosePrinter(handle)
                status = printer_info['Status']
                print(f"📊 Yazıcı durumu: {status}")
                if status != 0:
                    print("⚠️ Yazıcı uyarısı - devam ediliyor...")
            except Exception as e:
                print(f"⚠️ Yazıcı durum kontrolü başarısız: {e}")

            # İlk yöntem: ShellExecute
            print("🔄 ShellExecute deneniyor...")
            try:
                result = win32api.ShellExecute(
                    0,
                    "print",
                    output_pdf,
                    f'/d:"{default_printer}"',
                    ".",
                    0
                )
                if result > 32:
                    print("✅ ShellExecute başarılı!")
                    time.sleep(3)  # Yazdırma işleminin başlaması için bekle
                    return True, f"ShellExecute ile yazdırıldı: {default_printer}"
                else:
                    print(f"❌ ShellExecute hatası: {result}")
            except Exception as e:
                print(f"❌ ShellExecute exception: {e}")

            # Dosya tipine göre özelleştirilmiş yöntemler
            if file_ext == '.pdf':
                success, message = print_pdf_with_multiple_methods(
                    output_pdf, default_printer)
                if success:
                    return True, message
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
                success, message = print_image_with_multiple_methods(
                    output_pdf, default_printer)
                if success:
                    return True, message

            # Windows için ek otomatik yazdırma yöntemi
            try:
                print("🔄 PrintFile API deneniyor...")
                import tempfile
                import ctypes
                from ctypes import windll

                # Windows GDI print spooler API
                PRINTER_DEFAULTS = ctypes.Structure()
                PRINTER_DEFAULTS.DesiredAccess = 0x00000008  # PRINTER_ACCESS_USE

                printer_handle = ctypes.c_ulong()
                if windll.winspool.OpenPrinterA(default_printer, ctypes.byref(printer_handle), ctypes.byref(PRINTER_DEFAULTS)):
                    try:
                        # Doküman başlat
                        doc_info = (default_printer, output_pdf, None)
                        job_id = windll.winspool.StartDocPrinterA(
                            printer_handle, 1, doc_info)
                        if job_id > 0:
                            # Dokümanı yazdır
                            with open(output_pdf, 'rb') as f:
                                data = f.read()
                                bytes_written = ctypes.c_ulong()
                                windll.winspool.StartPagePrinter(
                                    printer_handle)
                                windll.winspool.WritePrinter(
                                    printer_handle, data, len(data), ctypes.byref(bytes_written))
                                windll.winspool.EndPagePrinter(printer_handle)
                                windll.winspool.EndDocPrinter(printer_handle)
                                return True, "Windows GDI PrintFile API ile yazdırıldı"
                    finally:
                        windll.winspool.ClosePrinter(printer_handle)
            except Exception as e:
                print(f"❌ PrintFile API hatası: {e}")

            # Tüm yöntemler başarısız oldu
            return False, "Otomatik yazdırma başarısız - tüm yöntemler denendi"

        except ImportError:
            return False, "❌ win32print modülü bulunamadı. 'pip install pywin32' çalıştırın"
        except Exception as e:
            print(f"❌ Genel Windows hatası: {e}")
            return False, f"Tüm otomatik yazdırma yöntemleri başarısız: {e}"

    elif system == "Linux":
        try:
            # Linux'ta CUPS ile yazdırma
            result = subprocess.run(
                ['lp', output_pdf], capture_output=True, text=True)
            if result.returncode == 0:
                return True, "✅ Linux yazdırma başarılı"
            else:
                # Alternatif yöntem
                result = subprocess.run(
                    ['lpr', output_pdf], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, "✅ Linux lpr yazdırma başarılı"
                else:
                    return False, f"❌ Linux yazdırma hatası: {result.stderr}"
        except Exception as e:
            return False, f"❌ Linux yazdırma hatası: {e}"

    elif system == "Darwin":  # macOS
        try:
            # macOS'ta CUPS ile yazdırma
            result = subprocess.run(
                ['lpr', output_pdf], capture_output=True, text=True)
            if result.returncode == 0:
                return True, "✅ macOS yazdırma başarılı"
            else:
                # Alternatif yöntem
                # GÜVENLİK / DOĞRULUK: shell=True kaldırıldı. Önceki hâlde '|'
                # bir kabuk borusu değil, cupsfilter'a giden düz bir argümandı.
                # Boru artık Python tarafında, kabuk devreye girmeden kuruluyor.
                cups = subprocess.Popen(
                    ['cupsfilter', output_pdf], stdout=subprocess.PIPE)
                lpr = subprocess.Popen(
                    ['lpr'], stdin=cups.stdout,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if cups.stdout:
                    cups.stdout.close()
                lpr.communicate()
                result = subprocess.CompletedProcess(
                    args=['cupsfilter', output_pdf, 'lpr'],
                    returncode=lpr.returncode, stdout='', stderr='')
                if result.returncode == 0:
                    return True, "✅ macOS cupsfilter yazdırma başarılı"
                else:
                    return False, f"❌ macOS yazdırma hatası: {result.stderr}"
        except Exception as e:
            return False, f"❌ macOS yazdırma hatası: {e}"

    else:
        return False, f"❌ Desteklenmeyen işletim sistemi: {system}"


def cleanup_files(file_list, print_success=True):
    """Dosya temizleme fonksiyonu"""
    if not file_list:
        return
    print(f"\n🧹 Dosya temizliği başlatılıyor... ({len(file_list)} dosya)")
    for file_path in file_list:
        if file_path and os.path.exists(file_path):
            try:
                # Yazdırma başarılıysa biraz bekle
                if print_success:
                    time.sleep(1)
                os.remove(file_path)
                print(f"✅ Silindi: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"⚠️ Silinemedi {os.path.basename(file_path)}: {e}")


@app.route('/')
def index():
    """Ana sayfa - HTML şablonunu göster"""
    local_ip = get_local_ip()
    # HTML dosyasını yükle
    with open(os.path.join(app.config['TEMPLATES_FOLDER'], 'index.html'), 'r', encoding='utf-8') as f:
        html_content = f.read()
    # Değişkenleri yerleştir
    html_content = html_content.replace('{{local_ip}}', local_ip)
    html_content = html_content.replace('{{system}}', platform.system())
    return html_content


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Statik dosyaları sunma"""
    return send_from_directory('static', filename)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Tek dosya yükleme"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    file = request.files['file']
    layout = request.form.get('layout', '1')
    print_direct = request.form.get('print_direct', 'true').lower() == 'true'

    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Desteklenmeyen dosya türü'})
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"\n📁 Dosya kaydedildi: {filepath}")
        print(f"📄 Dosya tipi: {get_file_extension(filename)}")
        print(f"📊 Dosya boyutu: {os.path.getsize(filepath)} bytes")
        # Dosya erişim kontrolü
        accessible, access_msg = test_file_access(filepath)
        if not accessible:
            return jsonify({'success': False, 'message': f'Dosya erişim hatası: {access_msg}'})
        # Layout PDF oluştur
        try:
            output_pdf = create_layout_pdf(filepath, layout)
            print(f"📄 Layout PDF oluşturuldu: {output_pdf}")
            # Oluşturulan PDF'in erişim kontrolü
            pdf_accessible, pdf_msg = test_file_access(output_pdf)
            if not pdf_accessible:
                return jsonify({'success': False, 'message': f'PDF oluşturma hatası: {pdf_msg}'})
        except Exception as layout_error:
            print(f"❌ Layout PDF oluşturma hatası: {layout_error}")
            return jsonify({'success': False, 'message': f'PDF oluşturma hatası: {str(layout_error)}'})

        # Yazdırma işlemi - eğer doğrudan yazdırma seçilmişse
        message = "PDF hazırlandı (yazdırma seçilmedi)"
        success = True

        if print_direct:
            print(f"\n🖨️ Yazdırma işlemi başlatılıyor...")
            success, message = advanced_print_pdf(output_pdf)
            print(f"🎯 Yazdırma sonucu: {success} - {message}")

        # Detaylı yanıt oluştur
        response_data = {
            'success': success,
            'message': message,
            'layout': layout,
            'filename': filename,
            'file_type': get_file_extension(filename),
            'original_size': os.path.getsize(filepath),
            'pdf_size': os.path.getsize(output_pdf) if os.path.exists(output_pdf) else 0,
            'system': platform.system(),
            'file_count': 1
        }
        # Geçici dosyaları temizle
        cleanup_files([filepath, output_pdf], success)
        return jsonify(response_data)
    except Exception as e:
        print(f"❌ Genel hata: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'İşlem hatası: {str(e)}',
            'error_type': type(e).__name__
        })


@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """Çoklu dosya yükleme"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
    files = request.files.getlist('files')
    layout = request.form.get('layout', '1')
    combine_files = request.form.get('combine', 'false').lower() == 'true'
    sort_files = request.form.get('sort', 'false').lower() == 'true'
    print_direct = request.form.get('print_direct', 'true').lower() == 'true'

    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'message': 'Dosya seçilmedi'})

    valid_files = []
    uploaded_files = []

    try:
        # Dosyaları kontrol et ve kaydet
        for file in files:
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Dosya erişim kontrolü
                accessible, access_msg = test_file_access(filepath)
                if accessible:
                    valid_files.append(filepath)
                    uploaded_files.append({
                        'name': filename,
                        'path': filepath,
                        'size': os.path.getsize(filepath),
                        'type': get_file_extension(filename)
                    })
                    print(
                        f"✅ Dosya kaydedildi: {filename} ({os.path.getsize(filepath)} bytes)")
                else:
                    print(f"❌ Dosya erişim hatası: {filename} - {access_msg}")

        if not valid_files:
            return jsonify({'success': False, 'message': 'Geçerli dosya bulunamadı'})

        print(f"\n📚 {len(valid_files)} dosya işlenecek")
        print(f"🔗 Birleştir: {combine_files}")
        print(f"📐 Layout: {layout}")

        # Dosyaları sırala
        if sort_files:
            valid_files.sort()
            print("📊 Dosyalar alfabetik sıralandı")

        # İşlem seçimi
        if combine_files:
            # Tüm dosyaları tek PDF'te birleştir
            try:
                combined_pdf = create_multi_file_pdf(valid_files, layout)
                if combined_pdf and os.path.exists(combined_pdf):
                    print(f"📄 Birleştirilmiş PDF oluşturuldu: {combined_pdf}")

                    # Yazdırma işlemi
                    success = True
                    message = "PDF hazırlandı (yazdırma seçilmedi)"

                    if print_direct:
                        success, message = advanced_print_pdf(combined_pdf)

                    # Yanıt verilerini hazırla
                    response_data = {
                        'success': success,
                        'message': message,
                        'layout': layout,
                        'file_count': len(valid_files),
                        'combined': True,
                        'files': uploaded_files,
                        'pdf_size': os.path.getsize(combined_pdf),
                        'system': platform.system()
                    }
                    # Dosyaları temizle
                    cleanup_files(valid_files + [combined_pdf], success)
                    return jsonify(response_data)
                else:
                    return jsonify({'success': False, 'message': 'Birleştirilmiş PDF oluşturulamadı'})
            except Exception as combine_error:
                print(f"❌ Birleştirme hatası: {combine_error}")
                return jsonify({'success': False, 'message': f'Birleştirme hatası: {str(combine_error)}'})
        else:
            # Her dosyayı ayrı ayrı işle
            results = []
            all_success = True
            processed_files = []
            for filepath in valid_files:
                try:
                    filename = os.path.basename(filepath)
                    print(f"\n📄 İşleniyor: {filename}")
                    # Layout PDF oluştur
                    output_pdf = create_layout_pdf(filepath, layout)
                    if output_pdf and os.path.exists(output_pdf):
                        # Yazdırma işlemi
                        success = True
                        message = "PDF hazırlandı (yazdırma seçilmedi)"

                        if print_direct:
                            success, message = advanced_print_pdf(output_pdf)

                        results.append({
                            'filename': filename,
                            'success': success,
                            'message': message,
                            'pdf_size': os.path.getsize(output_pdf) if os.path.exists(output_pdf) else 0
                        })
                        processed_files.append(output_pdf)
                        if not success:
                            all_success = False
                        print(f"🎯 {filename}: {success} - {message}")
                    else:
                        results.append({
                            'filename': filename,
                            'success': False,
                            'message': 'PDF oluşturulamadı'
                        })
                        all_success = False
                except Exception as file_error:
                    print(f"❌ {filename} işlem hatası: {file_error}")
                    results.append({
                        'filename': os.path.basename(filepath),
                        'success': False,
                        'message': f'İşlem hatası: {str(file_error)}'
                    })
                    all_success = False
            # Yanıt verilerini hazırla
            response_data = {
                'success': all_success,
                'message': f"{len([r for r in results if r['success']])}/{len(results)} dosya başarılı",
                'layout': layout,
                'file_count': len(valid_files),
                'combined': False,
                'files': uploaded_files,
                'results': results,
                'system': platform.system()
            }
            # Temizlik
            cleanup_files(valid_files + processed_files, True)
            return jsonify(response_data)
    except Exception as e:
        print(f"❌ Çoklu dosya genel hatası: {e}")
        import traceback
        traceback.print_exc()
        # Hata durumunda temizlik
        cleanup_files(valid_files, False)
        return jsonify({
            'success': False,
            'message': f'Çoklu dosya işlem hatası: {str(e)}',
            'error_type': type(e).__name__
        })


@app.route('/debug-printer')
def debug_printer():
    """Yazıcı debug bilgileri"""
    debug_printer_info()
    return jsonify({'status': 'Debug bilgileri konsola yazdırıldı'})


@app.route('/test-print/<filename>')
def test_print_file(filename):
    """Upload klasöründeki belirli bir dosyayı test yazdırma.

    GÜVENLİK: <path:filename> yerine <filename> kullanılıyor; path
    dönüştürücüsü '/' karakterine izin verdiği için dizin dışına çıkmayı
    mümkün kılıyordu. Ayrıca secure_filename ile normalize edilip
    realpath karşılaştırmasıyla UPLOAD_FOLDER içinde kaldığı doğrulanıyor.
    """
    try:
        safe_name = secure_filename(filename)
        if not safe_name:
            return jsonify({'success': False, 'message': 'Geçersiz dosya adı'}), 400

        upload_root = os.path.realpath(app.config['UPLOAD_FOLDER'])
        file_path = os.path.realpath(os.path.join(upload_root, safe_name))

        # Sınır kontrolü: dosya gerçekten upload klasörünün altında mı?
        if os.path.commonpath([upload_root, file_path]) != upload_root:
            return jsonify({'success': False, 'message': 'Geçersiz dosya yolu'}), 400

        if not os.path.isfile(file_path):
            return jsonify({'success': False, 'message': 'Dosya bulunamadı'}), 404

        success, message = advanced_print_pdf(file_path)
        return jsonify({
            'success': success,
            'message': message,
            'file': safe_name
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Test hatası: {str(e)}'})


@app.route('/status')
def status():
    """Sistem durumu"""
    try:
        info = {
            'system': platform.system(),
            'platform': platform.platform(),
            'ip': get_local_ip(),
            'port': 5000,
            'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
            'upload_folder_writable': os.access(app.config['UPLOAD_FOLDER'], os.W_OK),
            'max_file_size': app.config['MAX_CONTENT_LENGTH'],
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }
        if platform.system() == "Windows":
            try:
                import win32print
                default_printer = win32print.GetDefaultPrinter()
                info['default_printer'] = default_printer
                info['win32print_available'] = True
                # Yazıcı durumu
                try:
                    handle = win32print.OpenPrinter(default_printer)
                    printer_info = win32print.GetPrinter(handle, 2)
                    win32print.ClosePrinter(handle)
                    info['printer_status'] = printer_info['Status']
                    info['printer_ready'] = printer_info['Status'] == 0
                    info['printer_port'] = printer_info.get(
                        'pPortName', 'Bilinmiyor')
                except Exception as printer_error:
                    info['printer_error'] = str(printer_error)
            except ImportError:
                info['win32print_available'] = False
                info['error'] = 'win32print modülü bulunamadı - pip install pywin32'
            except Exception as e:
                info['win32print_error'] = str(e)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/cleanup-all', methods=['POST'])
def cleanup_all_files():
    """Tüm geçici dosyaları temizle.

    GÜVENLİK: Yıkıcı bir işlem olduğu için GET yerine POST. GET hâlinde
    herhangi bir sayfadaki <img src="..."> etiketi bile silmeyi
    tetikleyebiliyordu.
    """
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        files_deleted = 0
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        files_deleted += 1
                except Exception as e:
                    print(f"Dosya silinemedi {file_path}: {e}")
        return jsonify({
            'success': True,
            'message': f'{files_deleted} dosya temizlendi',
            'files_deleted': files_deleted
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Temizlik hatası: {str(e)}'})

# HTML şablonunu oluştur (ilk çalıştırmada)


def create_html_template():
    """index.html şablonunu oluştur"""
    template_path = os.path.join(app.config['TEMPLATES_FOLDER'], 'index.html')
    if not os.path.exists(template_path):
        print("HTML şablonu oluşturuluyor...")
        # Burada HTML kodunu bir dosyaya yazıyoruz
        with open(template_path, 'w', encoding='utf-8') as f:
            # Frontend kısmındaki HTML kodu buraya gelecek
            html_content = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canon PIXMA G2460 - Web Yazdır v2.0</title>
    <style>
        /* CSS kodları buraya gelecek */
    </style>
</head>
<body>
    <!-- HTML içeriği buraya gelecek -->
</body>
</html>"""
            f.write(html_content)
        print(f"HTML şablonu oluşturuldu: {template_path}")


if __name__ == '__main__':
    local_ip = get_local_ip()

    logger.info("=" * 60)
    logger.info("🖨️  WEB PRINT SERVICE - AĞ YAZDIRMA SERVİSİ v2.0")
    logger.info("=" * 60)
    logger.info(f"📍 Ana sayfa: http://localhost:{config.PORT}")
    logger.info(f"🌐 Ağ erişimi: http://{local_ip}:{config.PORT}")
    logger.info(f"🔧 Durum: http://localhost:{config.PORT}/status")
    logger.info(f"🐛 Debug: http://localhost:{config.PORT}/debug-printer")
    logger.info(f"🧹 Temizlik: http://localhost:{config.PORT}/cleanup-all")
    logger.info("📚 ÖZELLİKLER:")
    logger.info("   • Tek dosya yazdırma")
    logger.info("   • Çoklu dosya yazdırma")
    logger.info("   • Dosya birleştirme")
    logger.info("   • Layout seçenekleri (1,2,4,6,9)")
    logger.info(f"   • Desteklenen formatlar: {', '.join(ALLOWED_EXTENSIONS)}")
    logger.info(
        f"   • Maksimum dosya boyutu: {app.config['MAX_CONTENT_LENGTH']//1024//1024}MB")
    logger.info("=" * 60)

    # HTML şablonunu oluştur
    create_html_template()

    # Başlangıçta sistem bilgilerini göster (sadece debug modunda)
    if config.DEBUG:
        debug_printer_info()

    # Upload klasörü kontrolü
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.info(
            f"📁 Upload klasörü oluşturuldu: {app.config['UPLOAD_FOLDER']}")

    # Erişim token'ını göster. Servis kimlik doğrulaması olmadan
    # kullanılamaz; kullanıcının bu değeri görmesi gerekir.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        logger.info("=" * 60)
        logger.info("🔐 ERİŞİM TOKEN'I")
        if os.environ.get('PRINT_SERVICE_TOKEN'):
            logger.info("   Kaynak: PRINT_SERVICE_TOKEN ortam değişkeni")
        else:
            logger.info("   Kaynak: bu açılış için rastgele üretildi")
            logger.info("   Sabitlemek için: PRINT_SERVICE_TOKEN ortam değişkenini ayarlayın")
        logger.info(f"   Token: {config.ACCESS_TOKEN}")
        logger.info(
            f"   Giriş: http://{get_local_ip()}:{config.PORT}/?token={config.ACCESS_TOKEN}")
        logger.info("=" * 60)

    logger.info("\n🚀 Servis başlatılıyor...")
    logger.info("⏹️ Servisi durdurmak için Ctrl+C")
    logger.info("=" * 60)

    # Tarayıcıyı otomatik aç (sadece konfigürasyonda etkinse ve reloader değilse)
    # WERKZEUG_RUN_MAIN environment variable'ı reloader'ın ikinci çalışmasını belirtir
    if config.AUTO_OPEN_BROWSER and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        webbrowser.open(f"http://localhost:{config.PORT}")

    # Flask uygulamasını başlat
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
