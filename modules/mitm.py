import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import subprocess
import os
import sys
import time


class MITMTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="MITM - Ortadaki Adam Saldirisi")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="ARP spoofing ile ag trafigini kendi uzerinizden gecirir. Paket sayisini canli izler. Sadece kendi aginizda egitim icin kullanin.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef Ayarlari")
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

        grid.attach(Gtk.Label(label="Arayuz:"), 0, 2, 1, 1)
        iface_box = Gtk.Box(spacing=6)
        self.iface_entry = Gtk.Entry()
        self.iface_entry.set_placeholder_text("wlan0 / eth0 / enp0s3")
        iface_box.pack_start(self.iface_entry, True, True, 0)
        auto_btn = Gtk.Button(label="Otomatik")
        auto_btn.connect("clicked", lambda _: self.auto_detect())
        iface_box.pack_start(auto_btn, False, False, 0)
        grid.attach(iface_box, 1, 2, 1, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="ARP Spoofing Baslat")
        self.start_btn.connect("clicked", lambda _: self.start_mitm())
        hbox.pack_start(self.start_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop_mitm())
        hbox.pack_start(self.stop_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

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
        self.process = None
        self._reader = None

    def append_text(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")
        self.textview.scroll_to_iter(self.textbuffer.get_end_iter(), 0, False, 0, 0)

    def auto_detect(self):
        try:
            out = subprocess.run(
                ["ip", "route", "show", "default"], capture_output=True, text=True
            ).stdout
            for line in out.splitlines():
                parts = line.split()
                if "dev" in parts:
                    iface = parts[parts.index("dev") + 1]
                    self.iface_entry.set_text(iface)
                    self.append_text(f"[+] Arayuz algilandi: {iface}")
                    return
            self.status_label.set_text("Varsayilan ag arayuzu bulunamadi")
        except Exception as e:
            self.status_label.set_text(f"Algilama hatasi: {e}")

    def start_mitm(self):
        target = self.target_entry.get_text().strip()
        gateway = self.gateway_entry.get_text().strip()
        iface = self.iface_entry.get_text().strip()

        if not target or not gateway or not iface:
            self.status_label.set_text("Tum alanlari doldurun")
            return

        self.running = True
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.textbuffer.set_text("")
        self.append_text("[*] MITM saldirisi baslatiliyor...")
        self.append_text(f"[*] Hedef: {target}")
        self.append_text(f"[*] Gateway: {gateway}")
        self.append_text(f"[*] Arayuz: {iface}")
        self.append_text("[*] Root yetkisi icin sifre istenecek (pkexec)...")
        self.status_label.set_text("Sifre istemi bekleniyor...")

        worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mitm_worker.py")
        cmd = ["pkexec", sys.executable, worker, target, gateway, iface]
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._read_output, daemon=True)
        self._reader.start()
        self.append_text(f"[*] Worker baslatildi (PID: {self.process.pid})")

    def _read_output(self):
        for line in self.process.stdout:
            line = line.rstrip()
            if line:
                GLib.idle_add(self.append_text, line)
            if "[+] ARP spoofing calisiyor" in line:
                GLib.idle_add(self._set_status, "MITM calisiyor...")
        try:
            rc = self.process.wait()
        except Exception:
            rc = -1
        GLib.idle_add(self._on_exit, rc)

    def _set_status(self, msg):
        self.status_label.set_text(msg)

    def _on_exit(self, rc):
        self.running = False
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        if rc == 0:
            self.status_label.set_text("Durduruldu")
        elif rc is None:
            self.status_label.set_text("Bitti")
        else:
            self.status_label.set_text(f"Worker cikti (kod: {rc})")

    def stop_mitm(self):
        if self.process and self.process.poll() is None:
            self.append_text("[*] Durduruluyor... ARP tablolari geri yuklenecek.")
            self.process.send_signal(15)
        self.status_label.set_text("Durduruluyor...")
