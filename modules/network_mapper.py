import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import subprocess as sp
import re
import ipaddress


class NetworkMapperTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Ag Tarayici (Network Mapper)")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Yerel agdaki cihazlari, IP adreslerini, MAC adreslerini ve acik portlari tarar. Cihaz ureticisi ve OS tespiti yapar.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Ag Ayarlari")
        grid = Gtk.Grid()
        grid.set_border_width(16)
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        grid.attach(Gtk.Label(label="Ag (CIDR):"), 0, 0, 1, 1)
        self.net_entry = Gtk.Entry(placeholder_text="192.168.1.0/24")
        self.net_entry.set_size_request(200, 30)
        grid.attach(self.net_entry, 1, 0, 1, 1)
        self.detect_btn = Gtk.Button(label="Oto Tespit")
        self.detect_btn.connect("clicked", lambda _: self.detect_network())
        grid.attach(self.detect_btn, 2, 0, 1, 1)

        grid.attach(Gtk.Label(label="Port araligi:"), 0, 1, 1, 1)
        port_hbox = Gtk.Box(spacing=4)
        self.port_start = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.port_start.set_value(1)
        self.port_start.set_size_request(80, 30)
        port_hbox.pack_start(self.port_start, False, False, 0)
        port_hbox.pack_start(Gtk.Label(label="-"), False, False, 0)
        self.port_end = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.port_end.set_value(1000)
        self.port_end.set_size_request(80, 30)
        port_hbox.pack_start(self.port_end, False, False, 0)
        grid.attach(port_hbox, 1, 1, 1, 1)

        self.scan_hosts_check = Gtk.CheckButton(label="Cihazlari tara (Ping)")
        self.scan_hosts_check.set_active(True)
        grid.attach(self.scan_hosts_check, 0, 2, 2, 1)

        self.scan_ports_check = Gtk.CheckButton(label="Port tara (yavastir)")
        self.scan_ports_check.set_active(False)
        grid.attach(self.scan_ports_check, 0, 3, 2, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.scan_btn = Gtk.Button(label="Ag Taramasi Baslat")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop())
        self.stop_btn.get_style_context().add_class("destructive-action")
        hbox.pack_start(self.stop_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

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
        self.status_label.set_xalign(0)
        self.pack_start(self.status_label, False, False, 0)

        self.running = False
        self.stopped = False

    def log(self, text):
        GLib.idle_add(self._append, text)

    def _append(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def detect_network(self):
        try:
            r = sp.run(["ip", "-4", "addr", "show", "scope", "global"],
                       capture_output=True, text=True, timeout=5)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", r.stdout)
            if m:
                self.net_entry.set_text(m.group(1))
                self.status_label.set_text(f"Ag tespit edildi: {m.group(1)}")
            else:
                self.status_label.set_text("Ag tespit edilemedi")
        except Exception as e:
            self.status_label.set_text(f"hata: {e}")

    def get_mac(self, ip):
        try:
            r = sp.run(["ip", "neigh", "show", ip], capture_output=True, text=True, timeout=3)
            m = re.search(r"lladdr\s+(\S+)", r.stdout)
            if m:
                return m.group(1)
        except Exception:
            pass
        return "?"

    def get_vendor(self, mac):
        if mac == "?" or len(mac) < 8:
            return "?"
        oui = mac[:8].upper().replace(":", "")
        vendors = {
            "00037F": "Cisco", "000C29": "VMware", "005056": "VMware",
            "000569": "VMware", "001C14": "Dell", "0015C5": "Dell",
            "001A4B": "Dell", "002219": "Dell", "000E0C": "Apple",
            "001636": "Apple", "00188B": "Apple", "0026BB": "Apple",
            "041E64": "Apple", "080027": "Oracle/VirtualBox",
            "0050B6": "Intel", "001A7D": "Intel", "00A0C9": "Intel",
            "0050F2": "Microsoft", "001D09": "Microsoft", "0003FF": "Microsoft",
            "885395": "Samsung", "001E4F": "Samsung", "00D021": "Samsung",
            "001122": "TP-Link", "004096": "TP-Link", "E0E751": "TP-Link",
            "0015E1": "ASUS", "00605B": "ASUS", "F07960": "ASUS",
            "A41F72": "Routerboard", "4C5E0C": "Routerboard",
            "FC75E6": "MikroTik", "E46D6C": "MikroTik",
            "90F652": "Raspberry Pi", "B827EB": "Raspberry Pi",
            "00AA01": "Xerox", "CC1AFA": "Cannonical",
            "3C5A37": "Huawei", "00B5D6": "Huawei",
            "0015E9": "Nokia", "001D68": "Nokia",
            "00163E": "Xiaomi", "C0EEFB": "Xiaomi",
            "844FC9": "Xiaomi", "D850E6": "Apple",
            "F0B429": "Google", "A4C361": "Google",
        }
        return vendors.get(oui, "Bilinmiyor")

    def stop(self):
        self.stopped = True
        self.status_label.set_text("Durduruluyor...")

    def start_scan(self):
        net = self.net_entry.get_text().strip()
        if not net:
            self.status_label.set_text("Ag adresini girin veya oto tespit kullanin")
            return
        if self.running:
            return
        self.running = True
        self.stopped = False
        self.scan_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(net,), daemon=True)
        thread.start()

    def scan(self, net):
        try:
            network = ipaddress.ip_network(net, strict=False)
            hosts = list(network.hosts())
        except Exception as e:
            self.log(f"[-] Gecersiz ag adresi: {e}")
            GLib.idle_add(self.finish)
            return

        self.log(f"[*] Ag: {net}")
        self.log(f"[*] Toplam: {len(hosts)} adres")
        self.log("")

        if self.scan_hosts_check.get_active():
            self.log("=== CANLI CIHAZLAR ===")
            self.log(f"{'IP':18s} {'MAC':20s} {'Uretici':16s}" + (" {'Port':30s}" if self.scan_ports_check.get_active() else ""))
            self.log("-" * 60)

            found = 0
            for i, host in enumerate(hosts):
                if self.stopped:
                    break
                ip = str(host)
                if i % 10 == 0:
                    GLib.idle_add(self.status_label.set_text,
                        f"Taranıyor... {i}/{len(hosts)} ({found} bulundu)")

                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, 80))
                    sock.close()

                    if result == 0 or result == 11:
                        # Host is alive
                        mac = self.get_mac(ip)
                        vendor = self.get_vendor(mac)
                        ports = ""

                        if self.scan_ports_check.get_active():
                            ports = self.scan_ports(ip)
                            self.log(f"{ip:18s} {mac:20s} {vendor:16s} {ports[:30]}")
                        else:
                            self.log(f"{ip:18s} {mac:20s} {vendor:16s}")
                        found += 1
                    # Also try ping
                    try:
                        ping = sp.run(["ping", "-c", "1", "-W", "1", ip],
                                      capture_output=True, timeout=2)
                        if ping.returncode == 0 and result != 0:
                            mac = self.get_mac(ip)
                            vendor = self.get_vendor(mac)
                            self.log(f"{ip:18s} {mac:20s} {vendor:16s}")
                            found += 1
                    except Exception:
                        pass

                except Exception:
                    pass

            self.log("")
            if self.stopped:
                self.log(f"[!] Durduruldu. {found} cihaz bulundu")
            else:
                self.log(f"[+] {found} cihaz bulundu")

        if self.scan_ports_check.get_active() and not self.stopped:
            self.log("")
            self.log("=== PORT TARAMASI ===")

        if self.stopped:
            self.log("[!] Tarama kullanici tarafindan durduruldu")

        GLib.idle_add(self.finish)

    def scan_ports(self, ip):
        common_ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
                        143, 443, 445, 993, 995, 1433, 1521, 2049,
                        3306, 3389, 5432, 5900, 6379, 8080, 8443]
        open_ports = []
        for port in common_ports:
            if self.stopped:
                break
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    service = self.get_service_name(port)
                    open_ports.append(f"{port}/{service}")
            except Exception:
                pass
        return ", ".join(open_ports[:10])

    def get_service_name(self, port):
        services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 111: "RPC", 135: "RPC", 139: "NetBIOS",
            143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle", 2049: "NFS", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
            8080: "HTTP-Alt", 8443: "HTTPS-Alt"
        }
        return services.get(port, "?")

    def finish(self):
        self.running = False
        self.stopped = False
        self.scan_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.status_label.set_text("Tarama tamamlandi")
