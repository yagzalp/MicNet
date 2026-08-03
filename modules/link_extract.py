import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import re
import requests
from urllib.parse import urljoin, urlparse


class LinkExtractTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Baglanti Toplayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Sayfadaki tum linkleri ve kaynaklari toplar: href, src, script, stil ve form adresleri. Dahili ve harici linkler ayri listelenir. (osint/adim-1 taramasi)")
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
        self.scan_btn = Gtk.Button(label="Topla")
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
        self.status_label.set_text("Toplaniyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        try:
            r = requests.get(url, timeout=10, verify=False, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            body = r.text
            base = r.url
            parsed = urlparse(base)
            domain = parsed.netloc

            links = set()
            for m in re.finditer(r'(?:href|src|action|data-src)\s*=\s*["\']([^"\']+)["\']', body, re.IGNORECASE):
                raw = m.group(1).strip()
                if not raw or raw.startswith(("#", "mailto:", "javascript:", "tel:", "data:")):
                    continue
                full = urljoin(base, raw)
                links.add(full)

            internal = sorted(l for l in links if urlparse(l).netloc == domain)
            external = sorted(l for l in links if urlparse(l).netloc != domain)

            GLib.idle_add(self.log, f"[*] Hedef: {url}")
            GLib.idle_add(self.log, f"[*] Toplam {len(links)} benzersiz link bulundu\n")
            GLib.idle_add(self.log, f"=== DAHILI LINKLER ({len(internal)}) ===")
            for l in internal[:120]:
                GLib.idle_add(self.log, f"  {l}")
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, f"=== HARICI LINKLER ({len(external)}) ===")
            for l in external[:120]:
                GLib.idle_add(self.log, f"  {l}")

            if len(internal) > 120 or len(external) > 120:
                GLib.idle_add(self.log, f"\n[!] Sonuc buyuk oldugu icin ilk 120'de kesildi.")
        except requests.exceptions.SSLError:
            GLib.idle_add(self.log, "[-] SSL hatasi")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Toplama tamamlandi")
