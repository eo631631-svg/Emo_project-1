"""E.M.O — Kişisel Yapay Zeka Asistanı. Giriş noktası."""
from emo.system import uygulama_taramayi_baslat
import sys
import threading
from PySide6.QtWidgets import QApplication

from emo.gui import AssistantGUI
from emo.system import uygulama_taramayi_baslat
import sys, traceback

# ★ V74: Global hata yakalayıcı — program çökmesin
def _global_excepthook(tip, deger, tb):
    print("\n" + "="*60)
    print("YAKALANMAYAN HATA:")
    print("="*60)
    traceback.print_exception(tip, deger, tb)
    print("="*60 + "\n")

sys.excepthook = _global_excepthook

# Thread'lerdeki hatalar da yakalansın
import threading
_eski_thread_hook = threading.excepthook
def _thread_hook(args):
    print(f"\n[Thread Hatası - {args.thread.name if args.thread else '?'}]")
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
threading.excepthook = _thread_hook


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    gui = AssistantGUI()
    gui.showMaximized()

    # ★ V82: Ağ koruması ve otomatik geri yükleme
    from emo import ag_koruma
    ag_koruma.ag_izleyici_baslat(gui)
    
    threading.Thread(target=gui.main_audio_loop, daemon=True).start()
        # Uygulama taramasını arka planda başlat (bloklamadan)
    threading.Thread(target=uygulama_taramayi_baslat, daemon=True).start()
    threading.Thread(target=gui.initialize_assistant, daemon=True).start()
        # ★ V68: Arka plan servisleri
    from emo import extras
    threading.Thread(target=extras.batarya_izleyici_baslat, args=(gui,), daemon=True).start()
    extras._pano_izleyici_baslat()
    threading.Thread(target=extras.hatirlaticilari_geri_yukle, args=(gui,), daemon=True).start()
    threading.Thread(target=extras.proaktif_kontrol, args=(gui,), daemon=True).start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()