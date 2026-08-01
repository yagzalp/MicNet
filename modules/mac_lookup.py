import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests


class MacLookupTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="MAC Adresi Sorgulama")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="MAC adresinin hangi ureticiye ait oldugunu sorgular. Agdaki cihazlari tanimak icin kullanilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="MAC Adresi")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="00:11:22:AA:BB:CC")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_lookup())
        hbox.pack_start(self.entry, False, False, 0)
        self.lookup_btn = Gtk.Button(label="Sorgula")
        self.lookup_btn.connect("clicked", lambda _: self.start_lookup())
        self.lookup_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.lookup_btn, False, False, 0)
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

    def start_lookup(self):
        mac = self.entry.get_text().strip()
        if not mac:
            self.status_label.set_text("MAC adresi girin")
            return
        if self.running:
            return
        self.running = True
        self.lookup_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Sorgulaniyor...")
        thread = threading.Thread(target=self.lookup, args=(mac,), daemon=True)
        thread.start()

    def lookup(self, mac):
        MAC_LOOKUP_URL = "https://api.macvendors.com/"
        try:
            clean = mac.replace(":", "").replace("-", "").replace(".", "")[:6]
            resp = requests.get(f"{MAC_LOOKUP_URL}{clean}", timeout=10)
            if resp.status_code == 200:
                vendor = resp.text.strip()
                GLib.idle_add(self.log, f"[+] MAC: {mac.upper()}")
                GLib.idle_add(self.log, f"[+] Uretici: {vendor}")
                GLib.idle_add(self.log, f"[+] OUI: {clean.upper()}")
                oui_url = f"https://ouilookup.com/oui/{clean}"
                GLib.idle_add(self.log, f"[+] Detay: {oui_url}")
            elif resp.status_code == 404:
                GLib.idle_add(self.log, f"[-] MAC: {mac.upper()}")
                GLib.idle_add(self.log, "[-] Uretici bulunamadi (OUI taninmiyor)")
            else:
                GLib.idle_add(self.log, f"[-] Hata: HTTP {resp.status_code}")

        except requests.exceptions.ConnectionError:
            GLib.idle_add(self.log, "[-] Baglanti kurulamadi (Internet yok mu?)")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_lookup)

    def finish_lookup(self):
        self.running = False
        self.lookup_btn.set_sensitive(True)
        self.status_label.set_text("Sorgu tamamlandi")
