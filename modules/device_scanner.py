import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import subprocess as sp
import re
import ipaddress
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
except ImportError:
    requests = None


class DeviceScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Cihaz Tarama")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Yakindaki agdaki tum cihazlari bulur: IP adresi, MAC adresi, marka (uretici) ve model bilgisini gosterir. MAC adresinin ilk 6 hanesinden uretici tespit edilir.")
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
        self.net_entry.set_size_request(220, 30)
        grid.attach(self.net_entry, 1, 0, 1, 1)
        self.detect_btn = Gtk.Button(label="Oto Tespit")
        self.detect_btn.connect("clicked", lambda _: self.detect_network())
        grid.attach(self.detect_btn, 2, 0, 1, 1)

        self.online_check = Gtk.CheckButton(label="Ureticiyi internetten dogrula (macvendors.com)")
        self.online_check.set_active(True)
        grid.attach(self.online_check, 0, 1, 3, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.scan_btn = Gtk.Button(label="Tara")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop())
        self.stop_btn.get_style_context().add_class("destructive-action")
        hbox.pack_start(self.stop_btn, False, False, 0)
        self.export_btn = Gtk.Button(label="Listeyi Kaydet")
        self.export_btn.connect("clicked", lambda _: self.export_list())
        hbox.pack_start(self.export_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

        self.liststore = Gtk.ListStore(str, str, str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        cols = [("IP", 0), ("MAC", 1), ("Marka", 2), ("Model / Ad", 3), ("Hostname", 4)]
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

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_monospace(True)
        self.textview.get_style_context().add_class("output-text")
        self.textbuffer = self.textview.get_buffer()
        sw2 = Gtk.ScrolledWindow()
        sw2.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw2.set_size_request(-1, 130)
        sw2.add(self.textview)
        self.pack_start(sw2, False, False, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

        self.running = False
        self.stopped = False
        self.devices = []
        self.vendor_cache = {}

        self.VENDOR_DB = {
            "00037F": "Cisco", "000C29": "VMware", "005056": "VMware",
            "000569": "VMware", "080027": "Oracle/VirtualBox", "525400": "QEMU/KVM",
            "000E0C": "Apple", "001636": "Apple", "00188B": "Apple",
            "0026BB": "Apple", "041E64": "Apple", "D850E6": "Apple",
            "3CD9DB": "Apple", "ACBC32": "Apple", "F0D1A9": "Apple",
            "70656B": "Apple", "A8B84B": "Apple", "5886FA": "Apple",
            "885395": "Samsung", "001E4F": "Samsung", "00D021": "Samsung",
            "A439F9": "Samsung", "24949B": "Samsung", "F0953A": "Samsung",
            "E4FD78": "Samsung", "90B6FF": "Samsung", "3C5E8F": "Samsung",
            "F0B429": "Google", "A4C361": "Google", "18B430": "Google",
            "8CA1E7": "Google", "D8536B": "Google", "DCFAD5": "Google",
            "00163E": "Xiaomi", "C0EEFB": "Xiaomi", "844FC9": "Xiaomi",
            "286C07": "Xiaomi", "0C7C28": "Xiaomi", "7CB23B": "Xiaomi",
            "3C5A37": "Huawei", "00B5D6": "Huawei", "CC6DA0": "Huawei",
            "48A215": "Huawei", "7CF05F": "Huawei", "282E18": "Huawei",
            "A42C9E": "Huawei", "001122": "TP-Link", "004096": "TP-Link",
            "E0E751": "TP-Link", "50C7BF": "TP-Link", "E46D6C": "TP-Link",
            "08A151": "TP-Link", "340108": "TP-Link", "686E69": "TP-Link",
            "0015E1": "ASUS", "00605B": "ASUS", "F07960": "ASUS",
            "DCA904": "ASUS", "04D9F5": "ASUS", "109ADD": "ASUS",
            "A4B1C1": "D-Link", "001B11": "D-Link", "000C39": "D-Link",
            "28C2DD": "D-Link", "1C7EE5": "D-Link", "CC05A4": "D-Link",
            "001A79": "Netgear", "20E52A": "Netgear", "A0C4E5": "Netgear",
            "C0A0BB": "Netgear", "6C8CDB": "Netgear", "C864C7": "Netgear",
            "0017C8": "Linksys", "001A92": "Linksys", "000282": "Linksys",
            "001C10": "Linksys", "A0D7B8": "Linksys", "B4C9CF": "Linksys",
            "002622": "Belkin", "0090A2": "Belkin", "0030BD": "Belkin",
            "0021F7": "Zyxel", "001DAA": "Zyxel", "90F652": "Raspberry Pi",
            "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi", "28CDC1": "Raspberry Pi",
            "E45F01": "Raspberry Pi", "A4CF12": "Raspberry Pi", "F0B552": "Raspberry Pi",
            "88A25B": "Amazon", "74C246": "Amazon", "B0891D": "Amazon",
            "FCE57F": "Amazon", "A07905": "Amazon", "847DA6": "Amazon",
            "44D884": "Amazon", "A001DE": "Amazon", "049226": "Amazon",
            "0C8BFD": "LG", "100C6B": "LG", "BCC410": "LG",
            "048C03": "LG", "40D28A": "LG", "A080C7": "LG",
            "0013A9": "Sony", "00269E": "Sony", "3C2AF9": "Sony",
            "D0EBE0": "Sony", "B8CB29": "Sony", "4C46D3": "Sony",
            "001B7A": "HTC", "04E2C4": "HTC", "F8F1B6": "HTC",
            "001D69": "Motorola", "0050C2": "Motorola", "1083D1": "Motorola",
            "34F62A": "Motorola", "888927": "Motorola", "C819F7": "Motorola",
            "0015E9": "Nokia", "001D68": "Nokia", "647CAD": "Nokia",
            "108F1B": "Nokia", "34BDC8": "Nokia", "6CB7D2": "Nokia",
            "001E8F": "Lenovo", "001FA1": "Lenovo", "240A64": "Lenovo",
            "7081DB": "Lenovo", "54EAAE": "Lenovo", "9CE6E7": "Lenovo",
            "001C14": "Dell", "0015C5": "Dell", "001A4B": "Dell",
            "002219": "Dell", "B42B0A": "Dell", "F0DEF1": "Dell",
            "00A0C9": "Intel", "0050B6": "Intel", "001A7D": "Intel",
            "00121A": "HP", "001C25": "HP", "00223A": "HP",
            "3C52A1": "HP", "28D244": "HP", "B8CA3A": "HP",
            "001124": "Acer", "0060B3": "Acer", "DCF4C8": "Acer",
            "0015AF": "Toshiba", "002663": "Toshiba", "F07426": "Toshiba",
            "00D06E": "Brother", "001F2A": "Brother", "0050C2": "Brother",
            "000085": "Canon", "0010DC": "Canon", "2C9E5F": "Canon",
            "001B63": "Canon", "AC3D05": "Canon", "00EC00": "Canon",
            "000339": "Epson", "000B6A": "Epson", "0080E0": "Epson",
            "00E0B8": "Epson", "58E6BA": "Epson", "A0AEA8": "Epson",
            "000476": "Synology", "001132": "Synology", "90B34B": "Synology",
            "00C0B7": "QNAP", "0C62A6": "QNAP", "4868B4": "QNAP",
            "FC75E6": "MikroTik", "A41F72": "MikroTik", "4C5E0C": "MikroTik",
            "048D38": "MikroTik", "2C7490": "MikroTik", "6C3B6B": "MikroTik",
            "000C42": "Ubiquiti", "0011A7": "Ubiquiti", "78E3B5": "Ubiquiti",
            "68D719": "Ubiquiti", "04DDA1": "Ubiquiti", "A0D3C1": "Ubiquiti",
            "000FD4": "AVM (Fritz!)", "00307A": "AVM (Fritz!)", "00A33E": "AVM (Fritz!)",
            "9C133F": "Aruba", "0024DC": "Aruba", "0050B6": "Aruba",
            "000EC7": "Askey", "080058": "Arris", "C4B572": "Arris",
            "380B89": "Arris", "48BE2D": "Arris", "40516B": "Arris",
            "88D7F6": "Motorola", "848968": "Roku", "C05763": "Roku",
            "245EBE": "Roku", "B8E3A5": "Roku", "E8802E": "Roku",
            "100D7F": "Espressif (ESP32)", "24A160": "Espressif (ESP32)",
            "30AEA4": "Espressif (ESP32)", "24B8D2": "Espressif (ESP32)",
            "500BB0": "OnePlus", "5B5CFE": "OnePlus", "90F803": "OnePlus",
            "E016C8": "OPPO", "3C8CF8": "OPPO", "5C6DF7": "OPPO",
            "989696": "vivo", "8C5421": "vivo", "B072BF": "vivo",
            "F81654": "Honor", "9C50EE": "Honor", "30489A": "Honor",
            "2C4147": "OnePlus", "D8A2A5": "Sonos", "7825AD": "Sonos",
            "6A0F8B": "Sonos", "54B03A": "Sonos", "E47185": "Sonos",
            "18B52E": "Nordic (IoT)", "F8A45F": "Nordic (IoT)", "EC1E6B": "Amazon",
            "006A3E": "Wyze", "A8B5DA": "Wyze", "641666": "Sagemcom",
            "001A2B": "Sagemcom", "3C40E9": "Ziggo/Sagemcom", "90CDB6": "Sagemcom",
            "000BAB": "Devolo", "04F76A": "Devolo", "1ACB89": "Devolo",
            "FCFBFB": "Fire TV/Amazon", "4875E8": "Amazon", "9AEFD5": "Alexa/Amazon",
            "0030A0": "Panasonic", "C45584": "Panasonic", "00E027": "Panasonic",
            "00AE1E": "Panasonic", "0030F3": "Toshiba", "007A5D": "Gigaset",
            "001EC1": "Gigaset", "0CC9B3": "Gigaset", "0087C3": "Yealink",
            "04F021": "Yealink", "2C2D48": "Raspberry Pi", "58572D": "TP-Link",
            "3C32BF": "Aruba", "04D3B0": "Apple", "8C2DAA": "Samsung",
            "94E848": "Samsung", "A8FAF3": "Xiaomi", "8CE77D": "Xiaomi",
        }

        self.MODEL_HINTS = {
            "iphone": "iPhone", "ipad": "iPad", "macbook": "MacBook",
            "imac": "iMac", "macmini": "Mac mini", "galaxy": "Samsung Galaxy",
            "pixel": "Google Pixel", "xiaomi": "Xiaomi", "redmi": "Xiaomi Redmi",
            "huawei": "Huawei", "honor": "Honor", "oneplus": "OnePlus",
            "oppo": "OPPO", "vivo": "vivo", "nokia": "Nokia",
            "raspberry": "Raspberry Pi", "raspi": "Raspberry Pi",
            "echo": "Amazon Echo", "alexa": "Amazon Alexa", "nest": "Google Nest",
            "roku": "Roku", "firetv": "Amazon Fire TV", "fire-tv": "Amazon Fire TV",
            "esp32": "ESP32 (IoT)", "esp8266": "ESP8266 (IoT)",
            "android": "Android", "windows": "Windows PC", "win-": "Windows PC",
            "laptop": "Laptop", "desktop": "Desktop", "pc-": "PC",
            "printer": "Yazici", "canon": "Canon Yazici", "epson": "Epson Yazici",
            "hp": "HP Yazici", "brother": "Brother Yazici",
            "sonos": "Sonos", "apple-tv": "Apple TV", "nvidia": "NVIDIA Shield",
            "chromecast": "Google Chromecast", "gcp-": "Google Chromecast",
            "tplink": "TP-Link", "tp-link": "TP-Link", "router": "Router",
            "wifi": "WiFi Cihazi", "amazon": "Amazon Cihaz", "led": "Akilli Isik",
            "light": "Akilli Isik", "camera": "IP Kamera", "cam-": "IP Kamera",
            "smart-tv": "Akilli TV", "smarttv": "Akilli TV", "tv": "TV",
            "mi": "Xiaomi", "huami": "Xiaomi", "amazon": "Amazon",
        }

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
            self.status_label.set_text(f"Hata: {e}")

    def _is_ipv4(self, ip):
        try:
            ipaddress.IPv4Address(ip)
            return True
        except Exception:
            return False

    def read_arp(self):
        arp = {}
        try:
            r = sp.run(["ip", "neigh", "show"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                parts = line.split()
                if not parts:
                    continue
                ip = parts[0]
                mac = "?"
                for i, p in enumerate(parts):
                    if p == "lladdr" and i + 1 < len(parts):
                        mac = parts[i + 1].upper()
                if (mac != "?" and mac != "(INCOMPLETE)" and ":" in mac
                        and self._is_ipv4(ip)):
                    arp[ip] = mac
        except Exception:
            pass
        try:
            with open("/proc/net/arp") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 4 and parts[3] != "00:00:00:00:00:00":
                        arp[parts[0]] = parts[3].upper()
        except Exception:
            pass
        return arp

    def ping_host(self, ip):
        try:
            r = sp.run(["ping", "-c", "1", "-W", "1", "-n", ip],
                       capture_output=True, timeout=3)
            if r.returncode == 0:
                return ip
        except Exception:
            pass
        for port in (80, 443, 22, 445):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.4)
                if s.connect_ex((ip, port)) == 0:
                    s.close()
                    return ip
                s.close()
            except Exception:
                pass
        return None

    def get_own_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            pass
        return None

    def normalize_mac(self, mac):
        if ":" not in mac or mac in ("?", ""):
            return mac
        return mac.upper()

    def oui(self, mac):
        if len(mac) < 8:
            return ""
        return mac[:8].replace(":", "").upper()

    def lookup_vendor(self, mac, online):
        mac = self.normalize_mac(mac)
        o = self.oui(mac)
        if not o:
            return "?"
        if o in self.vendor_cache:
            return self.vendor_cache[o]
        local = self.VENDOR_DB.get(o, "Bilinmiyor")
        if online and requests is not None and local == "Bilinmiyor":
            try:
                url = f"https://api.macvendors.com/{mac}"
                r = requests.get(url, timeout=6)
                if r.status_code == 200 and r.text.strip():
                    local = r.text.strip()[:40]
            except Exception:
                pass
        self.vendor_cache[o] = local
        return local

    def guess_model(self, hostname, vendor):
        h = (hostname or "").lower()
        for key, model in self.MODEL_HINTS.items():
            if key in h:
                return model
        if vendor and vendor != "Bilinmiyor":
            return vendor + " cihaz"
        return "?"

    def get_hostname(self, ip):
        try:
            name = socket.gethostbyaddr(ip)[0]
            return name if name else "?"
        except Exception:
            return "?"

    def start_scan(self):
        net = self.net_entry.get_text().strip()
        if not net:
            self.status_label.set_text("Ag adresini girin veya Oto Tespit kullanin")
            return
        if self.running:
            return
        self.running = True
        self.stopped = False
        self.scan_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.liststore.clear()
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(net,), daemon=True)
        thread.start()

    def scan(self, net):
        online = self.online_check.get_active()
        try:
            network = ipaddress.ip_network(net, strict=False)
            hosts = list(network.hosts())
        except Exception as e:
            self.log(f"[-] Gecersiz ag adresi: {e}")
            GLib.idle_add(self.finish)
            return
        if len(hosts) > 1024:
            self.log(f"[-] Cok buyuk ag ({len(hosts)} adres). En fazla /22 desteklenir.")
            GLib.idle_add(self.finish)
            return

        own_ip = self.get_own_ip()
        arp0 = self.read_arp()

        self.log(f"[*] Ag: {net}")
        self.log(f"[*] Adres sayisi: {len(hosts)}")
        if own_ip:
            self.log(f"[*] Sizin IP: {own_ip}")
        self.log(f"[*] ARP tablosunda mevcut: {len(arp0)} cihaz")
        self.log("[*] Ping taramasi baslatildi...")

        alive = set(arp0.keys())
        found = 0
        with ThreadPoolExecutor(max_workers=60) as ex:
            futures = {ex.submit(self.ping_host, str(h)): str(h) for h in hosts}
            done = 0
            for fut in futures:
                if self.stopped:
                    for f in futures:
                        f.cancel()
                    break
                res = fut.result()
                done += 1
                if res:
                    alive.add(res)
                if done % 50 == 0:
                    GLib.idle_add(self.status_label.set_text,
                                  f"Taranıyor... {done}/{len(hosts)} ({len(alive)} cihaz)")

        arp = self.read_arp()
        arp.update(arp0)

        devices = []
        alive4 = [x for x in alive if self._is_ipv4(x)]
        for ip in sorted(alive4, key=lambda x: ipaddress.IPv4Address(x)):
            mac = arp.get(ip, "?")
            if mac == "?" and own_ip == ip:
                mac = self.get_own_mac()
            if mac == "?":
                mac = "?"
            vendor = self.lookup_vendor(mac, online)
            hostname = self.get_hostname(ip)
            model = self.guess_model(hostname, vendor)
            devices.append({"ip": ip, "mac": mac, "vendor": vendor,
                            "model": model, "hostname": hostname})
            found += 1

        if not self.stopped:
            for d in devices:
                row = [d["ip"], d["mac"], d["vendor"], d["model"], d["hostname"]]
                GLib.idle_add(self.liststore.append, row)
            GLib.idle_add(self._log_devices, devices, own_ip)
        self.devices = devices
        GLib.idle_add(self.status_label.set_text, f"{len(devices)} cihaz bulundu")
        GLib.idle_add(self.finish)

    def _log_devices(self, devices, own_ip):
        self.log("")
        self.log("=== BULUNAN CIHAZLAR ===")
        for d in devices:
            who = " (bu cihaz)" if d["ip"] == own_ip else ""
            self.log(f"{d['ip']:16s} {d['mac']:20s} {d['vendor']:16s} {d['model']}{who}")

    def get_own_mac(self):
        try:
            r = sp.run(["ip", "addr", "show"], capture_output=True, text=True, timeout=5)
            m = re.search(r"link/ether\s+(\S+)", r.stdout)
            if m:
                return m.group(1).upper()
        except Exception:
            pass
        return "?"

    def stop(self):
        self.stopped = True
        self.status_label.set_text("Durduruluyor...")

    def export_list(self):
        if not self.devices:
            self.status_label.set_text("Once tarama yapin")
            return
        dialog = Gtk.FileChooserDialog(
            title="Cihaz Listesini Kaydet",
            transient_for=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                     Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT),
        )
        dialog.set_current_name("cihazlar.csv")
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            try:
                with open(path, "w") as f:
                    f.write("IP,MAC,Marka,Model,Hostname\n")
                    for d in self.devices:
                        f.write(f"{d['ip']},{d['mac']},{d['vendor']},{d['model']},{d['hostname']}\n")
                self.status_label.set_text("Liste kaydedildi")
            except Exception:
                self.status_label.set_text("Kaydedilemedi")
        dialog.destroy()

    def finish(self):
        self.running = False
        self.stopped = False
        self.scan_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
