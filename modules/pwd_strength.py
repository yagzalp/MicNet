import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import secrets
import string
import math


class PwdStrengthTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Sifre Gucluk Testi")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Sifrelerin gucluk analizini yapar. Entropi, karakter cesitliligi, brute-force suresi ve yaygin sifre kontrolu icerir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Sifre Analizi")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="Sifreyi girin...")
        self.entry.set_size_request(400, 30)
        self.entry.set_visibility(False)
        self.entry.connect("activate", lambda _: self.analyze())
        hbox.pack_start(self.entry, False, False, 0)
        self.toggle_btn = Gtk.Button(label="Goster")
        self.toggle_btn.connect("clicked", lambda _: self.toggle_visibility())
        hbox.pack_start(self.toggle_btn, False, False, 0)
        self.analyze_btn = Gtk.Button(label="Test Et")
        self.analyze_btn.connect("clicked", lambda _: self.analyze())
        self.analyze_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.analyze_btn, False, False, 0)
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

        self.visible = False

        self.common_passwords = {
            "123456", "password", "12345678", "qwerty", "12345",
            "123456789", "football", "1234", "1234567890", "admin",
            "letmein", "welcome", "monkey", "dragon", "master",
            "123123", "donald", "654321", "qwerty123", "123321",
            "iloveyou", "sunshine", "password1", "princess", "123qwe",
            "000000", "111111", "222222", "333333", "444444",
            "555555", "666666", "777777", "888888", "999999",
            "abc123", "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "1q2w3e4r", "qwerty12345", "passw0rd", "P@ssw0rd",
        }

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def toggle_visibility(self):
        self.visible = not self.visible
        self.entry.set_visibility(self.visible)
        self.toggle_btn.set_label("Gizle" if self.visible else "Goster")

    def analyze(self):
        pwd = self.entry.get_text()
        if not pwd:
            self.status_label.set_text("Sifre girin")
            return

        self.textbuffer.set_text("")
        self.log(f"[*] Analiz edilen sifre: {'*' * len(pwd)} ({len(pwd)} karakter)\n")

        self.log("=== KARAKTER ANALIZI ===")
        length = len(pwd)
        has_lower = any(c.islower() for c in pwd)
        has_upper = any(c.isupper() for c in pwd)
        has_digit = any(c.isdigit() for c in pwd)
        has_special = any(c in string.punctuation for c in pwd)
        has_space = " " in pwd

        types = 0
        if has_lower:
            types += 1
        if has_upper:
            types += 1
        if has_digit:
            types += 1
        if has_special:
            types += 1

        self.log(f"  Uzunluk: {length}")
        self.log(f"  Kucuk harf: {'VAR' if has_lower else 'YOK'}")
        self.log(f"  Buyuk harf: {'VAR' if has_upper else 'YOK'}")
        self.log(f"  Rakam: {'VAR' if has_digit else 'YOK'}")
        self.log(f"  Ozel karakter: {'VAR' if has_special else 'YOK'}")
        self.log(f"  Karakter turu: {types}/4\n")

        self.log("=== ENTROPI HESABI ===")
        pool = 0
        if has_lower:
            pool += 26
        if has_upper:
            pool += 26
        if has_digit:
            pool += 10
        if has_special:
            pool += 32
        if has_space:
            pool += 1

        if pool == 0:
            pool = 1

        entropy = length * math.log2(pool)
        self.log(f"  Karakter havuzu: {pool}")
        self.log(f"  Entropi: {entropy:.1f} bit\n")

        self.log("=== SIFRE GUCU ===")
        if pwd.lower() in self.common_passwords:
            self.log("  [!!!] COK ZAYIF - Yaygin sifreler listesinde!")
            strength = "Cok Zayif"
            color = "error"
            self.status_label.set_text("Cok Zayif - Bu sifre yaygin olarak kullaniliyor!")
        elif length < 8:
            strength = "Zayif"
            self.status_label.set_text("Zayif - En az 8 karakter gerekli")
        elif entropy < 40:
            strength = "Zayif"
            self.status_label.set_text(f"Zayif (entropi: {entropy:.0f} bit)")
        elif entropy < 60:
            strength = "Orta"
            self.status_label.set_text(f"Orta (entropi: {entropy:.0f} bit)")
        elif entropy < 80:
            strength = "Guclu"
            self.status_label.set_text(f"Guclu (entropi: {entropy:.0f} bit)")
        elif entropy < 100:
            strength = "Cok Guclu"
            self.status_label.set_text(f"Cok Guclu (entropi: {entropy:.0f} bit)")
        else:
            strength = "KIRILAMAZ"
            self.status_label.set_text(f"KIRILAMAZ! (entropi: {entropy:.0f} bit)")

        self.log(f"  Seviye: {strength}\n")

        self.log("=== BRUTE-FORCE SURESI ===")
        if pwd.lower() in self.common_passwords:
            self.log("  Aninda kirilir (yaygin sifre)")
        else:
            combos = pool ** length
            rates = [
                ("100 milyar/sn (GPU)", 100_000_000_000),
                ("10 milyar/sn (GPU)", 10_000_000_000),
                ("1 milyar/sn (GPU)", 1_000_000_000),
                ("100 milyon/sn (CPU)", 100_000_000),
            ]

            for rate_name, rate in rates:
                seconds = combos / rate
                time_str = self.format_time(seconds)
                if seconds < 1:
                    break
                self.log(f"  {rate_name}: {time_str}")

        self.log("")
        self.log("=== ONERILER ===")
        if length < 8:
            self.log("  - Sifre en az 8 karakter olmali (tercihen 12+)")
        if not has_upper:
            self.log("  - Buyuk harf ekleyin")
        if not has_lower:
            self.log("  - Kucuk harf ekleyin")
        if not has_digit:
            self.log("  - Rakam ekleyin")
        if not has_special:
            self.log("  - Ozel karakter ekleyin (!@# gibi)")
        if pwd.lower() in self.common_passwords:
            self.log("  - Bu sifre yaygin oldugu icin aninda kirilir")
            self.log("  - Tamamen farkli bir sifre secin!")
        if len(set(pwd)) < length * 0.5:
            self.log("  - Tekrar eden karakter fazla, cesitlendirin")

    def format_time(self, seconds):
        if seconds < 1:
            return "1 saniyeden kisa"
        if seconds < 60:
            return f"{seconds:.1f} saniye"
        if seconds < 3600:
            return f"{seconds / 60:.1f} dakika"
        if seconds < 86400:
            return f"{seconds / 3600:.1f} saat"
        if seconds < 31536000:
            return f"{seconds / 86400:.1f} gun"
        if seconds < 31536000 * 100:
            return f"{seconds / 31536000:.1f} yil"
        return f"{seconds / 31536000:.0f} yil (guvenli)"
