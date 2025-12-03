"""
Layout Handler - PDF ve Resim Layout İşlemleri

Bu modül, resim dosyalarını belirtilen layout seçeneklerine göre
PDF'e dönüştürme işlemlerini gerçekleştirir.

Layout Seçenekleri:
    - 1: Tek sayfa (orijinal boyut)
    - 2: 2 kopya yan yana
    - 4: 4 kopya (2x2)
    - 6: 6 kopya (2x3)
    - 9: 9 kopya (3x3)

Örnek Kullanım:
    >>> from layout_handler import create_layout_pdf
    >>> output = create_layout_pdf("image.jpg", "4")
    >>> print(f"PDF oluşturuldu: {output}")
"""

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, mm
import os
import time
import tempfile
from pathlib import Path
import platform
import logging

# Logger yapılandırması
logger = logging.getLogger(__name__)


def get_image_size(image_path):
    """Resim boyutlarını al"""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        print(f"Resim boyutu alınamadı: {e}")
        return (800, 600)  # Varsayılan boyut


def create_layout_pdf(input_file, layout='1'):
    """
    Girdi dosyasını belirtilen layout'a göre PDF'e dönüştür
    Layout seçenekleri:
    1: Tek sayfa (orijinal boyut)
    2: 2 kopya yan yana
    4: 4 kopya (2x2)
    6: 6 kopya (2x3)
    9: 9 kopya (3x3)
    Not: PDF dosyaları için işlem yapılamaz, sadece resim dosyaları desteklenir.
    """
    print(f"🎨 Layout PDF oluşturuluyor: {input_file} -> Layout: {layout}")
    file_ext = Path(input_file).suffix.lower()
    output_dir = os.path.dirname(input_file)
    base_name = Path(input_file).stem
    output_pdf = os.path.join(output_dir, f"{base_name}_layout_{layout}.pdf")
    try:
        if file_ext == '.pdf':
            print("⚠️ PDF dosyaları desteklenmiyor. Sadece resim dosyaları işlenebilir.")
            return input_file
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
            return process_image_layout(input_file, output_pdf, layout)
        else:
            # Desteklenmeyen format için basit kopyalama
            print(f"⚠️ Desteklenmeyen dosya formatı: {file_ext}")
            return input_file  # Hata durumunda orijinal dosyayı döndür
    except Exception as e:
        print(f"❌ Layout PDF oluşturma hatası: {e}")
        return input_file  # Hata durumunda orijinal dosyayı döndür


def process_image_layout(input_image, output_pdf, layout):
    """Resim dosyası için layout işlemi"""
    try:
        # Resmi aç
        with Image.open(input_image) as img:
            # RGBA'ya dönüştür (şeffaflık desteği için)
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB')
            layout_num = int(layout)
            # A4 boyutları (300 DPI)
            a4_width, a4_height = 2480, 3508  # 300 DPI A4
            # PDF oluştur
            c = canvas.Canvas(output_pdf, pagesize=A4)
            temp_image_path = None
            try:
                if layout_num == 1:
                    # Tek resim - sayfaya sığdır
                    img_width, img_height = img.size
                    # Oranı koru
                    ratio = min(a4_width/img_width, a4_height/img_height) * 0.9
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    # Resimi yeniden boyutlandır
                    resized_img = img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS)
                    # Geçici dosya oluştur
                    temp_image_path = tempfile.mktemp(suffix='.jpg')
                    resized_img.save(temp_image_path, 'JPEG', quality=95)
                    # PDF'e ekle (ortalanmış)
                    x = (A4[0] - new_width * 72/300) / 2
                    y = (A4[1] - new_height * 72/300) / 2
                    c.drawImage(temp_image_path, x, y,
                                width=new_width * 72/300,
                                height=new_height * 72/300)
                else:
                    # Çoklu layout
                    if layout_num == 2:
                        cols, rows = 2, 1
                    elif layout_num == 4:
                        cols, rows = 2, 2
                    elif layout_num == 6:
                        cols, rows = 2, 3
                    elif layout_num == 9:
                        cols, rows = 3, 3
                    else:
                        cols, rows = 1, 1
                    # Her hücre boyutu
                    cell_width = A4[0] / cols
                    cell_height = A4[1] / rows
                    # Resimi küçült
                    small_width = int(a4_width / cols * 0.9)
                    small_height = int(a4_height / rows * 0.9)
                    # Oranı koru
                    img_ratio = img.size[0] / img.size[1]
                    cell_ratio = small_width / small_height
                    if img_ratio > cell_ratio:
                        # Genişlik sınırlayıcı
                        final_width = small_width
                        final_height = int(small_width / img_ratio)
                    else:
                        # Yükseklik sınırlayıcı
                        final_height = small_height
                        final_width = int(small_height * img_ratio)
                    small_img = img.resize(
                        (final_width, final_height), Image.Resampling.LANCZOS)
                    # Geçici dosya oluştur
                    temp_image_path = tempfile.mktemp(suffix='.jpg')
                    small_img.save(temp_image_path, 'JPEG', quality=95)
                    # Her hücreye resmi yerleştir
                    for row in range(rows):
                        for col in range(cols):
                            x = col * cell_width + \
                                (cell_width - final_width * 72/300) / 2
                            y = A4[1] - (row + 1) * cell_height + \
                                (cell_height - final_height * 72/300) / 2
                            c.drawImage(temp_image_path, x, y,
                                        width=final_width * 72/300,
                                        height=final_height * 72/300)
                c.save()
                # Geçici dosyayı temizle
                if temp_image_path and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                print(f"✅ Resim Layout tamamlandı: {output_pdf}")
                return output_pdf
            except Exception as inner_e:
                # Geçici dosyayı temizle
                if temp_image_path and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                raise inner_e
    except Exception as e:
        print(f"❌ Resim layout hatası: {e}")
        return input_image


def create_multi_file_pdf(file_list, layout='1'):
    """
    Birden fazla resim dosyasını tek PDF'te birleştir
    Not: Sadece resim dosyaları desteklenir, PDF dosyaları atlanır.
    """
    if not file_list:
        return None
    print(f"📚 Çoklu dosya PDF oluşturuluyor: {len(file_list)} dosya")
    # Sadece resim dosyalarını filtrele
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    image_files = [f for f in file_list if Path(
        f).suffix.lower() in image_extensions]
    if not image_files:
        print("❌ İşlenebilir resim dosyası bulunamadı")
        return None
    # Çıktı dosyası
    output_dir = os.path.dirname(
        file_list[0]) if file_list else tempfile.gettempdir()
    timestamp = int(time.time())
    output_pdf = os.path.join(
        output_dir, f"combined_layout_{layout}_{timestamp}.pdf")
    try:
        # Reportlab ile PDF oluştur
        c = canvas.Canvas(output_pdf, pagesize=A4)
        layout_num = int(layout)
        # Layout hesaplamaları
        if layout_num == 2:
            cols, rows = 2, 1
        elif layout_num == 4:
            cols, rows = 2, 2
        elif layout_num == 6:
            cols, rows = 2, 3
        elif layout_num == 9:
            cols, rows = 3, 3
        else:
            cols, rows = 1, 1
        current_position = 0
        total_positions = cols * rows
        for file_path in image_files:
            print(f"  📄 İşleniyor: {os.path.basename(file_path)}")
            try:
                with Image.open(file_path) as img:
                    if img.mode not in ['RGB', 'RGBA']:
                        img = img.convert('RGB')
                    # Yeni sayfa gerekli mi?
                    if current_position >= total_positions:
                        c.showPage()
                        current_position = 0
                    # Pozisyon hesapla
                    row = current_position // cols
                    col = current_position % cols
                    # Hücre boyutları
                    cell_width = A4[0] / cols
                    cell_height = A4[1] / rows
                    # Resim boyutlarını hesapla
                    img_width, img_height = img.size
                    target_width = int(2480 / cols * 0.9)  # 300 DPI
                    target_height = int(3508 / rows * 0.9)
                    # Oranı koru
                    img_ratio = img_width / img_height
                    cell_ratio = target_width / target_height
                    if img_ratio > cell_ratio:
                        final_width = target_width
                        final_height = int(target_width / img_ratio)
                    else:
                        final_height = target_height
                        final_width = int(target_height * img_ratio)
                    # Resimi yeniden boyutlandır
                    resized_img = img.resize(
                        (final_width, final_height), Image.Resampling.LANCZOS)
                    # Geçici dosya oluştur
                    temp_image_path = tempfile.mktemp(suffix='.jpg')
                    resized_img.save(temp_image_path, 'JPEG', quality=95)
                    # Pozisyon hesapla
                    x = col * cell_width + \
                        (cell_width - final_width * 72/300) / 2
                    y = A4[1] - (row + 1) * cell_height + \
                        (cell_height - final_height * 72/300) / 2
                    # Resimi PDF'e ekle
                    c.drawImage(temp_image_path, x, y,
                                width=final_width * 72/300,
                                height=final_height * 72/300)
                    # Geçici dosyayı temizle
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                    current_position += 1
            except Exception as img_error:
                print(f"⚠️ Resim işlenemedi {file_path}: {img_error}")
                continue
        # Son sayfayı kaydet
        c.save()
        print(f"✅ Çoklu dosya PDF tamamlandı: {output_pdf}")
        return output_pdf
    except Exception as e:
        print(f"❌ Çoklu dosya PDF hatası: {e}")
        return None


if __name__ == "__main__":
    # Test
    test_image = "test.jpg"
    if os.path.exists(test_image):
        output = create_layout_pdf(test_image, "4")
        print(f"Test çıktısı: {output}")
    else:
        print("Test etmek için bir resim dosyası gereklidir.")
