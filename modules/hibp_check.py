import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import hashlib
import requests

HIBP_URL = "https://api.pwnedpasswords.com/range/"


class HibpCheckTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Sifre Leak Kontrolu (HIBP)")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Parolaniz daha once veri ihlallerinde ele gecirildi mi? Have I Been Pwned (HIBP) k-anonimlik API'si kullanilir: parola HICBIR YERE gonderilmez, yalnizca SHA-1 oncinin 5 karakteri kontrol edilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Parola")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(visibility=False)
        self.entry.set_placeholder_text("Parolanizi girin")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_check())
        hbox.pack_start(self.entry, False, False, 0)
        self.check_btn = Gtk.Button(label="Kontrol Et")
        self.check_btn.connect("clicked", lambda _: self.start_check())
        self.check_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.check_btn, False, False, 0)
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

    def start_check(self):
        pwd = self.entry.get_text()
        if not pwd:
            self.status_label.set_text("Parola girin")
            return
        if self.running:
            return
        self.running = True
        self.check_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Kontrol ediliyor...")
        thread = threading.Thread(target=self.check, args=(pwd,), daemon=True)
        thread.start()

    def check(self, pwd):
        sha1 = hashlib.sha1(pwd.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        GLib.idle_add(self.log, f"[*] SHA-1 onci: {prefix} (sadece bu gonderilir)")
        try:
            r = requests.get(HIBP_URL + prefix, timeout=10, headers={"User-Agent": "MicNet"}, verify=True)
            if r.status_code == 200:
                found = 0
                for line in r.text.splitlines():
                    s, count = line.split(":")
                    if s == suffix:
                        found = int(count)
                        break
                if found:
                    GLib.idle_add(self.log, f"[!] PAROLA {found} KEZ VERI IHLALINDE GORULDU!")
                    GLib.idle_add(self.log, "    Bu parolayi DERHAL degistirin ve baska sitede kullanmayin.")
                else:
                    GLib.idle_add(self.log, "[+] Bilinen veri ihlallerinde bu parola bulunamadi.")
                GLib.idle_add(self.log, "[*] Kaynak: haveibeenpwned.com k-anonimlik API")
            else:
                GLib.idle_add(self.log, f"[-] API hatasi: HTTP {r.status_code}")
        except ImportError:
            GLib.idle_add(self.log, "[-] requests paketi yuklu degil")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_check)

    def finish_check(self):
        self.running = False
        self.check_btn.set_sensitive(True)
        self.status_label.set_text("Kontrol tamamlandi")
