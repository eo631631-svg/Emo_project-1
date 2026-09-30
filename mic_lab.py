"""
E.M.O MicLab — Tkinter versiyonu
Bağımlılık: pip install pyaudio numpy SpeechRecognition
Çalıştır: python mic_lab.py
"""
import sys, os, json, time, math, threading, collections
from datetime import datetime
from tkinter import (Tk, Frame, Label, Button, StringVar, IntVar, BooleanVar,
                      Canvas, Text, END, LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y,
                      HORIZONTAL, DISABLED, NORMAL)
from tkinter import ttk, messagebox

# --- Bağımlılıklar ---
try:
    import numpy as np
except ImportError:
    print("numpy kuruluyor...")
    os.system(f"{sys.executable} -m pip install numpy")
    import numpy as np

try:
    import pyaudio
except ImportError:
    print("pyaudio kuruluyor...")
    os.system(f"{sys.executable} -m pip install pyaudio")
    import pyaudio

try:
    import speech_recognition as sr
except ImportError:
    print("SpeechRecognition kuruluyor...")
    os.system(f"{sys.executable} -m pip install SpeechRecognition")
    import speech_recognition as sr


# ============================================================
# RENK PALETİ
# ============================================================
C_BG = "#06090f"
C_PANEL = "#0b1018"
C_PANEL_HI = "#101824"
C_BORDER = "#1a2d40"
C_CYAN = "#00d4ff"
C_CYAN_HI = "#7bf3ff"
C_GREEN = "#00ff9d"
C_AMBER = "#ffaa00"
C_RED = "#ff3344"
C_TEXT = "#d0e8f0"
C_TEXT_DIM = "#4a6b80"


# ============================================================
# SES YAKALAYICI THREAD
# ============================================================
class SesYakalayici:
    def __init__(self, cihaz_index=None, blok=1024):
        self.cihaz = cihaz_index
        self.blok = blok
        self._calisiyor = False
        self._thread = None
        self.rms = 0.0
        self.peak = 0.0
        self.son_dalga = None
        self.gurultu_toplama = False
        self.gurultu_ornekleri = []
        self.maks_rms = 0.0
        self.hata = None
        self.kanal_sayisi = 1
        self.ornek_orani = 16000

    def basla(self):
        if self._calisiyor: return
        self._calisiyor = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def dur(self):
        self._calisiyor = False
        if self._thread:
            self._thread.join(timeout=1.5)

    def _loop(self):
        pa = None
        stream = None
        try:
            pa = pyaudio.PyAudio()
            cihaz = self.cihaz
            if cihaz is None:
                cihaz = pa.get_default_input_device_info()["index"]
            b = pa.get_device_info_by_index(cihaz)
            self.ornek_orani = int(b.get("defaultSampleRate", 16000))
            self.kanal_sayisi = min(2, int(b.get("maxInputChannels", 1)))
            stream = pa.open(
                format=pyaudio.paInt16, channels=self.kanal_sayisi,
                rate=self.ornek_orani, input=True,
                frames_per_buffer=self.blok, input_device_index=cihaz)
            while self._calisiyor:
                try:
                    ham = stream.read(self.blok, exception_on_overflow=False)
                    if not ham: continue
                    veri = np.frombuffer(ham, dtype=np.int16)
                    if self.kanal_sayisi > 1:
                        veri = veri.reshape(-1, self.kanal_sayisi).mean(axis=1)
                    v = veri.astype(np.float64)
                    self.rms = float(np.sqrt(np.mean(v ** 2)))
                    self.peak = float(np.max(np.abs(v)))
                    self.son_dalga = v.copy()
                    self.maks_rms = max(self.maks_rms, self.rms)
                    if self.gurultu_toplama:
                        db = 20 * math.log10(max(self.rms, 1))
                        self.gurultu_ornekleri.append(db)
                except Exception as e:
                    self.hata = str(e); break
        except Exception as e:
            self.hata = str(e)
        finally:
            try:
                if stream:
                    stream.stop_stream(); stream.close()
            except: pass
            try:
                if pa: pa.terminate()
            except: pass


# ============================================================
# ANA UYGULAMA
# ============================================================
class MicLab:
    def __init__(self, root):
        self.root = root
        self.root.title("E.M.O MicLab — Mikrofon Teşhis Aracı")
        self.root.geometry("1100x800")
        self.root.configure(bg=C_BG)

        self.yakalayici = None
        self.cihazlar = {}
        self._build_ui()
        self._cihazlari_yukle()
        self._guncelle()  # periyodik güncelleme

    # -----------------------------------------------
    def _build_ui(self):
        # ÜST BAŞLIK
        top = Frame(self.root, bg=C_BG)
        top.pack(fill=X, padx=16, pady=(12, 6))

        Label(top, text="🎤  E.M.O MICLAB", bg=C_BG, fg=C_CYAN,
              font=("Consolas", 16, "bold")).pack(side=LEFT)
        Label(top, text="   Mikrofon Teşhis ve Kalibrasyon Aracı",
              bg=C_BG, fg=C_TEXT_DIM, font=("Segoe UI", 10)).pack(side=LEFT)

        self.durum_lbl = Label(top, text="● HAZIR", bg=C_PANEL, fg=C_AMBER,
                                font=("Consolas", 10, "bold"),
                                padx=14, pady=6, relief="solid", bd=1)
        self.durum_lbl.pack(side=RIGHT)

        # CİHAZ SEÇİMİ
        cihaz_frame = Frame(self.root, bg=C_PANEL, highlightbackground=C_BORDER,
                             highlightthickness=1)
        cihaz_frame.pack(fill=X, padx=16, pady=6)
        ic = Frame(cihaz_frame, bg=C_PANEL)
        ic.pack(fill=X, padx=14, pady=10)

        Label(ic, text="🎙️  Mikrofon:", bg=C_PANEL, fg=C_TEXT,
              font=("Segoe UI", 10)).pack(side=LEFT, padx=(0, 10))

        self.cihaz_combo = ttk.Combobox(ic, state="readonly", width=60,
                                         font=("Consolas", 9))
        self.cihaz_combo.pack(side=LEFT, padx=(0, 10))
        self.cihaz_combo.bind("<<ComboboxSelected>>", lambda e: self._cihaz_degisti())

        self.basla_btn = Button(ic, text="▶ BAŞLAT", bg=C_CYAN, fg=C_BG,
                                 font=("Consolas", 10, "bold"),
                                 relief="flat", padx=20, pady=6,
                                 cursor="hand2", command=self._basla_durdur)
        self.basla_btn.pack(side=LEFT)

        self.yenile_btn = Button(ic, text="🔄 Yenile", bg=C_PANEL_HI, fg=C_TEXT,
                                  font=("Segoe UI", 9), relief="flat",
                                  padx=12, pady=6, cursor="hand2",
                                  command=self._cihazlari_yukle)
        self.yenile_btn.pack(side=LEFT, padx=6)

        # SEVİYE GÖSTERGESİ
        seviye_frame = Frame(self.root, bg=C_PANEL, highlightbackground=C_BORDER,
                              highlightthickness=1)
        seviye_frame.pack(fill=X, padx=16, pady=6)
        self.seviye_canvas = Canvas(seviye_frame, bg=C_BG, height=200,
                                     highlightthickness=0)
        self.seviye_canvas.pack(fill=X, padx=14, pady=10)

        # DALGA FORMU
        dalga_frame = Frame(self.root, bg=C_PANEL, highlightbackground=C_BORDER,
                             highlightthickness=1)
        dalga_frame.pack(fill=X, padx=16, pady=6)
        self.dalga_canvas = Canvas(dalga_frame, bg=C_BG, height=120,
                                    highlightthickness=0)
        self.dalga_canvas.pack(fill=X, padx=14, pady=10)

        # KALİBRASYON
        kal_frame = Frame(self.root, bg=C_PANEL, highlightbackground=C_BORDER,
                           highlightthickness=1)
        kal_frame.pack(fill=X, padx=16, pady=6)

        Label(kal_frame, text="KALİBRASYON", bg=C_PANEL, fg=C_CYAN_HI,
              font=("Consolas", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 4))

        kal_ic = Frame(kal_frame, bg=C_PANEL)
        kal_ic.pack(fill=X, padx=14, pady=(0, 10))

        # Satır 1: Gürültü ölç
        Button(kal_ic, text="🔇  1. GÜRÜLTÜ TABANI ÖLÇ (3 sn sessiz kal)",
               bg=C_BG, fg=C_CYAN, font=("Segoe UI", 9, "bold"),
               relief="solid", bd=1, padx=14, pady=8, anchor="w",
               cursor="hand2", command=self._gurultu_olc).pack(fill=X, pady=3)

        # Satır 2: Eşik ayarı
        esik_satir = Frame(kal_ic, bg=C_PANEL)
        esik_satir.pack(fill=X, pady=3)
        Label(esik_satir, text="Eşik (dB):", bg=C_PANEL, fg=C_TEXT,
              font=("Segoe UI", 9)).pack(side=LEFT)
        self.esik_var = IntVar(value=-40)
        self.esik_slider = ttk.Scale(esik_satir, from_=-70, to=-10,
                                      orient=HORIZONTAL, variable=self.esik_var,
                                      command=lambda v: self._esik_degisti())
        self.esik_slider.pack(side=LEFT, fill=X, expand=True, padx=10)
        self.esik_lbl = Label(esik_satir, text="-40 dB", bg=C_PANEL,
                               fg=C_CYAN_HI, font=("Consolas", 10, "bold"), width=8)
        self.esik_lbl.pack(side=LEFT)

        # Satır 3: Konuşma testi
        Button(kal_ic, text="🗣️  2. KONUŞMA TESTİ (5 sn konuş)",
               bg=C_BG, fg=C_GREEN, font=("Segoe UI", 9, "bold"),
               relief="solid", bd=1, padx=14, pady=8, anchor="w",
               cursor="hand2", command=self._konusma_testi).pack(fill=X, pady=3)

        # Satır 4: Kaydet
        Button(kal_ic, text="💾  3. AYARLARI KAYDET (mic_ayarlari.json)",
               bg=C_BG, fg=C_AMBER, font=("Segoe UI", 9, "bold"),
               relief="solid", bd=1, padx=14, pady=8, anchor="w",
               cursor="hand2", command=self._ayarlari_kaydet).pack(fill=X, pady=3)

        # KONUŞMA TANIMA TESTİ
        tan_frame = Frame(self.root, bg=C_PANEL, highlightbackground=C_BORDER,
                           highlightthickness=1)
        tan_frame.pack(fill=X, padx=16, pady=6)

        Label(tan_frame, text="CANLI TEST", bg=C_PANEL, fg=C_CYAN_HI,
              font=("Consolas", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 4))

        tan_ic = Frame(tan_frame, bg=C_PANEL)
        tan_ic.pack(fill=X, padx=14, pady=(0, 10))

        Button(tan_ic, text="🎤  KONUŞMA TANIMA TESTİ",
               bg=C_BG, fg=C_CYAN, font=("Segoe UI", 9, "bold"),
               relief="solid", bd=1, padx=14, pady=8,
               cursor="hand2", command=self._tanima_testi).pack(anchor="w")

        self.tanima_lbl = Label(tan_ic, text="Test için tıkla",
                                 bg=C_BG, fg=C_TEXT_DIM,
                                 font=("Segoe UI", 10), anchor="w",
                                 padx=10, pady=10, relief="solid", bd=1,
                                 wraplength=1000, justify="left")
        self.tanima_lbl.pack(fill=X, pady=(6, 0))

        # LOG
        log_frame = Frame(self.root, bg=C_PANEL, highlightbackground=C_BORDER,
                           highlightthickness=1)
        log_frame.pack(fill=X, padx=16, pady=(6, 12))
        self.log_text = Text(log_frame, bg=C_BG, fg=C_TEXT,
                              font=("Consolas", 8), height=6,
                              relief="flat", insertbackground=C_CYAN)
        self.log_text.pack(fill=X, padx=14, pady=10)

        self._logla("✅ MicLab başlatıldı")

    # -----------------------------------------------
    def _logla(self, mesaj):
        zaman = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{zaman}] {mesaj}\n")
        self.log_text.see(END)

    def _cihazlari_yukle(self):
        self.cihaz_combo["values"] = []
        self.cihazlar = {}
        try:
            pa = pyaudio.PyAudio()
            n = pa.get_device_count()
            secenekler = []
            for i in range(n):
                try:
                    b = pa.get_device_info_by_index(i)
                    if int(b.get("maxInputChannels", 0)) > 0:
                        ad = b.get("name", f"Cihaz {i}")
                        self.cihazlar[i] = ad
                        secenekler.append(f"[{i}] {ad}")
                except Exception as e:
                    self._logla(f"Cihaz {i} atlandı: {e}")
            pa.terminate()
            self.cihaz_combo["values"] = secenekler
            if secenekler:
                self.cihaz_combo.current(0)
                self._logla(f"✅ {len(secenekler)} mikrofon bulundu")
            else:
                self._logla("⚠ Hiç mikrofon bulunamadı")
        except Exception as e:
            self._logla(f"❌ Cihaz listesi alınamadı: {e}")

    def _cihaz_degisti(self):
        if self.yakalayici and self.yakalayici._calisiyor:
            self._basla_durdur()  # durdur
            self._basla_durdur()  # yeni cihazla başlat

    def _secili_cihaz(self):
        secim = self.cihaz_combo.current()
        if secim < 0: return None
        keys = list(self.cihazlar.keys())
        if secim >= len(keys): return None
        return keys[secim]

    def _basla_durdur(self):
        if self.yakalayici is None:
            cihaz = self._secili_cihaz()
            if cihaz is None:
                self._logla("⚠ Önce mikrofon seç")
                return
            self.yakalayici = SesYakalayici(cihaz_index=cihaz)
            self.yakalayici.basla()
            time.sleep(0.3)
            if self.yakalayici.hata:
                self._logla(f"❌ Başlatma hatası: {self.yakalayici.hata}")
                self.yakalayici = None
                return
            self.basla_btn.config(text="⏹ DURDUR", bg=C_RED, fg="#ffffff")
            self.durum_lbl.config(text="● CANLI", fg=C_GREEN, bg=C_PANEL)
            self._logla("▶ Ses yakalama başladı")
        else:
            self.yakalayici.dur()
            self.yakalayici = None
            self.basla_btn.config(text="▶ BAŞLAT", bg=C_CYAN, fg=C_BG)
            self.durum_lbl.config(text="● HAZIR", fg=C_AMBER, bg=C_PANEL)
            self._logla("⏸ Ses yakalama durduruldu")

    def _esik_degisti(self):
        v = int(self.esik_var.get())
        self.esik_lbl.config(text=f"{v} dB")

    def _gurultu_olc(self):
        if not self.yakalayici:
            self._logla("⚠ Önce BAŞLAT'a bas")
            return
        self.yakalayici.gurultu_toplama = True
        self.yakalayici.gurultu_ornekleri = []
        self._logla("🔇 3 saniye sessiz kalın...")

        def _bitir():
            time.sleep(3.0)
            self.yakalayici.gurultu_toplama = False
            ornekler = self.yakalayici.gurultu_ornekleri
            if not ornekler:
                self._logla("⚠ Ölçüm alınamadı")
                return
            s = sorted(ornekler)
            kes = int(len(s) * 0.1)
            if kes > 0: s = s[:-kes]
            medyan = s[len(s) // 2]
            onerilen = int(medyan + 12)
            onerilen = max(-70, min(-10, onerilen))
            self.esik_var.set(onerilen)
            self._esik_degisti()
            self._logla(f"✅ Gürültü: {medyan:.1f} dB → Eşik önerisi: {onerilen} dB")
        threading.Thread(target=_bitir, daemon=True).start()

    def _konusma_testi(self):
        if not self.yakalayici:
            self._logla("⚠ Önce BAŞLAT'a bas")
            return
        self.yakalayici.maks_rms = 0.0
        self._logla("🗣️ 5 saniye konuşun...")

        def _bitir():
            time.sleep(5.0)
            mr = self.yakalayici.maks_rms
            if mr == 0:
                self._logla("❌ Ses algılanmadı")
                return
            db = 20 * math.log10(max(mr, 1))
            esik = int(self.esik_var.get())
            fark = db - esik
            if fark > 15:
                self._logla(f"✅ Mükemmel! Konuşma: {db:.1f} dB (eşiğin {fark:.1f} dB üstü)")
            elif fark > 5:
                self._logla(f"✓ İyi. Konuşma: {db:.1f} dB (eşiğin {fark:.1f} dB üstü)")
            else:
                self._logla(f"⚠ Zayıf! Konuşma: {db:.1f} dB (fark sadece {fark:.1f} dB)")
                self._logla("   → Mikrofonu yaklaştır ya da ses artır")
        threading.Thread(target=_bitir, daemon=True).start()

    def _tanima_testi(self):
        if not self.yakalayici:
            self._logla("⚠ Önce BAŞLAT'a bas")
            return
        cihaz = self._secili_cihaz()
        self.tanima_lbl.config(text="🎤 Dinleniyor... 5 saniye konuşun", fg=C_CYAN)
        def _g():
            try:
                r = sr.Recognizer()
                r.energy_threshold = 250
                r.dynamic_energy_threshold = True
                r.pause_threshold = 0.6
                r.operation_timeout = 8
                with sr.Microphone(device_index=cihaz) as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        ses = r.listen(source, timeout=6, phrase_time_limit=6)
                    except sr.WaitTimeoutError:
                        self.root.after(0, lambda: self.tanima_lbl.config(
                            text="❌ Ses algılanmadı", fg=C_RED))
                        return
                try:
                    metin = r.recognize_google(ses, language="tr-TR")
                    self.root.after(0, lambda: self.tanima_lbl.config(
                        text=f"📝 {metin}", fg=C_GREEN))
                    self._logla(f"Konuşma tanıma: {metin}")
                except sr.UnknownValueError:
                    self.root.after(0, lambda: self.tanima_lbl.config(
                        text="❌ Anlaşılamadı - daha net konuş", fg=C_RED))
                except sr.RequestError as e:
                    self.root.after(0, lambda: self.tanima_lbl.config(
                        text=f"❌ İnternet hatası: {e}", fg=C_RED))
            except Exception as e:
                self.root.after(0, lambda: self.tanima_lbl.config(
                    text=f"❌ Hata: {e}", fg=C_RED))
        threading.Thread(target=_g, daemon=True).start()

    def _ayarlari_kaydet(self):
        ayarlar = {
            "cihaz_index": self._secili_cihaz(),
            "cihaz_adi": self.cihaz_combo.get(),
            "energy_threshold": int(self.esik_var.get()),
            "dynamic_energy": False,
            "pause_threshold": 0.45,
            "non_speaking_duration": 0.20,
            "phrase_threshold": 0.15,
            "operation_timeout": 5,
            "tarih": datetime.now().isoformat(),
        }
        try:
            with open("mic_ayarlari.json", "w", encoding="utf-8") as f:
                json.dump(ayarlar, f, ensure_ascii=False, indent=2)
            self._logla(f"💾 Kaydedildi: mic_ayarlari.json")
            self._logla(f"   Cihaz: {ayarlar['cihaz_adi']}")
            self._logla(f"   Eşik: {ayarlar['energy_threshold']} dB")
            messagebox.showinfo("Kaydedildi",
                                 "mic_ayarlari.json dosyasına kaydedildi.\n"
                                 "E.M.O bir sonraki başlatmada bu ayarları kullanacak.")
        except Exception as e:
            self._logla(f"❌ Kaydetme hatası: {e}")

    # -----------------------------------------------
    # PERİYODİK GÜNCELLEME (Canvas çizimi)
    # -----------------------------------------------
    def _guncelle(self):
        try:
            self._ciz_seviye()
            self._ciz_dalga()
        except Exception as e:
            pass
        self.root.after(40, self._guncelle)

    def _ciz_seviye(self):
        c = self.seviye_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10: return

        # Zemin ızgarası
        for db in range(-80, 1, 10):
            x = int((db + 80) / 80 * (w - 20)) + 10
            renk = C_BORDER if db % 20 else C_TEXT_DIM
            c.create_line(x, 30, x, h - 25, fill=renk)
            c.create_text(x, h - 12, text=f"{db}dB", fill=C_TEXT_DIM,
                          font=("Consolas", 7))

        # Ses verisi
        if self.yakalayici and self.yakalayici._calisiyor:
            rms = self.yakalayici.rms
            peak = self.yakalayici.peak
            rms_db = 20 * math.log10(max(rms, 1))
            peak_db = 20 * math.log10(max(peak, 1))

            # Eşik çizgisi
            esik = int(self.esik_var.get())
            x_esik = int((esik + 80) / 80 * (w - 20)) + 10
            c.create_line(x_esik, 10, x_esik, h - 20, fill=C_RED, width=2)
            c.create_text(x_esik + 4, 10, text=f"EŞİK {esik}dB",
                          fill=C_RED, font=("Bahnschrift", 8, "bold"), anchor="w")

            # RMS bar
            x_rms = int((max(-80, min(0, rms_db)) + 80) / 80 * (w - 20)) + 10
            renk = C_GREEN if rms_db < esik else C_RED
            c.create_rectangle(10, h // 2 - 20, x_rms, h // 2 + 20,
                                fill=renk, outline="")

            # Peak işareti
            x_peak = int((max(-80, min(0, peak_db)) + 80) / 80 * (w - 20)) + 10
            c.create_line(x_peak, h // 2 - 25, x_peak, h // 2 + 25,
                          fill="#ffffff", width=2)

            # Üst metin
            fark = rms_db - esik
            c.create_text(10, 15, anchor="w",
                          text=f"RMS: {rms_db:+.1f} dB   PEAK: {peak_db:+.1f} dB   FARK: {fark:+.1f} dB",
                          fill=C_CYAN_HI, font=("Bahnschrift", 11, "bold"))
        else:
            c.create_text(w // 2, h // 2, text="Mikrofon kapalı · BAŞLAT'a bas",
                          fill=C_TEXT_DIM, font=("Segoe UI", 12))

    def _ciz_dalga(self):
        c = self.dalga_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10: return
        # Merkez çizgi
        c.create_line(0, h // 2, w, h // 2, fill=C_BORDER)
        if not self.yakalayici or not self.yakalayici._calisiyor:
            return
        v = self.yakalayici.son_dalga
        if v is None or len(v) == 0: return
        n = len(v)
        step = max(1, n // (w * 2))
        # Renk
        rms = self.yakalayici.rms
        db = 20 * math.log10(max(rms, 1))
        if db > -20: renk = C_RED
        elif db > -40: renk = C_CYAN_HI
        else: renk = C_CYAN
        # Noktalar
        noktalar = []
        for i in range(0, n, step):
            x = int(i / n * w)
            val = v[i] / 32768.0
            y = int(h / 2 - val * (h / 2 - 8))
            noktalar.extend([x, y])
        if len(noktalar) >= 4:
            c.create_line(noktalar, fill=renk, width=1)

    def kapat(self):
        try:
            if self.yakalayici:
                self.yakalayici.dur()
        except: pass
        self.root.destroy()


def main():
    root = Tk()
    app = MicLab(root)
    root.protocol("WM_DELETE_WINDOW", app.kapat)
    root.mainloop()


if __name__ == "__main__":
    main()