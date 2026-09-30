# E.M.O — Kişisel Yapay Zeka Asistanı (V65)

Windows için PySide6 tabanlı, Iron Man'in JARVIS'inden ilham almış sesli asistan.

## Özellikler

- 🎙️ **Sesli komutlar:** Edge-TTS ile doğal Türkçe ses, çok dilli destek (14 dil)
- 🤖 **Çoklu AI motoru:** Ollama (yerel) → Gemini → Pollinations (yedek)
- 🖥️ **Sistem telemetrisi:** CPU/RAM/Disk canlı arc göstergeleri
- 📊 **Bilgisayar analizi:** Defender durumu, süreçler, yüklü uygulamalar
- 🚀 **Kapsamlı uygulama açma:** Kısayollar + Store + Registry + Program Files
- 📝 **Notlar, rehber, hatırlatıcı, hava durumu, hesap makinesi**
- 🔒 **Kalıcı izin sistemi:** Erişimleri tek tek onaylayın
- 🎨 **JARVIS animasyonlu çekirdek:** Durum değişince renk ve hız değişir

## Kurulum

### 1. Python 3.10+ gerekli
[python.org](https://www.python.org/downloads/) → indir → **"Add to PATH"** işaretli olacak

### 2. Sanal ortam (VS Code)
- `Ctrl+Shift+P` → **Python: Create Environment** → **Venv**
- Terminal açılır → şu komut:
```bash
pip install -r requirements.txt