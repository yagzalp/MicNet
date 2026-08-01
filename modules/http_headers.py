import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
from modules.http_utils import status_str


class HttpHeadersTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="HTTP Baslik & Cerez Analizi")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Sunucunun gonderdigi tum HTTP basliklarini, tarayici cerezlerinin guvenlik bayraklarini ve HTTP metodlarini inceler.")
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
        self.entry.set_size_request(350, 30)
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
        self.status_label.set_text("Isteniyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
        }

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, "")

        try:
            resp = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Baglanti kurulamadi: {e}")
            GLib.idle_add(self.finish_scan)
            return

        h = resp.headers
        GLib.idle_add(self.log, f"[+] Durum: {status_str(resp.status_code)}")
        GLib.idle_add(self.log, f"[+] Final URL: {resp.url}")
        GLib.idle_add(self.log, f"[+] HTTP Surumu: HTTP/{resp.raw.version / 10.0 if resp.raw and resp.raw.version else '?'}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== TUM BASLIKLAR ===")
        for k in h:
            GLib.idle_add(self.log, f"  {k}: {h[k]}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== GUYENLIK ANALIZI ===")
        checks = [
            ("Strict-Transport-Security", "HSTS", "HTTPS zorlamasi yok; SSL strip saldirisina acik"),
            ("Content-Security-Policy", "CSP", "CSP yok; XSS korunmasiz"),
            ("X-Frame-Options", "Clickjacking korumasi", "Clickjacking'e acik"),
            ("X-Content-Type-Options", "MIME Sniffing korumasi", "MIME sniffing saldirisina acik"),
            ("Referrer-Policy", "Referrer politikasi", "URL bilgisi harici sitelere sizabiliyor"),
            ("Permissions-Policy", "Permissions-Policy", "Tarayici API izinleri (kamera/mikrofon) kontrol edilmiyor"),
            ("X-XSS-Protection", "XSS filtreleme", "Eski tarayicilarda XSS filtresi yok"),
            ("Cross-Origin-Opener-Policy", "COOP", "COOP yok; tarayici karsi taraftan etkilesime acik"),
        ]
        mevcut = 0
        for key, name, risk in checks:
            val = h.get(key)
            if val:
                mevcut += 1
                GLib.idle_add(self.log, f"  [+] {name}: KORUMALI")
            else:
                GLib.idle_add(self.log, f"  [-] {name}: YOK -> {risk}")
        GLib.idle_add(self.log, f"\n  [*] {mevcut}/{len(checks)} guvenlik basligi mevcut")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== COZENLER (COOKIES) ===")
        if resp.cookies:
            for c in resp.cookies:
                flags = []
                if c.secure:
                    flags.append("Secure")
                if c.has_nonstandard_attr("HttpOnly"):
                    flags.append("HttpOnly")
                if c.domain:
                    flags.append("Domain=" + c.domain)
                if c.path:
                    flags.append("Path=" + c.path)
                if c.expires:
                    flags.append("Expires=" + str(c.expires))
                risk = ""
                if "HttpOnly" not in flags:
                    risk = " [!] HttpOnly YOK - JS ile erisilebilir (XSS riski)"
                if "Secure" not in flags:
                    risk += " [!] Secure YOK - HTTP uzerinden gonderilebilir"
                GLib.idle_add(self.log, f"  [{c.name}] = {c.value[:40]}")
                GLib.idle_add(self.log, f"      Bayraklar: {', '.join(flags) if flags else 'yok'}{risk}")
        else:
            GLib.idle_add(self.log, "  [*] Cerez gonderilmedi")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== HTTP METODLARI ===")
        methods = ["OPTIONS", "TRACE", "PUT", "DELETE", "PATCH"]
        for m in methods:
            try:
                r = requests.request(m, url, timeout=8, headers=headers)
                GLib.idle_add(self.log, f"  {m}: {r.status_code} ({status_str(r.status_code)})")
                if m == "TRACE" and r.status_code == 200 and "TRACE" in r.text:
                    GLib.idle_add(self.log, "      [!] TRACE etkin - Cross-Site Tracing (XST) riski")
                if m == "OPTIONS" and r.status_code in (200, 204):
                    allow = r.headers.get("Allow", "")
                    GLib.idle_add(self.log, f"      Allow: {allow}")
            except Exception as e:
                GLib.idle_add(self.log, f"  {m}: hata ({e})")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== TAVSIYELER ===")
        missing = [k for k, _, _ in checks if not h.get(k)]
        if missing:
            GLib.idle_add(self.log, "  Asagidaki basliklar eklenmeli:")
            for k in missing:
                GLib.idle_add(self.log, f"    - {k}")
        else:
            GLib.idle_add(self.log, "  [*] Temel basliklar tamam")

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Analiz tamamlandi")
