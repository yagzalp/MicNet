import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GLib
import threading
import hashlib
import os


class FileHashTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="DOSYA HASH DOGRULAMA")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bir dosyanin MD5, SHA-1 ve SHA-256 ozetlerini hesaplar ve isterseniz beklenen bir hash ile karsilastirir. Dosyanin bozulup bozulmadigini veya degistirilip degistirilmediigini dogrulamak icin kullanilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Dosya Secin")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.file_label = Gtk.Label(label="Dosya secilmedi")
        self.file_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.file_label.set_size_request(300, -1)
        hbox.pack_start(self.file_label, False, False, 0)
        self.pick_btn = Gtk.Button(label="Dosya Sec...")
        self.pick_btn.connect("clicked", lambda _: self.pick_file())
        hbox.pack_start(self.pick_btn, False, False, 0)
        input_box.pack_start(hbox, False, False, 0)

        hbox2 = Gtk.Box(spacing=8)
        hbox2.set_halign(Gtk.Align.CENTER)
        hbox2.pack_start(Gtk.Label(label="Beklenen hash:"), False, False, 0)
        self.expected_entry = Gtk.Entry(placeholder_text="istege bagli - md5/sha1/sha256")
        self.expected_entry.set_size_request(320, 30)
        hbox2.pack_start(self.expected_entry, False, False, 0)
        self.hash_btn = Gtk.Button(label="Hash Hesapla")
        self.hash_btn.connect("clicked", lambda _: self.start_hash())
        self.hash_btn.get_style_context().add_class("suggested-action")
        hbox2.pack_start(self.hash_btn, False, False, 0)
        input_box.pack_start(hbox2, False, False, 0)

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
        self.selected_file = None

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def pick_file(self):
        dialog = Gtk.FileChooserDialog(title="Dosya Sec", transient_for=self.get_toplevel(),
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            self.selected_file = dialog.get_filename()
            self.file_label.set_text(os.path.basename(self.selected_file))
            self.log(f"[*] Secilen dosya: {self.selected_file}")
        dialog.destroy()

    def start_hash(self):
        if not self.selected_file:
            self.status_label.set_text("Once dosya secin")
            return
        if self.running:
            return
        self.running = True
        self.hash_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Hesaplaniyor...")
        thread = threading.Thread(target=self.compute_hash, daemon=True)
        thread.start()

    def compute_hash(self):
        path = self.selected_file
        try:
            size = os.path.getsize(path)
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(1 << 20)
                    if not chunk:
                        break
                    md5.update(chunk)
                    sha1.update(chunk)
                    sha256.update(chunk)

            GLib.idle_add(self.log, f"[*] Dosya: {path}")
            GLib.idle_add(self.log, f"[*] Boyut: {size:,} byte ({size/1024/1024:.2f} MB)\n")
            GLib.idle_add(self.log, f"MD5    : {md5.hexdigest()}")
            GLib.idle_add(self.log, f"SHA-1  : {sha1.hexdigest()}")
            GLib.idle_add(self.log, f"SHA-256: {sha256.hexdigest()}")

            expected = self.expected_entry.get_text().strip().lower()
            if expected:
                GLib.idle_add(self.log, "\n=== KARSILASTIRMA ===")
                if expected == md5.hexdigest():
                    GLib.idle_add(self.log, f"  [OK] MD5 ile eslesiyor - dosya dogrulanmis")
                elif expected == sha1.hexdigest():
                    GLib.idle_add(self.log, f"  [OK] SHA-1 ile eslesiyor - dosya dogrulanmis")
                elif expected == sha256.hexdigest():
                    GLib.idle_add(self.log, f"  [OK] SHA-256 ile eslesiyor - dosya dogrulanmis")
                else:
                    GLib.idle_add(self.log, "  [!!] Hicbir hash eslesmedi - dosya degistirilmis veya beklenen hash yanlis")
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Hata: {e}")
        GLib.idle_add(self.finish_hash)

    def finish_hash(self):
        self.running = False
        self.hash_btn.set_sensitive(True)
        self.status_label.set_text("Hash hesaplandi")
