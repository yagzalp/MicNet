import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import dns.resolver
import dns.zone
import dns.query
import dns.rdatatype


class DnsZoneTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="DNS Kayitlari & Zone Transfer")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Domain'in tum DNS kayitlarini (A, AAAA, MX, NS, TXT, SOA, CNAME) cozer ve name server'lar uzerinde zone transfer (AXFR) acigi testi yapar.")
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
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)

        self.axfr_check = Gtk.CheckButton(label="Zone transfer (AXFR) test et")
        self.axfr_check.set_active(True)
        hbox.pack_start(self.axfr_check, False, False, 0)

        self.scan_btn = Gtk.Button(label="Sorgula")
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
        domain = self.entry.get_text().strip()
        if not domain:
            self.status_label.set_text("Domain girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Sorgulaniyor...")
        do_axfr = self.axfr_check.get_active()
        thread = threading.Thread(target=self.scan, args=(domain, do_axfr), daemon=True)
        thread.start()

    def _query(self, rtype, domain):
        try:
            answers = dns.resolver.resolve(domain, rtype, lifetime=8)
            return [a.to_text() for a in answers]
        except dns.resolver.NoAnswer:
            return []
        except Exception:
            return None

    def scan(self, domain, do_axfr):
        domain = domain.strip().lower()
        if not domain.endswith("."):
            domain = domain + "."

        GLib.idle_add(self.log, f"[*] Hedef: {domain}")
        GLib.idle_add(self.log, "")

        for rtype, name in [(dns.rdatatype.A, "A"), (dns.rdatatype.AAAA, "AAAA"),
                            (dns.rdatatype.CNAME, "CNAME"), (dns.rdatatype.MX, "MX"),
                            (dns.rdatatype.NS, "NS"), (dns.rdatatype.TXT, "TXT"),
                            (dns.rdatatype.SOA, "SOA")]:
            res = self._query(rtype, domain)
            GLib.idle_add(self.log, f"--- {name} KAYITLARI ---")
            if res is None:
                GLib.idle_add(self.log, "  [*] Sorgu hatasi/zaman asimi")
            elif not res:
                GLib.idle_add(self.log, "  [-] Kayit yok")
            else:
                for r in res:
                    GLib.idle_add(self.log, f"  [+] {r}")
            GLib.idle_add(self.log, "")

        if do_axfr:
            GLib.idle_add(self.log, "=== ZONE TRANSFER (AXFR) TESTI ===")
            ns_list = self._query(dns.rdatatype.NS, domain)
            if not ns_list:
                GLib.idle_add(self.log, "  [-] NS kaydi bulunamadi, AXFR testi atlandi")
            else:
                GLib.idle_add(self.log, f"  [*] {len(ns_list)} name server bulundu, deneniyor...")
                for ns in ns_list:
                    ns_host = ns.rstrip(".")
                    try:
                        ip = dns.resolver.resolve(ns_host, "A", lifetime=8)[0].to_text()
                    except Exception:
                        ip = ns_host
                    try:
                        z = dns.zone.from_xfr(dns.query.xfr(ip, domain, timeout=8))
                        names = list(z.nodes.keys())
                        GLib.idle_add(self.log, f"  [!] ACIK: {ns} ({ip}) zone transfer yapti!")
                        GLib.idle_add(self.log, f"      {len(names)} kayit cekildi")
                        for n in names[:50]:
                            GLib.idle_add(self.log, f"        - {n}")
                        if len(names) > 50:
                            GLib.idle_add(self.log, f"        ... ve {len(names)-50} daha")
                    except Exception as e:
                        GLib.idle_add(self.log, f"  [-] {ns} ({ip}): kapali ({str(e)[:60]})")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== DEGERLENDIRME ===")
        GLib.idle_add(self.log, "  [*] Zone transfer acigi: saldirgan tum kayitlari (admin panelleri dahil) cekebilir")
        GLib.idle_add(self.log, "  [*] Guvenli DNS: AXFR sadece yetkili sunuculara sinirlandirilmali")

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Sorgu tamamlandi")
