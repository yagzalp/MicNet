import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import dns.resolver
import dns.reversename


class DnsLookupTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="DNS Kayit Sorgulama")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Domain adlarinin DNS kayitlarini sorgular. A, MX, NS, TXT, SOA, CNAME ve PTR kayitlarini gosterir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Sorgu Ayarlari")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)

        self.entry = Gtk.Entry(placeholder_text="ornek.com")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_lookup())
        hbox.pack_start(self.entry, False, False, 0)

        self.record_combo = Gtk.ComboBoxText()
        for rec in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "PTR (IP ile)", "TUMU"]:
            self.record_combo.append(rec.lower().replace(" ", "_"), rec)
        self.record_combo.set_active(0)
        hbox.pack_start(self.record_combo, False, False, 0)

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

    def log(self, text, newline=True):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + ("\n" if newline else ""))

    def start_lookup(self):
        query = self.entry.get_text().strip()
        if not query:
            self.status_label.set_text("Domain veya IP girin")
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
        record = self.record_combo.get_active_id()
        if record == "ptr_(ip_ile)":
            self.query_ptr(query)
        elif record == "tumu":
            self.query_all(query)
        else:
            self.query_single(query, record.upper())
        GLib.idle_add(self.finish_lookup)

    def resolve(self, qname, rtype):
        try:
            answers = dns.resolver.resolve(qname, rtype)
            return [str(a) for a in answers]
        except dns.resolver.NoAnswer:
            return None
        except dns.resolver.NXDOMAIN:
            return []
        except Exception:
            return None

    def query_single(self, query, rtype):
        self.log(f"=== {rtype} Kaydi: {query} ===")
        results = self.resolve(query, rtype)
        if results is None:
            self.log("  Hata: Sorgu basarisiz")
        elif not results:
            self.log("  Kayit bulunamadi")
        else:
            for r in results:
                self.log(f"  {r}")

    def query_ptr(self, ip):
        self.log(f"=== PTR (Ters DNS): {ip} ===")
        try:
            n = dns.reversename.from_address(ip)
            answers = dns.resolver.resolve(n, "PTR")
            for a in answers:
                self.log(f"  {a}")
        except Exception as e:
            self.log(f"  Hata: {e}")

    def query_all(self, domain):
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
            GLib.idle_add(self.log, f"\n=== {rtype} ===")
            results = self.resolve(domain, rtype)
            if results is None:
                GLib.idle_add(self.log, "  Hata / kayit yok")
            elif not results:
                GLib.idle_add(self.log, "  Bulunamadi")
            else:
                for r in results:
                    GLib.idle_add(self.log, f"  {r}")

    def finish_lookup(self):
        self.running = False
        self.lookup_btn.set_sensitive(True)
        self.status_label.set_text("Sorgu tamamlandi")
