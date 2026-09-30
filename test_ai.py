"""E.M.O AI Sağlayıcı Tanı Testi — hangisi çalışıyor görelim."""
import sys, time, json, socket
import requests

print("=" * 70)
print("  E.M.O AI SAĞLAYICI TANI TESTİ")
print("=" * 70)
print()

# 0) Genel internet
print("[0] İnternet erişimi...")
try:
    r = requests.get("https://www.google.com", timeout=5)
    print(f"    ✅ Google erişilebilir (HTTP {r.status_code})")
except Exception as e:
    print(f"    ❌ Google erişilemiyor: {e}")
    sys.exit(1)
print()

# 1) DNS
print("[1] DNS çözümleme...")
for host in ["google.com", "duckduckgo.com", "pollinations.ai", "text.pollinations.ai",
             "api-inference.huggingface.co", "generativelanguage.googleapis.com"]:
    try:
        ip = socket.gethostbyname(host)
        print(f"    ✅ {host:45s} → {ip}")
    except Exception as e:
        print(f"    ❌ {host:45s} → {e}")
print()

# 2) Ollama
print("[2] Ollama (yerel yapay zeka)...")
try:
    r = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
    modeller = r.json().get("models", [])
    print(f"    ✅ Ollama çalışıyor ({len(modeller)} model)")
    for m in modeller:
        print(f"       • {m['name']}  ({m.get('size', 0) / 1e9:.2f} GB)")
except Exception as e:
    print(f"    ❌ Ollama yok: {e}")
print()

# 3) Pollinations GET
print("[3] Pollinations GET (key gerekmez)...")
try:
    t = time.time()
    r = requests.get("https://text.pollinations.ai/Merhaba%20nasilsin", timeout=20)
    sure = time.time() - t
    if r.status_code == 200 and r.text.strip():
        print(f"    ✅ HTTP 200 ({sure:.1f}s)")
        print(f"       Cevap: {r.text[:150]}...")
    else:
        print(f"    ⚠️  HTTP {r.status_code} ({sure:.1f}s)")
        print(f"       Detay: {r.text[:150]}")
except Exception as e:
    print(f"    ❌ Hata: {e}")
print()

# 4) Pollinations POST
print("[4] Pollinations POST...")
try:
    t = time.time()
    r = requests.post("https://text.pollinations.ai/openai",
        json={"model": "openai", "messages": [{"role": "user", "content": "Merhaba nasılsın?"}]},
        timeout=20)
    sure = time.time() - t
    if r.status_code == 200:
        j = r.json()
        c = j.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"    ✅ HTTP 200 ({sure:.1f}s)")
        print(f"       Cevap: {c[:150]}...")
    else:
        print(f"    ⚠️  HTTP {r.status_code} ({sure:.1f}s)")
except Exception as e:
    print(f"    ❌ Hata: {e}")
print()

# 5) DuckDuckGo AI Chat
print("[5] DuckDuckGo AI Chat...")
try:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    sr = requests.get("https://duckduckgo.com/duckchat/v1/status",
                      headers={"x-vqd-accept": "1", **headers}, timeout=10)
    print(f"       Status HTTP: {sr.status_code}")
    vqd = sr.headers.get("x-vqd-4")
    if not vqd:
        print(f"    ❌ VQD token alınamadı")
        print(f"       Headers: {dict(sr.headers)}")
    else:
        print(f"    ✅ VQD token: {vqd[:30]}...")
        headers["x-vqd-4"] = vqd
        r2 = requests.post("https://duckduckgo.com/duckchat/v1/chat",
            headers=headers,
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Merhaba"}]},
            timeout=20, stream=True)
        print(f"       Chat HTTP: {r2.status_code}")
        if r2.status_code == 200:
            toplanan = ""
            for satir in r2.iter_lines(decode_unicode=True):
                if not satir: continue
                if satir.startswith("data: "):
                    v = satir[6:].strip()
                    if v == "[DONE]": break
                    try:
                        j = json.loads(v)
                        if "message" in j: toplanan += j["message"]
                    except: pass
            if toplanan:
                print(f"    ✅ Cevap: {toplanan[:150]}...")
            else:
                print(f"    ⚠️  Cevap gelmedi")
        else:
            print(f"    ❌ HTTP {r2.status_code}: {r2.text[:200]}")
except Exception as e:
    print(f"    ❌ Hata: {e}")
print()

# 6) HuggingFace Inference
print("[6] HuggingFace Inference (ücretsiz)...")
try:
    r = requests.post("https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct",
                      json={"inputs": "Merhaba, nasılsın?", "parameters": {"max_new_tokens": 80}},
                      timeout=20)
    if r.status_code == 200:
        print(f"    ✅ HTTP 200")
        print(f"       Cevap: {str(r.json())[:150]}...")
    else:
        print(f"    ⚠️  HTTP {r.status_code}: {r.text[:150]}")
except Exception as e:
    print(f"    ❌ Hata: {e}")
print()

# 7) Winget kontrolü (Ollama kurulumu için)
print("[7] Ollama kurulumu için ortam kontrolü...")
import shutil
if shutil.which("winget"):
    print(f"    ✅ winget mevcut → otomatik Ollama kurabiliriz")
else:
    print(f"    ❌ winget yok → manuel Ollama kurulumu gerekli")
print()

print("=" * 70)
print("  TEST TAMAMLANDI")
print("=" * 70)
print()
print("Bana ✅ ve ❌ sonuçlarını gönder, hangi sağlayıcıyı kullanacağımızı göreceğiz.")