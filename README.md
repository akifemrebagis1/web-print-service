# 🖨️ Web Print Service

> Turn any USB printer into a network printer — print from any device on your local network through a beautiful web interface.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)

---

## 🎯 Problem & Solution

**Problem:** You have a USB printer with no Wi-Fi/network support. Only the connected PC can print.

**Solution:** This service runs a web server on the connected PC, allowing **any device on the network** (phones, tablets, other PCs) to upload and print files through a browser.

---

## ✨ Features

- 🌐 **Network printing** — print from any device on your local network
- 📱 **Mobile friendly** — responsive web UI works on phones and tablets
- 📄 **Multi-format** — supports PDF, PNG, JPG, JPEG, BMP, GIF, TIFF
- 📐 **Layout options** — print 1, 2, 4, 6, or 9 copies per page
- 📎 **File merging** — combine multiple files into a single print job
- 🔍 **Auto-detect printer** — automatically finds the system's default printer
- 🖥️ **Cross-platform** — Windows, Linux, macOS support
- 🚀 **One-click start** — includes `start_print_service.bat` for Windows

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/akifemrebagis1/web-print-service.git
cd web-print-service

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
```

### Run

```bash
# Linux/macOS
python app.py

# Windows (double-click or run)
start_print_service.bat
```

Then open `http://<YOUR_PC_IP>:5000` from any device on your network.

---

## 📐 Layout Options

| Layout | Description |
|--------|-------------|
| **1** | Original size (full page) |
| **2** | 2 copies side by side |
| **4** | 4 copies (2×2 grid) |
| **6** | 6 copies (2×3 grid) |
| **9** | 9 copies (3×3 grid) |

---

## 🏗️ Architecture

```
┌─────────────────────────┐
│  Phone / Tablet / PC    │  ← Any device on the network
│  (Web Browser)          │
└────────┬────────────────┘
         │ HTTP
┌────────▼────────────────┐
│  Flask Web Server       │  ← Runs on the PC with USB printer
│  - File upload          │
│  - Layout processing    │
│  - Print queue          │
└────────┬────────────────┘
         │
┌────────▼────────────────┐
│  USB Printer            │  ← No network needed!
└─────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python, Flask |
| **Image Processing** | Pillow (PIL) |
| **PDF Generation** | ReportLab |
| **Printing** | pywin32 (Windows) / CUPS (Linux/macOS) |
| **Frontend** | HTML5, CSS3, JavaScript |

---

## 📄 License

MIT License
