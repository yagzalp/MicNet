import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import json
import os


class SettingsTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Ayarlar & API Anahtarlari")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Harici API servislerine baglanmak icin API anahtarlarini yapilandirin. Anahtarlar localde saklanir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        self.config_path = os.path.expanduser("~/.config/micnet")
        self.config_file = os.path.join(self.config_path, "config.json")
        self.config = self.load_config()

        frame = Gtk.Frame(label="API Anahtarlari")
        grid = Gtk.Grid()
        grid.set_border_width(16)
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)

        self.entries = {}

        apis = [
            ("shodan", "Shodan", "shodan.io - IP/port bilgisi, ag tarama"),
            ("virustotal", "VirusTotal", "virustotal.com - URL/dosya tarama"),
            ("securitytrails", "SecurityTrails", "securitytrails.com - DNS history, subdomain"),
            ("abuseipdb", "AbuseIPDB", "abuseipdb.com - IP reputasyon sorgulama"),
        ]

        for i, (key, name, desc_text) in enumerate(apis):
            lbl = Gtk.Label(label=f"{name}:")
            lbl.set_xalign(0)
            lbl.set_tooltip_text(desc_text)
            grid.attach(lbl, 0, i, 1, 1)

            entry = Gtk.Entry()
            entry.set_size_request(350, 30)
            entry.set_placeholder_text(desc_text)
            if key in self.config.get("apikeys", {}):
                entry.set_text(self.config["apikeys"][key])
            self.entries[key] = entry
            grid.attach(entry, 1, i, 1, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        info_frame = Gtk.Frame(label="Nasil alinir?")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_border_width(16)

        info_text = Gtk.Label(
            label="API anahtarlari icin ilgili sitelere kayit olup profil sayfanizdan API key alabilirsiniz.\n"
                  "Tum servislerin ucretsiz kotalari vardir.\n"
                  "Anahtarlar sadece bu cihazda saklanir."
        )
        info_text.set_line_wrap(True)
        info_text.set_xalign(0)
        info_box.pack_start(info_text, False, False, 0)

        info_frame.add(info_box)
        self.pack_start(info_frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.save_btn = Gtk.Button(label="Kaydet")
        self.save_btn.connect("clicked", lambda _: self.save_config())
        self.save_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.save_btn, False, False, 0)
        self.clear_btn = Gtk.Button(label="Temizle")
        self.clear_btn.connect("clicked", lambda _: self.clear_keys())
        hbox.pack_start(self.clear_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

        self.status_label = Gtk.Label(label="")
        self.status_label.set_xalign(0)
        self.pack_start(self.status_label, False, False, 0)

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    return json.load(f)
        except Exception:
            pass
        return {"apikeys": {}}

    def save_config(self):
        try:
            os.makedirs(self.config_path, exist_ok=True)
            apikeys = {}
            for key, entry in self.entries.items():
                val = entry.get_text().strip()
                if val:
                    apikeys[key] = val
            self.config["apikeys"] = apikeys
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            self.status_label.set_text(f"Kaydedildi: {len(apikeys)} API anahtari")
        except Exception as e:
            self.status_label.set_text(f"Hata: {e}")

    def clear_keys(self):
        for entry in self.entries.values():
            entry.set_text("")
        self.status_label.set_text("Alanlar temizlendi. Kaydet butonuna basin.")
