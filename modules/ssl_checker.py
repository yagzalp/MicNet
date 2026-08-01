import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import ssl
from datetime import datetime


class SslCheckerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="SSL/TLS Sertifika Analizi")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef sunucunun SSL/TLS sertifikasini inceler: gecerlilik suresi, veren kurum, SAN alanlari, desteklenen protokol ve sifreleme bilgileri.")
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
        self.entry = Gtk.Entry(placeholder_text="ornek.com")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)

        self.port_spin = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.port_spin.set_value(443)
        hbox.pack_start(self.port_spin, False, False, 0)

        self.scan_btn = Gtk.Button(label="Analiz Et")
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
        host = self.entry.get_text().strip()
        if not host:
            self.status_label.set_text("Hedef girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Baglaniyor...")
        port = int(self.port_spin.get_value())
        thread = threading.Thread(target=self.scan, args=(host, port), daemon=True)
        thread.start()

    def _connect(self, host, port, min_ver, max_ver):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = min_ver
        ctx.maximum_version = max_ver
        sock = socket.create_connection((host, port), timeout=8)
        ssock = ctx.wrap_socket(sock, server_hostname=host)
        return ssock

    def scan(self, host, port):
        host = host.rstrip("/")
        if "://" in host:
            host = host.split("://", 1)[1]

        GLib.idle_add(self.log, f"[*] Hedef: {host}:{port}")
        GLib.idle_add(self.log, "")

        ssock = None
        try:
            ssock = self._connect(host, port, ssl.TLSVersion.MINIMUM_SUPPORTED, ssl.TLSVersion.MAXIMUM_SUPPORTED)
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Baglanti kurulamadi: {e}")
            GLib.idle_add(self.finish_scan)
            return

        try:
            cert = ssock.getpeercert()
            proto = ssock.version()
            cipher = ssock.cipher()
            ssock.close()
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Sertifika okunamadi: {e}")
            GLib.idle_add(self.finish_scan)
            return

        GLib.idle_add(self.log, "=== BAGLANTI BILGILERI ===")
        GLib.idle_add(self.log, f"  [+] Protokol: {proto}")
        GLib.idle_add(self.log, f"  [+] Sifre (cipher): {cipher[0]} | {cipher[1]} bit")

        if not cert:
            GLib.idle_add(self.log, "  [-] Sertifika bulunamadi (muhtemelen kendinden imzali/gecersiz)")
        else:
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, "=== SERTIFIKA BILGILERI ===")

            def get_subject(field):
                try:
                    for t in cert.get("subject", ()):
                        if t[0][0] == field:
                            return t[0][1]
                except Exception:
                    pass
                return None

            cn = get_subject("commonName")
            org = get_subject("organizationName")
            country = get_subject("countryName")

            GLib.idle_add(self.log, f"  [+] Ortak Ad (CN): {cn or '?'}")
            GLib.idle_add(self.log, f"  [+] Kurulus: {org or '?'}")
            GLib.idle_add(self.log, f"  [+] Ulke: {country or '?'}")

            issuer = cert.get("issuer")
            issuer_cn = None
            if issuer:
                try:
                    for t in issuer:
                        if t[0][0] == "commonName":
                            issuer_cn = t[0][1]
                except Exception:
                    pass
            GLib.idle_add(self.log, f"  [+] Veren (Issuer): {issuer_cn or '?'}")

            try:
                not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
                not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                now = datetime.utcnow()
                total = (not_after - not_before).days
                kalan = (not_after - now).days

                GLib.idle_add(self.log, f"  [+] Gecerli: {not_before.strftime('%Y-%m-%d')} -> {not_after.strftime('%Y-%m-%d')}")
                GLib.idle_add(self.log, f"  [+] Toplam gecerlilik: {total} gun")
                if kalan < 0:
                    GLib.idle_add(self.log, f"  [-] SON KULLANMA TARIHI GECTI ({-kalan} gun once)")
                elif kalan < 30:
                    GLib.idle_add(self.log, f"  [!] UYARI: {kalan} gun sonra sifresi dolacak")
                else:
                    GLib.idle_add(self.log, f"  [+] Kalan sure: {kalan} gun")
            except Exception:
                pass

            sans = []
            try:
                for entry in cert.get("subjectAltName", ()):
                    sans.append(entry[1])
            except Exception:
                pass
            if sans:
                GLib.idle_add(self.log, f"  [+] SAN alanlari ({len(sans)}):")
                for s in sans[:20]:
                    GLib.idle_add(self.log, f"      - {s}")
                if len(sans) > 20:
                    GLib.idle_add(self.log, f"      ... ve {len(sans)-20} tane daha")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== PROTOKOL TESTLERI ===")
        test_list = [
            ("TLS 1.3", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3),
            ("TLS 1.2", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2),
            ("TLS 1.1", ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1),
            ("TLS 1.0", ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1),
        ]
        for name, mn, mx in test_list:
            try:
                s2 = self._connect(host, port, mn, mx)
                s2.close()
                GLib.idle_add(self.log, f"  [+] {name}: DESTEKLENIYOR")
            except Exception:
                GLib.idle_add(self.log, f"  [-] {name}: desteklenmiyor")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== DEGERLENDIRME ===")
        if proto == "TLSv1.3":
            GLib.idle_add(self.log, "  [+] Guncel ve guvenli protokol kullaniyor")
        elif proto == "TLSv1.2":
            GLib.idle_add(self.log, "  [+] Kabul edilebilir protokol (TLS 1.2+)")
        else:
            GLib.idle_add(self.log, "  [-] ESKI protokol - TLS 1.2/1.3'e yukseltilmeli")
        GLib.idle_add(self.log, "  [*] Guvenli HTTPS icin HSTS de ayarlanmali (Headers sekmesine bak)")

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Analiz tamamlandi")
