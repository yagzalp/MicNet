import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import secrets
import string
import pyperclip


class PasswordGenTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Sifre Olusturucu")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Guclu ve rastgele sifreler olusturur. Uzunluk, karakter turu ve adet ayarlariyla ozellestirilebilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Ayarlar")
        grid = Gtk.Grid()
        grid.set_border_width(16)
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        grid.attach(Gtk.Label(label="Uzunluk:"), 0, 0, 1, 1)
        self.length_spin = Gtk.SpinButton.new_with_range(4, 128, 1)
        self.length_spin.set_value(16)
        grid.attach(self.length_spin, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Sayi:"), 2, 0, 1, 1)
        self.digits_check = Gtk.CheckButton()
        self.digits_check.set_active(True)
        grid.attach(self.digits_check, 3, 0, 1, 1)

        grid.attach(Gtk.Label(label="Kucuk Harf:"), 0, 1, 1, 1)
        self.lower_check = Gtk.CheckButton()
        self.lower_check.set_active(True)
        grid.attach(self.lower_check, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Buyuk Harf:"), 2, 1, 1, 1)
        self.upper_check = Gtk.CheckButton()
        self.upper_check.set_active(True)
        grid.attach(self.upper_check, 3, 1, 1, 1)

        grid.attach(Gtk.Label(label="Ozel Karakter:"), 0, 2, 1, 1)
        self.special_check = Gtk.CheckButton()
        self.special_check.set_active(True)
        grid.attach(self.special_check, 1, 2, 1, 1)

        grid.attach(Gtk.Label(label="Adet:"), 2, 2, 1, 1)
        self.count_spin = Gtk.SpinButton.new_with_range(1, 50, 1)
        self.count_spin.set_value(5)
        grid.attach(self.count_spin, 3, 2, 1, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.gen_btn = Gtk.Button(label="Sifre Olustur")
        self.gen_btn.connect("clicked", lambda _: self.generate())
        self.gen_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.gen_btn, False, False, 0)
        self.copy_btn = Gtk.Button(label="Kopyala")
        self.copy_btn.set_sensitive(False)
        self.copy_btn.connect("clicked", lambda _: self.copy())
        hbox.pack_start(self.copy_btn, False, False, 0)
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

        self.last_passwords = []

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def generate(self):
        length = int(self.length_spin.get_value())
        count = int(self.count_spin.get_value())

        chars = ""
        if self.lower_check.get_active():
            chars += string.ascii_lowercase
        if self.upper_check.get_active():
            chars += string.ascii_uppercase
        if self.digits_check.get_active():
            chars += string.digits
        if self.special_check.get_active():
            chars += string.punctuation

        if not chars:
            self.status_label.set_text("En az bir karakter turu secin")
            return

        self.textbuffer.set_text("")
        self.last_passwords = []

        for i in range(count):
            pwd = "".join(secrets.choice(chars) for _ in range(length))
            self.last_passwords.append(pwd)
            self.log(f"{i+1:2d}. {pwd}")

        self.status_label.set_text(f"{count} sifre olusturuldu (uzunluk: {length})")
        self.copy_btn.set_sensitive(True)

    def copy(self):
        if self.last_passwords:
            try:
                pyperclip.copy(self.last_passwords[0])
                self.status_label.set_text("Ilk sifre panoya kopyalandi")
            except Exception:
                self.status_label.set_text("Pano erisimi yok, sifreyi elle kopyalayin")
