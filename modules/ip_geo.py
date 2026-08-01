import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import json


class IpGeoTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="IP / Domain Konum Bulma")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="IP adresi veya domainin fiziksel konumunu tespit eder. Ulke, sehir, ISP ve harita bilgisi verir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="IP adresi veya domain")
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
        query = self.entry.get_text().strip()
        if not query:
            self.status_label.set_text("IP veya domain girin")
            return
        if self.running:
            return
        self.running = True
        self.lookup_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Sorgulaniyor...")
        thread = threading.Thread(target=self.lookup, args=(query,), daemon=True)
        thread.start()

    def lookup(self, query):
        try:
            import requests
            ip = query
            if not query.replace(".", "").isdigit():
                ip = socket.gethostbyname(query)
                GLib.idle_add(self.log, f"[+] Domain: {query}")
                GLib.idle_add(self.log, f"[+] Cozulen IP: {ip}")

            GLib.idle_add(self.log, f"\n[*] Konum bilgisi aliniyor...\n")
            resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = resp.json()

            if data.get("status") == "success":
                fields = [
                    ("Ulke", "country"),
                    ("Ulke Kodu", "countryCode"),
                    ("Bolge", "regionName"),
                    ("Sehir", "city"),
                    ("Ilce", "district"),
                    ("Posta Kodu", "zip"),
                    ("Enlem", "lat"),
                    ("Boylam", "lon"),
                    ("Saat Dilimi", "timezone"),
                    ("ISP", "isp"),
                    ("Organizasyon", "org"),
                    ("AS Numarasi", "as"),
                ]
                for label, key in fields:
                    val = data.get(key)
                    if val:
                        emoji = " [+]"
                        GLib.idle_add(self.log, f"{emoji} {label}: {val}")

                maps_url = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
                GLib.idle_add(self.log, f"\n    Harita: {maps_url}")
            else:
                GLib.idle_add(self.log, f"[-] Bilgi alinamadi: {data.get('message', '?')}")

        except socket.gaierror:
            GLib.idle_add(self.log, "[-] Domain cozulemedi")
        except ImportError:
            GLib.idle_add(self.log, "[-] requests paketi gerekli")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_lookup)

    def finish_lookup(self):
        self.running = False
        self.lookup_btn.set_sensitive(True)
        self.status_label.set_text("Sorgu tamamlandi")
