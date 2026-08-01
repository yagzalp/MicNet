import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import subprocess
import re


class WifiScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="WiFi Scanner")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Cevredeki kablosuz aglari tarar ve SSID, MAC adresi, sinyal seviyesi, kanal ve sifreleme turu gibi bilgileri gosterir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.scan_btn = Gtk.Button(label="WiFi Tara")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        hbox.pack_start(self.scan_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop_scan())
        hbox.pack_start(self.stop_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

        self.liststore = Gtk.ListStore(str, str, str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)

        renderer_text = Gtk.CellRendererText()
        columns = [
            ("SSID", 0),
            ("BSSID (MAC)", 1),
            ("Sinyal", 2),
            ("Kanal", 3),
            ("Şifreleme", 4),
        ]
        for title_text, col_idx in columns:
            col = Gtk.TreeViewColumn(title_text, renderer_text, text=col_idx)
            col.set_resizable(True)
            col.set_sort_column_id(col_idx)
            self.treeview.append_column(col)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.treeview)
        self.pack_start(sw, True, True, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

        self.running = False

    def start_scan(self):
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.liststore.clear()
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan_wifi, daemon=True)
        thread.start()

    def stop_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.status_label.set_text("Tarama durduruldu")

    def scan_wifi(self):
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,CHAN,SECURITY", "dev", "wifi", "list"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout

            for line in output.strip().split("\n"):
                if not line or not self.running:
                    continue
                parts = line.split(":")
                if len(parts) < 3:
                    continue
                ssid = parts[0] or "(gizli)"
                bssid = parts[1].replace("\\:", ":") if len(parts) > 1 else "?"
                signal = parts[2] if len(parts) > 2 else "?"
                channel = parts[3] if len(parts) > 3 else "?"
                encryption = parts[4] if len(parts) > 4 else "?"

                GLib.idle_add(
                    self.liststore.append,
                    [ssid, bssid, signal, channel, encryption],
                )

            GLib.idle_add(self.finish_scan)

        except subprocess.TimeoutExpired:
            GLib.idle_add(self.status_label.set_text, "Zaman aşımı")
        except FileNotFoundError:
            GLib.idle_add(self.status_label.set_text, "nmcli bulunamadı (NetworkManager yüklü değil)")
        except Exception as e:
            GLib.idle_add(self.status_label.set_text, f"Hata: {e}")

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        count = len(self.liststore)
        self.status_label.set_text(f"Tarama tamamlandı: {count} ağ bulundu")
