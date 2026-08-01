import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
from datetime import datetime
from modules.http_utils import status_str, port_str


class PortScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Port Scanner")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef bir IP veya domaindeki acik portlari tarar. Hangi servislerin calistigini ve potansiyel guvenlik aciklarini tespit eder.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef ve Ayarlar")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)

        self.entry = Gtk.Entry(placeholder_text="hedef.com veya IP")
        self.entry.set_size_request(200, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)

        self.port_range_combo = Gtk.ComboBoxText()
        self.port_range_combo.append("common", "Yaygin (1-1024)")
        self.port_range_combo.append("top50", "Top 50")
        self.port_range_combo.append("top100", "Top 100")
        self.port_range_combo.append("full", "Tum (1-65535)")
        self.port_range_combo.set_active(0)
        hbox.pack_start(self.port_range_combo, False, False, 0)

        self.scan_btn = Gtk.Button(label="Tara")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)

        self.cancel_btn = Gtk.Button(label="Iptal")
        self.cancel_btn.set_sensitive(False)
        self.cancel_btn.connect("clicked", lambda _: self.cancel_scan())
        hbox.pack_start(self.cancel_btn, False, False, 0)
        input_box.pack_start(hbox, False, False, 0)

        frame.add(input_box)
        self.pack_start(frame, False, False, 0)

        self.liststore = Gtk.ListStore(str, str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)

        cols = [("Port", 0), ("Durum", 1), ("Servis", 2), ("Aciklama", 3)]
        for title_text, idx in cols:
            col = Gtk.TreeViewColumn(title_text, Gtk.CellRendererText(), text=idx)
            col.set_resizable(True)
            col.set_sort_column_id(idx)
            self.treeview.append_column(col)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.treeview)
        self.pack_start(sw, True, True, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

        self.running = False

        self.common_ports = {
            21: ("FTP", "Dosya Transferi - guvenli degil"),
            22: ("SSH", "Guvenli Shell"),
            23: ("Telnet", "Guvenli olmayan uzaktan erisim"),
            25: ("SMTP", "E-posta gonderimi"),
            53: ("DNS", "Domain Name System"),
            80: ("HTTP", "Web sunucusu - sifresiz"),
            110: ("POP3", "E-posta alma - guvenli degil"),
            143: ("IMAP", "E-posta alma - sifresiz"),
            443: ("HTTPS", "Guvenli web sunucusu"),
            445: ("SMB", "Windows dosya paylasimi"),
            993: ("IMAPS", "Guvenli IMAP"),
            995: ("POP3S", "Guvenli POP3"),
            1433: ("MSSQL", "Microsoft SQL Server"),
            1521: ("Oracle", "Oracle Database"),
            2049: ("NFS", "Network File System"),
            3306: ("MySQL", "MySQL veritabani"),
            3389: ("RDP", "Uzak Masaustu Protokolu"),
            5432: ("PostgreSQL", "PostgreSQL veritabani"),
            5900: ("VNC", "Sanal Ag Bilgisayari"),
            6379: ("Redis", "Redis veritabani"),
            8080: ("HTTP-Proxy", "Alternatif HTTP portu"),
            8443: ("HTTPS-Alt", "Alternatif HTTPS portu"),
            27017: ("MongoDB", "MongoDB veritabani"),
        }

        self.top_50 = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993,
                       995, 1433, 1521, 2049, 3306, 3389, 5432, 5900, 5985, 5986, 6379,
                       8080, 8443, 9000, 9090, 27017, 20, 69, 79, 161, 162, 389, 636,
                       873, 993, 995, 1723, 1883, 2375, 2376, 3128, 3268, 3269, 4848,
                       5672, 9200]

    def start_scan(self):
        host = self.entry.get_text().strip()
        if not host:
            self.status_label.set_text("Hedef girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.cancel_btn.set_sensitive(True)
        self.liststore.clear()
        self.status_label.set_text("Taranıyor...")

        mode = self.port_range_combo.get_active_id()
        if mode == "top50":
            ports = self.top_50
        elif mode == "top100":
            ports = self.top_50 + [11, 17, 18, 19, 37, 49, 70, 81, 88, 106, 109, 113,
                                   115, 117, 119, 123, 144, 146, 150, 156, 210, 213,
                                   220, 259, 264, 315, 350, 389, 427, 434, 444, 464,
                                   512, 513, 514, 515, 524, 540, 548, 554, 563, 587,
                                   591, 593, 631, 636, 646, 691, 749, 750]
        elif mode == "full":
            ports = list(range(1, 65536))
        else:
            ports = list(range(1, 1025))

        thread = threading.Thread(target=self.scan, args=(host, ports), daemon=True)
        thread.start()

    def cancel_scan(self):
        self.running = False
        self.status_label.set_text("Iptal edildi")
        self.scan_btn.set_sensitive(True)
        self.cancel_btn.set_sensitive(False)

    def scan(self, host, ports):
        try:
            ip = socket.gethostbyname(host)
            GLib.idle_add(lambda: self.status_label.set_text(f"Taranıyor: {host} ({ip})"))
        except socket.gaierror:
            GLib.idle_add(lambda: self.status_label.set_text("Host cozulemedi"))
            GLib.idle_add(self.finish_scan)
            return

        total = len(ports)
        found = 0
        for i, port in enumerate(ports):
            if not self.running:
                break
            try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        found += 1
                        banner = ""
                        try:
                            s.settimeout(2)
                            s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                            banner = s.recv(256).decode("utf-8", errors="ignore").strip()[:80]
                        except Exception:
                            pass
                        s.close()
                        row = [str(port), "ACIK", port_str(port), banner]
                        GLib.idle_add(self.liststore.append, row)
                    else:
                        s.close()
            except Exception:
                pass
            if i % 10 == 0:
                GLib.idle_add(lambda p=i+1, t=total: self.status_label.set_text(
                    f"Taranıyor: {p}/{t} port ({found} acik)"))

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.cancel_btn.set_sensitive(False)
        count = len(self.liststore)
        self.status_label.set_text(f"Tamamlandi: {count} acik port bulundu")
