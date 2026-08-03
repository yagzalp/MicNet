import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import re
import requests

TECH_MARKERS = [
    ("WordPress", r"wp-content|wp-includes|/wp-json/", None),
    ("Joomla", r"/media/system/|com_content", None),
    ("Drupal", r"/sites/default/files|Drupal.settings|drupal", None),
    ("Magento", r"Magento|mage/|/skin/frontend/", None),
    ("Shopify", r"cdn\.shopify\.com|myshopify\.com", None),
    ("Wix", r"wix\.com", None),
    ("Blogger", r"blogspot\.com", None),
    ("Bootstrap", r"bootstrap", None),
    ("jQuery", r"jquery", None),
    ("React", r"react", None),
    ("Vue.js", r"vue\.js|__vue__", None),
    ("Angular", r"ng-version|angular", None),
    ("Laravel", r"laravel_session", "cookie"),
    ("Django", r"csrftoken|django", "cookie"),
    ("Flask", r"flask", "header"),
    ("PHP", r"PHPSESSID", "cookie"),
    ("ASP.NET", r"ASP\.NET_SessionId|__VIEWSTATE", "cookie"),
    ("Java/JSP", r"JSESSIONID", "cookie"),
    ("Tomcat", r"Apache-Coyote", "header"),
    ("Nginx", r"nginx", "header"),
    ("Apache", r"apache", "header"),
    ("IIS", r"Microsoft-IIS", "header"),
    ("Cloudflare", r"cloudflare", "header"),
    ("Akamai", r"akamai", "header"),
    ("Varnish", r"varnish", "header"),
    ("Vercel", r"vercel", "header"),
]


class TechDetectTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Web Teknoloji Tespiti")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef sitenin kullandigi teknolojileri tespit eder: sunucu, isletim sistemi, CMS, programlama dili ve CDN. HTTP basliklari, cerezler ve sayfa iceriginden izler cikarir.")
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
        self.scan_btn = Gtk.Button(label="Tespit Et")
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
        self.status_label.set_text("Tespit ediliyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        try:
            r = requests.get(url, timeout=10, verify=False, allow_redirects=True)
            headers = {k.lower(): v for k, v in r.headers.items()}
            cookies = "; ".join(f"{c.name}={c.value}" for c in r.cookies)
            body = r.text[:200000]
            GLib.idle_add(self.log, f"[*] Hedef: {url}")
            GLib.idle_add(self.log, f"[*] Durum: {r.status_code} | Boyut: {len(body)} byte\n")

            found = []
            for tech, marker, source in TECH_MARKERS:
                hay = ""
                if source == "cookie":
                    hay = cookies
                elif source == "header":
                    hay = " ".join(headers.values())
                else:
                    hay = body + " " + " ".join(headers.values()) + " " + cookies
                if re.search(marker, hay, re.IGNORECASE):
                    found.append(tech)

            GLib.idle_add(self.log, "=== TESPIT EDILEN TEKNOLOJILER ===")
            if found:
                for t in sorted(set(found)):
                    GLib.idle_add(self.log, f"  [+] {t}")
            else:
                GLib.idle_add(self.log, "  [-] Bilinen teknoloji tespit edilemedi")

            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, "=== ONEMLI BASLIKLAR ===")
            for h in ["server", "x-powered-by", "x-generator", "x-aspnet-version", "x-aspnet-mvc-version", "x-drupal-cache", "x-magento-cache-control", "via"]:
                if h in headers:
                    GLib.idle_add(self.log, f"  {h}: {headers[h]}")
            if cookies:
                GLib.idle_add(self.log, f"  Cerezler: {cookies[:200]}")
        except requests.exceptions.SSLError:
            GLib.idle_add(self.log, "[-] SSL hatasi")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tespit tamamlandi")
