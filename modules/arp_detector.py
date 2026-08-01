import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import subprocess as sp
import re


class ArpDetectorTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="ARP Spoof Dedektoru")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Agdaki ARP spoofing saldirilarini tespit eder. ARP tablosunu analiz ederek, gateway MAC adresindeki degisiklikleri ve MITM saldirilarini algilar.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="ARP Analizi")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        lbl = Gtk.Label(label="Bu arac ARP tablosunu okuyarak agdaki anormallikleri tespit eder. Birden fazla IP ayni MAC'e sahipse ARP spoofing var demektir.")
        lbl.set_xalign(0)
        lbl.get_style_context().add_class("desc-label")
        lbl.set_line_wrap(True)
        input_box.pack_start(lbl, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.scan_btn = Gtk.Button(label="ARP Tablosunu Tara")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)

        self.watch_btn = Gtk.Button(label="Surekli Izle (3sn)")
        self.watch_btn.connect("clicked", lambda _: self.toggle_watch())
        hbox.pack_start(self.watch_btn, False, False, 0)
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
        self.status_label.set_xalign(0)
        self.pack_start(self.status_label, False, False, 0)

        self.running = False
        self.watching = False
        self.watch_timer = None

    def log(self, text):
        GLib.idle_add(self._append, text)

    def _append(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_scan(self):
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("ARP tablosu analiz ediliyor...")
        thread = threading.Thread(target=self.scan, daemon=True)
        thread.start()

    def toggle_watch(self):
        if self.watching:
            self.watching = False
            self.watch_btn.set_label("Surekli Izle (3sn)")
            self.status_label.set_text("Izleme durduruldu")
        else:
            self.watching = True
            self.watch_btn.set_label("Durdur")
            self.textbuffer.set_text("")
            self.status_label.set_text("ARP izleniyor (3sn aralikla)...")
            self.log("[*] ARP spoofing izleme basladi (Cikis: Durdur butonu)\n")
            thread = threading.Thread(target=self.watch_loop, daemon=True)
            thread.start()

    def watch_loop(self):
        while self.watching:
            self.scan_arp()
            import time
            for _ in range(30):
                if not self.watching:
                    break
                time.sleep(0.1)

    def get_gateway_ip(self):
        try:
            r = sp.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5)
            m = re.search(r"default via (\S+)", r.stdout)
            if m:
                return m.group(1)
        except Exception:
            pass
        return "192.168.1.1"

    def scan(self):
        self.scan_arp()
        GLib.idle_add(self.finish)

    def scan_arp(self):
        try:
            r = sp.run(["ip", "neigh", "show"], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")

            if not lines or lines[0] == "":
                self.log("[-] ARP tablosu bos veya okunamadi")
                self.log("    Root yetkisi gerekmeyen bir sistem kullaniliyor")
                self.log("    ip neigh komutu ile ARP tablosu okunur")
                return

            entries = []
            mac_map = {}
            ip_map = {}
            gw_ip = self.get_gateway_ip()

            self.log(f"[*] Gateway: {gw_ip}")
            self.log(f"[*] ARP tablosu: {len(lines)} kayit\n")

            for line in lines:
                parts = line.split()
                if len(parts) < 3:
                    continue
                ip = parts[0]
                state = parts[1] if len(parts) > 1 else "?"
                mac = "?"
                dev = "?"

                for i, p in enumerate(parts):
                    if p == "lladdr" and i + 1 < len(parts):
                        mac = parts[i + 1]
                    if p == "dev" and i + 1 < len(parts):
                        dev = parts[i + 1]

                entries.append({
                    "ip": ip, "mac": mac, "state": state, "dev": dev
                })

                if mac != "?" and mac != "(incomplete)":
                    mac_map.setdefault(mac, []).append(ip)
                ip_map[ip] = mac

            self.log(f"{'IP':20s} {'MAC':20s} {'Durum':12s} {'Arayuz':10s}")
            self.log("-" * 62)
            for e in entries:
                mac_display = e["mac"][:17] if e["mac"] != "?" else "?"
                self.log(f"{e['ip']:20s} {mac_display:20s} {e['state']:12s} {e['dev']:10s}")

            self.log("")
            self.log("=== SPOOFING ANALIZI ===")

            spoofed = False

            for mac, ips in mac_map.items():
                ipv4_list = [ip for ip in ips if ":" not in ip]
                if len(ipv4_list) > 1:
                    self.log(f"[!!!] ARP SPOOFING TESPITI!")
                    self.log(f"      MAC: {mac} birden fazla IPV4 adresine ait!")
                    for ip in ipv4_list:
                        self.log(f"      - {ip}")
                    spoofed = True

            gw_ipv4 = gw_ip.split("%")[0]
            gw_mac = ip_map.get(gw_ipv4, "?")
            for mac, ips in mac_map.items():
                ipv4_list = [ip for ip in ips if ":" not in ip]
                if gw_ipv4 not in ipv4_list and len(ipv4_list) > 1:
                    for ip in ipv4_list:
                        if ip != gw_ipv4:
                            self.log(f"[?] Supheli: {ip} ({mac}) - Gateway ile ayni MAC")
                            spoofed = True

            if not spoofed:
                self.log("[+] ARP spoofing tespit edilmedi, ag temiz gorunuyor")
            else:
                self.log("")
                self.log("  Ne yapmalisiniz?")
                self.log("  1. Agdaki cihazlari tek tek kontrol edin")
                self.log("  2. Statik ARP girisleri ekleyin")
                self.log("  3. Kablosuz ag sifresini degistirin")
                self.log("  4. WPA2/WPA3 kullandiginizdan emin olun")

        except sp.TimeoutExpired:
            self.log("[-] ARP tablosu okunurken zaman asimi")
        except FileNotFoundError:
            self.log("[-] 'ip' komutu bulunamadi")
        except Exception as e:
            self.log(f"[-] Hata: {e}")

    def finish(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("ARP analizi tamamlandi")
