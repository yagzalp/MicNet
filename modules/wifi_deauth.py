import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import subprocess
import re


class WifiDeauthTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="WiFi Deauth Saldırısı")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="WiFi aglarina deauth (baglanti kesme) saldirisi yapar. Sadece egitim amacli kullanilmalidir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        # Ağ seçimi
        frame1 = Gtk.Frame(label="Hedef Ağ")
        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox1.set_border_width(16)

        hbox_bssid = Gtk.Box(spacing=6)
        hbox_bssid.pack_start(Gtk.Label(label="BSSID (MAC):"), False, False, 0)
        self.bssid_entry = Gtk.Entry()
        self.bssid_entry.set_placeholder_text("ff:ff:ff:ff:ff:ff")
        hbox_bssid.pack_start(self.bssid_entry, True, True, 0)
        vbox1.pack_start(hbox_bssid, False, False, 0)

        hbox_ch = Gtk.Box(spacing=6)
        hbox_ch.pack_start(Gtk.Label(label="Kanal:"), False, False, 0)
        self.channel_spin = Gtk.SpinButton.new_with_range(1, 14, 1)
        hbox_ch.pack_start(self.channel_spin, False, False, 0)
        vbox1.pack_start(hbox_ch, False, False, 0)

        frame1.add(vbox1)
        self.pack_start(frame1, False, False, 0)

        # İstemci seçimi (opsiyonel)
        frame2 = Gtk.Frame(label="Hedef İstemci (opsiyonel - boş bırakılırsa tüm istemciler)")
        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox2.set_border_width(16)
        self.client_entry = Gtk.Entry()
        self.client_entry.set_placeholder_text("İstemci MAC adresi (boş = broadcast)")
        vbox2.pack_start(self.client_entry, False, False, 0)
        frame2.add(vbox2)
        self.pack_start(frame2, False, False, 0)

        # Kontroller
        hbox_ctrl = Gtk.Box(spacing=8)
        hbox_ctrl.set_halign(Gtk.Align.CENTER)
        self.deauth_btn = Gtk.Button(label="Saldırıyı Başlat")
        self.deauth_btn.connect("clicked", lambda _: self.start_deauth())
        hbox_ctrl.pack_start(self.deauth_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop_deauth())
        hbox_ctrl.pack_start(self.stop_btn, False, False, 0)
        self.pack_start(hbox_ctrl, False, False, 0)

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

    def append_text(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_deauth(self):
        bssid = self.bssid_entry.get_text().strip()
        if not bssid:
            self.status_label.set_text("Lütfen BSSID girin")
            return

        self.running = True
        self.deauth_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.textbuffer.set_text("")
        self.append_text("[*] Deauth saldırısı başlatılıyor...")
        self.append_text(f"[*] Hedef BSSID: {bssid}")
        self.append_text(f"[*] Kanal: {int(self.channel_spin.get_value())}")
        self.append_text("[*] Uyarı: Bu işlem için monitör modu (aireplay-ng) gerekir.")
        self.append_text("[*] Alternatif olarak mdk4 veya bettercap kullanılabilir.")
        self.status_label.set_text("Saldırı başlatıldı")

        thread = threading.Thread(
            target=self.run_deauth, args=(bssid,), daemon=True
        )
        thread.start()

    def run_deauth(self, bssid):
        channel = int(self.channel_spin.get_value())
        client = self.client_entry.get_text().strip()

        self.append_text(f"\n[!] Uyarı: Bu araç yalnızca eğitim amaçlıdır.")
        self.append_text(f"[!] İzinsiz kullanımı yasa dışıdır.\n")

        self.append_text(f"\n[*] Kullanılabilecek komutlar:")
        self.append_text(f"  # Kanalı ayarla:")
        self.append_text(f"  sudo iwconfig wlan0 channel {channel}")
        self.append_text(f"  # Deauth gönder:")
        if client:
            self.append_text(f"  sudo aireplay-ng -0 0 -a {bssid} -c {client} wlan0")
        else:
            self.append_text(f"  sudo aireplay-ng -0 0 -a {bssid} wlan0")
        self.append_text(f"\n  # Alternatif (mdk4):")
        self.append_text(f"  sudo mdk4 wlan0 d -B {bssid}")

        GLib.idle_add(self.finish_deauth)

    def stop_deauth(self):
        self.running = False
        if self.process:
            self.process.terminate()
        self.deauth_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.append_text("\n[*] Saldırı durduruldu")
        self.status_label.set_text("Durduruldu")

    def finish_deauth(self):
        self.running = False
        self.deauth_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.status_label.set_text("Hazır")
