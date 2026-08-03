import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests

EVIL_ORIGIN = "https://evil.example.com"
TEST_PATHS = ["/", "/api", "/api/v1", "/api/user", "/api/config", "/login"]


class CorsScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="CORS Tarayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="CORS yanlis yapilandirmasini test eder. Sitenin Access-Control-Allow-Origin basligina saldirgan kokeni (Origin) yansitip yansitmadigini kontrol eder. Yanlis yapilandirilmis CORS, kullanici verilerinin baska sitece cekilmesine yol acar.")
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
        url = self.entry.get_text().strip().rstrip("/")
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

    def scan(self, url):
        try:
            GLib.idle_add(self.log, f"[*] Hedef: {url}")
            GLib.idle_add(self.log, f"[*] Deneme kokeni (Origin): {EVIL_ORIGIN}\n")
            GLib.idle_add(self.log, "=== CORS YANITLARI ===")
            found = False
            for path in TEST_PATHS:
                target = url + path
                try:
                    r = requests.get(target, timeout=10, verify=False, headers={"Origin": EVIL_ORIGIN, "User-Agent": "Mozilla/5.0"})
                    acao = r.headers.get("Access-Control-Allow-Origin")
                    acac = r.headers.get("Access-Control-Allow-Credentials")
                    if acao and EVIL_ORIGIN in acao:
                        found = True
                        GLib.idle_add(self.log, f"  [ZAFIYET!] {path} (HTTP {r.status_code})")
                        GLib.idle_add(self.log, f"    ACAO: {acao}")
                        GLib.idle_add(self.log, f"    ACAC: {acac or 'yok'}")
                        if acac and acac.lower() == "true":
                            GLib.idle_add(self.log, "    [!] Credentials'li CORS! Kimlik dogrulamasiyla veri cekilebilir.")
                        else:
                            GLib.idle_add(self.log, "    [i] Credentials yok ama koken yansitiliyor.")
                        GLib.idle_add(self.log, "")
                    elif acao == "*":
                        if acac and acac.lower() == "true":
                            found = True
                            GLib.idle_add(self.log, f"  [ZAFIYET!] {path}: ACAO=* ILE credentials'a izin veriliyor (tarayicida engellenir ama acik) ")
                        else:
                            GLib.idle_add(self.log, f"  [OK] {path}: ACAO=* (kimlik bilgisi yok, dusuk risk)")
                    else:
                        GLib.idle_add(self.log, f"  [-] {path} (HTTP {r.status_code}): koken yansitilmadi")
                except Exception as e:
                    GLib.idle_add(self.log, f"  [-] {path}: {type(e).__name__}")

            GLib.idle_add(self.log, "\n=== SONUC ===")
            if found:
                GLib.idle_add(self.log, "  [!] CORS yanlis yapilandirmasi tespit edildi!")
                GLib.idle_add(self.log, "  Saldirganin yapabilecekleri:")
                GLib.idle_add(self.log, "  - Kurban tarayicisini zararli siteye sokup hedef siteye istek attirabilir")
                GLib.idle_add(self.log, "  - Kimlik bilgileriyle korunan verileri (profil, API yaniti) okuyabilir")
                GLib.idle_add(self.log, "  - Oturum yonetimli islemler (islem/banka) tetikleyebilir")
                GLib.idle_add(self.log, "  Cozum: koken beyaz listesi kullanin; 'Origin' yansitmayin; ACAO'yu sabit domainlere set edin.")
            else:
                GLib.idle_add(self.log, "  [-] CORS yanlis yapilandirmasi bulunamadi.")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
