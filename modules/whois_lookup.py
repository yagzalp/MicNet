import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading


class WhoisTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="WHOIS Sorgulama")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Domain kayit bilgilerini sorgular. Domain sahibi, kayit tarihi ve sunucu bilgilerini gosterir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Domain")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek.com")
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
        domain = self.entry.get_text().strip()
        if not domain:
            self.status_label.set_text("Domain girin")
            return
        if self.running:
            return
        self.running = True
        self.lookup_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Sorgulaniyor...")
        thread = threading.Thread(target=self.lookup, args=(domain,), daemon=True)
        thread.start()

    def lookup(self, domain):
        try:
            import whois
            w = whois.whois(domain)
            fields = [
                ("Domain", "domain_name"),
                ("Kayit Tarihi", "creation_date"),
                ("Son Guncelleme", "updated_date"),
                ("Son Kullanma", "expiration_date"),
                ("Kayitci", "registrar"),
                ("WHOIS Sunucu", "whois_server"),
                ("Durum", "status"),
                ("DNS Sunuculari", "name_servers"),
                ("Sahip", "org"),
                ("Ulke", "country"),
                ("E-posta", "emails"),
            ]
            for label, key in fields:
                val = w.get(key)
                if val:
                    if isinstance(val, list):
                        val = ", ".join(str(v) for v in val[:3])
                        if len(w.get(key, [])) > 3:
                            val += f" (ve {len(w.get(key)) - 3} daha)"
                    GLib.idle_add(self.log, f"{label}: {val}")

            if not w.get("domain_name"):
                GLib.idle_add(self.log, "[-] WHOIS bilgisi bulunamadi")
        except ImportError:
            GLib.idle_add(self.log, "[-] python-whois paketi yuklu degil")
            GLib.idle_add(self.log, "    Yuklemek icin: pip install python-whois")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_lookup)

    def finish_lookup(self):
        self.running = False
        self.lookup_btn.set_sensitive(True)
        self.status_label.set_text("Sorgu tamamlandi")
