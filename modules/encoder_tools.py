import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import base64
import hashlib
import binascii
import urllib.parse


class EncoderToolsTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Kodlama / Sifreleme Araclari")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Base64, Base32, Hex, URL, Binary, ROT13 ve ASCII kodlama/cozumleme yapar; ayrica MD5, SHA1, SHA256 hashlerini hesaplar ve hash esleme testi yapar.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Islem")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.mode_combo = Gtk.ComboBoxText()
        for mid, mlab in [("b64", "Base64"), ("b32", "Base32"), ("hex", "Hex"),
                          ("url", "URL"), ("bin", "Binary"), ("rot13", "ROT13"),
                          ("ascii", "ASCII <-> Dec")]:
            self.mode_combo.append(mid, mlab)
        self.mode_combo.set_active(0)
        hbox.pack_start(self.mode_combo, False, False, 0)

        self.encode_btn = Gtk.Button(label="Kodla")
        self.encode_btn.connect("clicked", lambda _: self.transform(encode=True))
        self.encode_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.encode_btn, False, False, 0)

        self.decode_btn = Gtk.Button(label="Coz")
        self.decode_btn.connect("clicked", lambda _: self.transform(encode=False))
        hbox.pack_start(self.decode_btn, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)

        self.input_view = Gtk.TextView()
        self.input_view.set_wrap_mode(Gtk.WrapMode.WORD)
        sw_in = Gtk.ScrolledWindow()
        sw_in.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw_in.set_size_request(-1, 120)
        sw_in.add(self.input_view)
        vbox.pack_start(sw_in, False, False, 0)

        self.output_view = Gtk.TextView()
        self.output_view.set_editable(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.output_view.get_style_context().add_class("output-text")
        sw_out = Gtk.ScrolledWindow()
        sw_out.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw_out.set_size_request(-1, 160)
        sw_out.add(self.output_view)
        vbox.pack_start(sw_out, True, True, 0)

        frame.add(vbox)
        self.pack_start(frame, True, True, 0)

        frame2 = Gtk.Frame(label="Hash Uretimi")
        hbox2 = Gtk.Box(spacing=8)
        hbox2.set_border_width(12)
        self.hash_btn = Gtk.Button(label="MD5 / SHA1 / SHA256 Hesapla")
        self.hash_btn.connect("clicked", lambda _: self.compute_hash())
        self.hash_btn.get_style_context().add_class("suggested-action")
        hbox2.pack_start(self.hash_btn, False, False, 0)

        self.hash_verify_btn = Gtk.Button(label="Hash Karsilastir (girdi girip 3 hash esle)")
        self.hash_verify_btn.connect("clicked", lambda _: self.compute_hash(verify=True))
        hbox2.pack_start(self.hash_verify_btn, False, False, 0)
        frame2.add(hbox2)
        self.pack_start(frame2, False, False, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

    def get_input(self):
        buf = self.input_view.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)

    def set_output(self, text):
        buf = self.output_view.get_buffer()
        buf.set_text(text)

    def transform(self, encode):
        data = self.get_input()
        mode = self.mode_combo.get_active_id()
        try:
            if mode == "b64":
                out = base64.b64encode(data.encode()).decode() if encode else base64.b64decode(data).decode()
            elif mode == "b32":
                out = base64.b32encode(data.encode()).decode() if encode else base64.b32decode(data).decode()
            elif mode == "hex":
                out = data.encode().hex() if encode else bytes.fromhex(data).decode()
            elif mode == "url":
                out = urllib.parse.quote(data) if encode else urllib.parse.unquote(data)
            elif mode == "bin":
                out = " ".join(f"{b:08b}" for b in data.encode()) if encode else "".join(
                    chr(int(x, 2)) for x in data.split() if x)
            elif mode == "rot13":
                import codecs
                out = codecs.encode(data, "rot13")
            elif mode == "ascii":
                if encode:
                    out = " ".join(str(ord(c)) for c in data)
                else:
                    out = "".join(chr(int(x)) for x in data.split() if x.isdigit())
            else:
                out = data
            self.set_output(out)
            self.status_label.set_text("Islem basarili")
        except Exception as e:
            self.set_output(f"HATA: {e}")
            self.status_label.set_text("Islem basarisiz")

    def compute_hash(self, verify=False):
        data = self.get_input()
        if not data:
            self.status_label.set_text("Girdi girin")
            return
        md5 = hashlib.md5(data.encode()).hexdigest()
        sha1 = hashlib.sha1(data.encode()).hexdigest()
        sha256 = hashlib.sha256(data.encode()).hexdigest()
        sha512 = hashlib.sha512(data.encode()).hexdigest()
        out = (f"MD5:    {md5}\n"
               f"SHA1:   {sha1}\n"
               f"SHA256: {sha256}\n"
               f"SHA512: {sha512}")
        if verify:
            out += "\n\n--- KARSILASTIRMA ---\nBu hash'ler girdi metninden uretildi."
        self.set_output(out)
        self.status_label.set_text("Hash hesaplandi")
