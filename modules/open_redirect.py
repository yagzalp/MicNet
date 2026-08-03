import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
from urllib.parse import quote

REDIRECT_PARAMS = ["url", "redirect", "next", "return", "return_url", "target", "out", "goto", "rurl", "dest", "redirect_url"]
MARKER = "https://example.com/"


class OpenRedirectTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Open Redirect Tarayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef sitede acik yonlendirme (open redirect) acigi arar. Yaygin yonlendirme parametrelerine harici bir isaretci domain enjekte edilir ve yanit kontrol edilir.")
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
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com/giris.php")
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
        for param in REDIRECT_PARAMS:
            sep = "&" if "?" in base_url else "?"
            test_url = f"{base_url}{sep}{param}={quote(MARKER)}"
            try:
                r = requests.get(test_url, timeout=8, verify=False, allow_redirects=False)
                location = r.headers.get("Location", "")
                final = r.url if r.url else ""
                if MARKER in location or MARKER in final:
                    found += 1
                    GLib.idle_add(self.log, f"[!] ACIL YONLENDIRME: ?{param} -> {location[:80]}")
                elif location:
                    GLib.idle_add(self.log, f"[-] ?{param} -> {location[:60]} (harici degil)")
                else:
                    GLib.idle_add(self.log, f"[-] ?{param} -> yonlendirme yok (HTTP {r.status_code})")
            except requests.exceptions.SSLError:
                GLib.idle_add(self.log, f"[-] SSL hatasi: {test_url[:80]}")
            except Exception as e:
                GLib.idle_add(self.log, f"[-] ?{param} hata: {e}")
        if found == 0:
            GLib.idle_add(self.log, "[-] Yonlendirme parametrelerinde acik bulunamadi.")
        else:
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, f"[!] {found} ACIL YONLENDIRME BULUNDU")
            GLib.idle_add(self.log, "    Bu acik bir saldirganin su islemleri yapmasina izin verir:")
            GLib.idle_add(self.log, "    - Saghte baglanti (kimlik avi): guvenilir siteymis gibi gorunen")
            GLib.idle_add(self.log, "      baglantiyla kurbani zararli siteye yonlendirir")
            GLib.idle_add(self.log, "    - OAuth/oturum belirtecini (token) calar")
            GLib.idle_add(self.log, "    - Malware barindiran siteye yonlendirme")
            GLib.idle_add(self.log, "    Korunma: Yonlendirme parametrelerini allow-list ile dogrulayin,")
            GLib.idle_add(self.log, "            sadece kendi domaininize izin verin.")
        GLib.idle_add(self.finish_scan, found)

    def finish_scan(self, found):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text(f"Tarama tamamlandi - {found} acik yonlendirme")
