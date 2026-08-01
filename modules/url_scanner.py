import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
from modules.http_utils import status_str


class UrlScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="URL Analiz & Guvenlik Kontrolu")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Web sitesinin guvenlik basliklarini, koruma duzeyini ve olasi saldiri vektorlerini analiz eder.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef URL")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek.com")
        self.entry.set_size_request(400, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Analiz Et")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)
        input_box.pack_start(hbox, False, False, 0)

        frame.add(input_box)
        self.pack_start(frame, False, False, 0)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_monospace(True)
        self.textview.get_style_context().add_class("output-text")
        self.textbuffer = self.textview.get_buffer()
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.textview)
        self.pack_start(sw, True, True, 0)

        self.status_label = Gtk.Label(label="")
        self.status_label.set_xalign(0)
        self.pack_start(self.status_label, False, False, 0)

        self.running = False

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_scan(self):
        url = self.entry.get_text().strip()
        if not url:
            self.status_label.set_text("URL girin")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.entry.set_text(url)
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Analiz ediliyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        if not url.startswith("http"):
            url = "https://" + url

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, "")

        resp = None
        for scheme in ["https://", "http://"]:
            try:
                test_url = scheme + url.split("://", 1)[1]
                resp = requests.get(test_url, timeout=10, allow_redirects=True, headers=headers)
                if resp.status_code < 400 or resp.status_code in (403, 429):
                    break
            except Exception:
                continue

        if resp is None:
            try:
                resp = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
            except Exception as e:
                GLib.idle_add(self.log, f"[-] Baglanti kurulamadi: {e}")
                GLib.idle_add(self.log, "    Muhtemel sebepler:")
                GLib.idle_add(self.log, "    - Site kapali veya erisilemez")
                GLib.idle_add(self.log, "    - DNS cozulemedi")
                GLib.idle_add(self.log, "    - Guvenlik duvari (WAF/Cloudflare) engelliyor")
                GLib.idle_add(self.log, "    - IPv6 sorunu")
                GLib.idle_add(self.finish_scan)
                return

        h = resp.headers
        son_url = resp.url

        GLib.idle_add(self.log, f"[+] Durum: {status_str(resp.status_code)}")
        GLib.idle_add(self.log, f"[+] Son URL: {son_url}")

        server = h.get("Server", "?")
        powered = h.get("X-Powered-By", "")

        cloudflare = "cloudflare" in server.lower() or "CF-Ray" in h or "cf-cache-status" in h

        if cloudflare:
            GLib.idle_add(self.log, "[+] Guvenlik: Cloudflare tespit edildi")
        elif server.lower() in ("cloudflare",):
            GLib.idle_add(self.log, "[+] Guvenlik: Cloudflare tespit edildi")
        elif resp.status_code == 403 and "cloudflare" in resp.text[:500].lower():
            GLib.idle_add(self.log, "[+] Guvenlik: Cloudflare tespit edildi (403 engellemesi)")
        else:
            waf_sinyalleri = []
            for k in h:
                if any(x in k.lower() for x in ("waf", "shield", "firewall", "sec-", "x-protect")):
                    waf_sinyalleri.append(f"{k}: {h[k][:60]}")
            if waf_sinyalleri:
                GLib.idle_add(self.log, "[*] Guvenlik: WAF/Guvenlik duvari sinyalleri var")
                for s in waf_sinyalleri:
                    GLib.idle_add(self.log, f"      {s}")
            else:
                GLib.idle_add(self.log, "[-] Guvenlik: Bilinen bir WAF tespit edilemedi")

        GLib.idle_add(self.log, f"[+] Sunucu: {server}{' | ' + powered if powered else ''}")
        GLib.idle_add(self.log, "")

        GLib.idle_add(self.log, "=== GUVENLIK BASLIKLARI ===")
        GLib.idle_add(self.log, "")

        header_info = [
            ("Strict-Transport-Security", "HSTS (HTTPS zorlamasi)",
             "SSL Strip: HTTPS'yi HTTP'ye dusurup trafigi dinleme"),
            ("X-Frame-Options", "X-Frame-Options (Clickjacking)",
             "Clickjacking: Siteyi baska site icinde frame'de gosterip tuzağa dusurme"),
            ("X-Content-Type-Options", "MIME Sniffing Korumasi",
             "MIME Sniffing: JS/resim maskeli zararli dosya yukletme"),
            ("Content-Security-Policy", "CSP (XSS Korumasi)",
             "XSS: Script enjekte edip kullaniciyi hedef alma"),
            ("X-XSS-Protection", "XSS Filtresi",
             "Reflected XSS: URL'den gelen script'i calistirma"),
            ("Referrer-Policy", "Referrer Politikasi",
             "Bilgi sizintisi: URL'yi harici sitelere gonderme"),
            ("Permissions-Policy", "Permissions-Policy",
             "Yetkisiz API: Kamera/mikrofon/GPS'i calma"),
        ]

        for key, name, saldiri in header_info:
            val = h.get(key)
            GLib.idle_add(self.log, f"[{key}]")
            if val:
                GLib.idle_add(self.log, f"  [+] {name}: KORUMALI ({val[:80]})")
            else:
                GLib.idle_add(self.log, f"  [-] {name}: KORUMASIZ")
                GLib.idle_add(self.log, f"      Risk: {saldiri}")
            GLib.idle_add(self.log, "")

        GLib.idle_add(self.log, "=== OZET ===")
        total = len(header_info)
        mevcut = sum(1 for key, _, _ in header_info if h.get(key))
        GLib.idle_add(self.log, f"  {mevcut}/{total} guvenlik basligi mevcut")
        if mevcut < total:
            GLib.idle_add(self.log, f"  [!] {total - mevcut} potansiyel guvenlik acigi")
            for key, name, saldiri in header_info:
                if not h.get(key):
                    GLib.idle_add(self.log, f"      - {name} -> {saldiri}")
        else:
            GLib.idle_add(self.log, "  [*] Tum temel basliklar mevcut, iyi yapilandirilmis")
        GLib.idle_add(self.log, "")

        if cloudflare:
            GLib.idle_add(self.log, "=== CLOUDFLARE DEGERLENDIRMESI ===")
            GLib.idle_add(self.log, "  [+] Korur: DDoS, SQL Injection, XSS, L7 saldirilarina karsi")
            GLib.idle_add(self.log, "  [+] WAF kurallari ile ozellestirilebilir")
            GLib.idle_add(self.log, "  [-] Asil sunucu IP'si bulunursa Cloudflare baypas edilebilir")
            GLib.idle_add(self.log, "  [-] SSL/TLS ayarlari yanlissa trafik cozulebilir")
            GLib.idle_add(self.log, "  [-] Uygulama katmaninda (L7) acik varsa WAF atlatilabilir")
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, "  Nasil hacklenir?")
            GLib.idle_add(self.log, "  1. Shodan/Censys ile asil IP'yi bul (Cloudflare'i baypas et)")
            GLib.idle_add(self.log, "  2. DNS history ile eski IP'leri bul")
            GLib.idle_add(self.log, "  3. SSL certificate transparency log'larindan IP bul")
            GLib.idle_add(self.log, "  4. WAF kurallarini asmak icin bypass teknikleri dene")
            GLib.idle_add(self.log, "  5. Rate limiting yoksa brute-force dene")
        else:
            GLib.idle_add(self.log, "=== DEGERLENDIRME ===")
            GLib.idle_add(self.log, "  [-] WAF/Cloudflare yok - dogrudan saldiriya acik")
            GLib.idle_add(self.log, "  Nasil hacklenir?")
            GLib.idle_add(self.log, "  1. Dogrudan IP'ye saldiri (port tarama, exploit)")
            GLib.idle_add(self.log, "  2. SQL Injection / XSS dene")
            GLib.idle_add(self.log, "  3. Directory busting ile gizli sayfalari bul")
            GLib.idle_add(self.log, "  4. Rate limit yoksa brute-force baslat")

        if resp.status_code >= 400:
            GLib.idle_add(self.log, f"\n[!] HTTP {resp.status_code} - Sayfaya erisim engellendi")
            if resp.status_code == 403:
                GLib.idle_add(self.log, "    Site veya WAF tarafindan engelleniyor olabilirsiniz")
            elif resp.status_code == 429:
                GLib.idle_add(self.log, "    Rate limit'e takildiniz, cok fazla istek gonderdiniz")

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Analiz tamamlandi")
