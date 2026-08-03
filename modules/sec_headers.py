import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests

HEADERS = [
    ("Strict-Transport-Security", "HSTS - siteyi yalniz HTTPS uzerinden calistirir. Eksikse MITM/saldiri riski.", "yuksek"),
    ("Content-Security-Policy", "CSP - XSS ve veri calma saldirilarini sinirlar. Eksikse XSS riski artar.", "yuksek"),
    ("X-Frame-Options", "Clickjacking korumasi. Eksikse sayfa iframe icinde gizlenebilir.", "yuksek"),
    ("X-Content-Type-Options", "MIME-sniffing korumasi (nosniff). Eksikse kotu niyetli dosya yorumlamasi riski.", "orta"),
    ("Referrer-Policy", "Referrer bilgisinin ne kadar sizdirilacagini kontrol eder.", "orta"),
    ("Permissions-Policy", "Tarayici ozelliklerini (kamera, GPS) sayfa bazinda sinirlar.", "dusuk"),
    ("X-XSS-Protection", "Eski tarayicilarda XSS filtresi (modern tarayicilarda CSP onerilir).", "dusuk"),
]


class SecHeadersTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="GUVENLIK BASLIK DENETIMI")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef sitenin HTTP guvenlik basliklarini denetler: HSTS, CSP, X-Frame-Options ve cerez bayraklari. Eksik basliklar ve risk seviyeleri listelenir.")
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
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com")
        self.entry.set_size_request(340, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Denetle")
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
            self.status_label.set_text("URL http/https ile baslamali")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Denetleniyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        try:
            r = requests.get(url, timeout=10, verify=False, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            headers = {k.lower(): v for k, v in r.headers.items()}

            GLib.idle_add(self.log, f"[*] Hedef: {url}")
            GLib.idle_add(self.log, f"[*] HTTP {r.status_code}\n")
            GLib.idle_add(self.log, "=== GUVENLIK BASLIKLARI ===")

            missing_critical = 0
            for name, note, sev in HEADERS:
                key = name.lower()
                if key in headers:
                    val = headers[key][:120]
                    GLib.idle_add(self.log, f"  [OK]  {name}")
                    GLib.idle_add(self.log, f"         -> {val}")
                else:
                    missing_critical += 1 if sev == "yuksek" else 0
                    GLib.idle_add(self.log, f"  [YOK] {name}   (onem: {sev.upper()})")
                    GLib.idle_add(self.log, f"         {note}")

            GLib.idle_add(self.log, "\n=== CEREZ BAYRAKLARI ===")
            set_cookies = r.raw.headers.get_all("Set-Cookie") if hasattr(r.raw.headers, "get_all") else None
            cookies = set_cookies or []
            if r.headers.get("Set-Cookie"):
                pass
            if not cookies:
                sc = r.raw.headers.get_list("Set-Cookie") if hasattr(r.raw.headers, "get_list") else []
                cookies = sc
            if cookies:
                for c in cookies:
                    http_only = "HttpOnly" in c
                    secure = "Secure" in c
                    flags = []
                    if http_only:
                        flags.append("HttpOnly")
                    if secure:
                        flags.append("Secure")
                    flag_str = ", ".join(flags) if flags else "ONEMLI BAYRAK YOK (JS erisebilir, HTTP uzerinden gidebilir)"
                    GLib.idle_add(self.log, f"  {c.split(';')[0]} -> {flag_str}")
            else:
                GLib.idle_add(self.log, "  [-] Cerez ayarlanmamis")

            GLib.idle_add(self.log, "\n=== OZET ===")
            if missing_critical:
                GLib.idle_add(self.log, f"  [!] {missing_critical} kritik baslik eksik - tarayici korumalari zayif.")
            else:
                GLib.idle_add(self.log, "  [+] Kritik guvenlik basliklari mevcut.")
            GLib.idle_add(self.log, "\n[*] Ipucu: eksik basliklar sunucu/uygulama ayarlarindan eklenmelidir (nginx.conf, web.config, .htaccess).")
        except requests.exceptions.SSLError:
            GLib.idle_add(self.log, "[-] SSL hatasi")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Denetim tamamlandi")
