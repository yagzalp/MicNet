import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import hashlib
import hmac


class HashToolsTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Hash Araclari")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Metinlerin hash degerlerini hesaplar (MD5, SHA, BLAKE2, HMAC) veya MD5 hashlerini common password listesiyle kirmaya calisir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        nb = Gtk.Notebook()
        nb.set_tab_pos(Gtk.PositionType.TOP)

        nb.append_page(self.build_hash_tab(), Gtk.Label(label="Hash Olustur"))
        nb.append_page(self.build_hmac_tab(), Gtk.Label(label="HMAC"))
        nb.append_page(self.build_crack_tab(), Gtk.Label(label="Hash Kir (MD5)"))
        self.pack_start(nb, True, True, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

    def build_hash_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.hash_input = Gtk.Entry(placeholder_text="Metin girin...")
        self.hash_input.set_size_request(300, 30)
        self.hash_input.connect("activate", lambda _: self.do_hash())
        hbox.pack_start(self.hash_input, False, False, 0)
        self.hash_btn = Gtk.Button(label="Hashle")
        self.hash_btn.connect("clicked", lambda _: self.do_hash())
        self.hash_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.hash_btn, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        self.hash_liststore = Gtk.ListStore(str, str)
        self.hash_treeview = Gtk.TreeView(model=self.hash_liststore)

        for title_text, idx in [("Algoritma", 0), ("Hash Degeri", 1)]:
            col = Gtk.TreeViewColumn(title_text, Gtk.CellRendererText(), text=idx)
            col.set_resizable(True)
            self.hash_treeview.append_column(col)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.hash_treeview)
        vbox.pack_start(sw, True, True, 0)

        return vbox

    def build_hmac_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(16)

        hbox1 = Gtk.Box(spacing=8)
        hbox1.set_halign(Gtk.Align.CENTER)
        hbox1.pack_start(Gtk.Label(label="Metin:"), False, False, 0)
        self.hmac_input = Gtk.Entry(placeholder_text="Metin girin...")
        self.hmac_input.set_size_request(250, 30)
        self.hmac_input.connect("activate", lambda _: self.do_hmac())
        hbox1.pack_start(self.hmac_input, False, False, 0)
        vbox.pack_start(hbox1, False, False, 0)

        hbox2 = Gtk.Box(spacing=8)
        hbox2.set_halign(Gtk.Align.CENTER)
        hbox2.pack_start(Gtk.Label(label="Anahtar:"), False, False, 0)
        self.hmac_key = Gtk.Entry(placeholder_text="Gizli anahtar...")
        self.hmac_key.set_size_request(250, 30)
        hbox2.pack_start(self.hmac_key, False, False, 0)
        vbox.pack_start(hbox2, False, False, 0)

        hbox3 = Gtk.Box(spacing=8)
        hbox3.set_halign(Gtk.Align.CENTER)
        self.hmac_btn = Gtk.Button(label="HMAC Olustur")
        self.hmac_btn.connect("clicked", lambda _: self.do_hmac())
        self.hmac_btn.get_style_context().add_class("suggested-action")
        hbox3.pack_start(self.hmac_btn, False, False, 0)
        vbox.pack_start(hbox3, False, False, 0)

        self.hmac_liststore = Gtk.ListStore(str, str)
        self.hmac_treeview = Gtk.TreeView(model=self.hmac_liststore)
        for title_text, idx in [("Algoritma", 0), ("HMAC Degeri", 1)]:
            col = Gtk.TreeViewColumn(title_text, Gtk.CellRendererText(), text=idx)
            col.set_resizable(True)
            self.hmac_treeview.append_column(col)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.hmac_treeview)
        vbox.pack_start(sw, True, True, 0)

        return vbox

    def build_crack_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.crack_input = Gtk.Entry(placeholder_text="MD5 hash girin...")
        self.crack_input.set_size_request(300, 30)
        self.crack_input.connect("activate", lambda _: self.do_crack())
        hbox.pack_start(self.crack_input, False, False, 0)
        self.crack_btn = Gtk.Button(label="Kir")
        self.crack_btn.connect("clicked", lambda _: self.do_crack())
        self.crack_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.crack_btn, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        self.crack_textview = Gtk.TextView()
        self.crack_textview.set_editable(False)
        self.crack_textview.set_monospace(True)
        self.crack_textbuffer = self.crack_textview.get_buffer()
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_vexpand(True)
        sw.add(self.crack_textview)
        vbox.pack_start(sw, True, True, 0)

        self.status_label2 = Gtk.Label(label="")
        vbox.pack_start(self.status_label2, False, False, 0)

        return vbox

    def do_hash(self):
        text = self.hash_input.get_text().strip()
        if not text:
            self.status_label.set_text("Metin girin")
            return
        self.hash_liststore.clear()
        data = text.encode("utf-8")

        algos = [
            ("MD5", hashlib.md5(data).hexdigest()),
            ("SHA-1", hashlib.sha1(data).hexdigest()),
            ("SHA-224", hashlib.sha224(data).hexdigest()),
            ("SHA-256", hashlib.sha256(data).hexdigest()),
            ("SHA-384", hashlib.sha384(data).hexdigest()),
            ("SHA-512", hashlib.sha512(data).hexdigest()),
            ("SHA3-224", hashlib.sha3_224(data).hexdigest()),
            ("SHA3-256", hashlib.sha3_256(data).hexdigest()),
            ("SHA3-384", hashlib.sha3_384(data).hexdigest()),
            ("SHA3-512", hashlib.sha3_512(data).hexdigest()),
            ("BLAKE2b", hashlib.blake2b(data).hexdigest()),
            ("BLAKE2s", hashlib.blake2s(data).hexdigest()),
        ]
        for name, hval in algos:
            self.hash_liststore.append([name, hval])
        self.status_label.set_text(f"12 hash olusturuldu ({len(text)} karakter)")

    def do_hmac(self):
        text = self.hmac_input.get_text().strip()
        key = self.hmac_key.get_text().strip()
        if not text:
            self.status_label.set_text("Metin girin")
            return
        if not key:
            self.status_label.set_text("Anahtar girin")
            return
        self.hmac_liststore.clear()
        data = text.encode("utf-8")
        k = key.encode("utf-8")

        algos = [
            ("HMAC-MD5", hashlib.md5),
            ("HMAC-SHA1", hashlib.sha1),
            ("HMAC-SHA256", hashlib.sha256),
            ("HMAC-SHA512", hashlib.sha512),
        ]
        for name, func in algos:
            h = hmac.new(k, data, func).hexdigest()
            self.hmac_liststore.append([name, h])
        self.status_label.set_text("HMAC degerleri olusturuldu")

    def do_crack(self):
        target = self.crack_input.get_text().strip().lower()
        if not target:
            self.status_label2.set_text("MD5 hash girin")
            return
        if len(target) != 32:
            self.status_label2.set_text("Gecerli bir MD5 hash girin (32 karakter)")
            return

        self.crack_btn.set_sensitive(False)
        self.crack_textbuffer.set_text("")
        self.status_label2.set_text("Kirmaya calisiyor...")
        thread = threading.Thread(target=self.crack, args=(target,), daemon=True)
        thread.start()

    def crack(self, target):
        common = [
            "123456", "password", "12345678", "qwerty", "123456789",
            "12345", "1234", "111111", "1234567", "sunshine",
            "qwerty123", "admin", "letmein", "welcome", "monkey",
            "dragon", "master", "hunter", "abc123", "passw0rd",
            "iloveyou", "trustno1", "batman", "superman", "princess",
            "shadow", "starwars", "football", "baseball", "soccer",
            "michael", "jennifer", "joshua", "andrew", "matthew",
            "thomas", "charlie", "george", "william", "joseph",
            "sifre", "parola", "123", "123123", "qwertyuiop",
            "asdfgh", "zxcvbn", "1q2w3e4r", "zaq1xsw2", "test",
            "password123", "Password", "P@ssw0rd", "pass123",
            "qwerty12345", "Qwerty123", "qazwsx", "qwerty1",
            "abcd1234", "123456789a", "a123456", "123qweasd",
            "987654321", "qwertyuiop123", "1qaz2wsx", "3edc4rfv",
            "!@#$%^&*", "passw0rd!", "admin123", "root", "toor",
            "guest", "user", "default", "temp123", "changeme",
        ]
        found = None
        for word in common:
            if hashlib.md5(word.encode()).hexdigest() == target:
                found = word
                break

        GLib.idle_add(self.crack_textbuffer.set_text, "")
        if found:
            GLib.idle_add(self.crack_textbuffer.insert,
                          self.crack_textbuffer.get_end_iter(),
                          f"[+] SIFRE BULUNDU: {found}\n\n"
                          f"    Hash: {target}\n"
                          f"    Sifre: {found}\n")
            GLib.idle_add(self.status_label2.set_text, f"Sifre bulundu: {found}")
        else:
            GLib.idle_add(self.crack_textbuffer.insert,
                          self.crack_textbuffer.get_end_iter(),
                          f"[-] Sifre bulunamadi\n\n"
                          f"    Hash: {target}\n\n"
                          f"[*] Common password listesinde yok.\n"
                          f"[*] Daha buyuk bir sozluk icin rockyou.txt kullanabilirsiniz.\n")
            GLib.idle_add(self.status_label2.set_text, "Sifre bulunamadi")

        GLib.idle_add(self.crack_btn.set_sensitive, True)
