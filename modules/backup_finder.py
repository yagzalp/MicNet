import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests

SENSITIVE_PATHS = [
    ("/.git/config", "git", "[core]", "Git deposu acik!"),
    ("/.git/HEAD", "git", "ref:", "Git deposu acik!"),
    ("/.git/logs/HEAD", "git", None, "Git log acik!"),
    ("/.env", "env", "=", "Ortam degiskenleri (.env) acik!"),
    ("/.env.bak", "env", "=", "Ortam degiskenleri yedegi acik!"),
    ("/backup.zip", "zip", None, "Yedek zip dosyasi!"),
    ("/backup.tar.gz", "tar", None, "Yedek tar arsivi!"),
    ("/backup.sql", "sql", "CREATE TABLE|INSERT INTO", "Veritabani yedegi!"),
    ("/db.sql", "sql", "CREATE TABLE|INSERT INTO", "Veritabani yedegi!"),
    ("/database.sql", "sql", "CREATE TABLE|INSERT INTO", "Veritabani yedegi!"),
    ("/index.php.bak", "bak", "<?php", "Kaynak kodu yedegi!"),
    ("/index.html~", "bak", None, "Yedek dosya!"),
    ("/config.php.bak", "bak", "<?php", "Yapilandirma kodu!"),
    ("/config.old", "bak", None, "Eski yapilandirma!"),
    ("/wp-config.php.bak", "wp", "<?php", "WordPress yapilandirmasi!"),
    ("/.DS_Store", "mac", None, "Mac metadata dosyasi!"),
    ("/phpinfo.php", "phpinfo", "phpinfo()|PHP Version", "phpinfo sayfasi!"),
    ("/.htaccess", "apache", None, "Apache yapilandirmasi!"),
    ("/web.config", "iis", None, "IIS yapilandirmasi!"),
    ("/.ssh/id_rsa", "ssh", "BEGIN.*PRIVATE KEY", "SSH ozel anahtari!"),
    ("/.well-known/security.txt", "sec", None, "Güvenlik iletisim dosyasi (bilgi)"),
]

REDIRECT_CODES = {301, 302, 303, 307, 308}


class BackupFinderTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Yedek / Hassas Dosya Bulucu")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef sitede acikta birakilmis hassas dosyalari arar: .git deposu, .env, yedekler, SQL dump'lari, kaynak kodu, SSH anahtarlari. Her yol icin durum kodu ve icerik ipucu raporlanir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef URL (taban)")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com")
        self.entry.set_size_request(340, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Tara")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)
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

    def start_scan(self):
        url = self.entry.get_text().strip().rstrip("/")
        if not url:
            self.status_label.set_text("URL girin")
            return
        if not url.startswith(("http://", "https://")):
            self.status_label.set_text("URL http/https ile baslamali")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        session = requests.Session()
        session.verify = False
        session.headers["User-Agent"] = "Mozilla/5.0"

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, f"[*] {len(SENSITIVE_PATHS)} yol deneniyor\n")

        found = []
        for path, kind, sig, msg in SENSITIVE_PATHS:
            target = url + path
            try:
                r = session.get(target, timeout=8, allow_redirects=False)
                code = r.status_code
                if code == 200 or (code in REDIRECT_CODES and r.headers.get("Location")):
                    body = r.text[:4000]
                    hit = sig and __import__("re").search(sig, body)
                    interesting = hit or (sig is None and len(body) > 50 and "404" not in body[:200])
                    if code == 200 and (hit or (sig is None and interesting)):
                        found.append((path, kind, msg))
                        GLib.idle_add(self.log, f"  [BULUNDU!] {path}  (HTTP {code}) - {msg}")
                        if hit:
                            GLib.idle_add(self.log, f"    Kanit: {hit.group(0)[:80]}")
                    elif code in REDIRECT_CODES:
                        loc = r.headers.get("Location")
                        GLib.idle_add(self.log, f"  [YONLENDIRME] {path} -> {loc}")
                    elif code == 200 and sig and not hit:
                        GLib.idle_add(self.log, f"  [?] {path} (HTTP 200 ama bilinen imza yok, boyut {len(body)}")
                    else:
                        GLib.idle_add(self.log, f"  [-] {path} (HTTP {code})")
                else:
                    GLib.idle_add(self.log, f"  [-] {path} (HTTP {code})")
            except requests.exceptions.SSLError:
                GLib.idle_add(self.log, f"  [-] {path} (SSL hatasi)")
            except requests.exceptions.RequestException:
                GLib.idle_add(self.log, f"  [-] {path} (baglanti hatasi)")

        GLib.idle_add(self.log, "\n=== SONUC ===")
        if found:
            GLib.idle_add(self.log, f"  [!] {len(found)} hassas dosya/kaynak acikta!")
            for path, kind, msg in found:
                GLib.idle_add(self.log, f"  - {path}: {msg}")
            GLib.idle_add(self.log, "  Etki: kaynak kodu, sifre, DB kimlik bilgileri, git gecmisi sizabilir.")
            GLib.idle_add(self.log, "  Cozum: bu yollari web sunucusunda engelleyin (403), yedekleri erisilebilir dizinden kaldirin.")
        else:
            GLib.idle_add(self.log, "  [-] Yaygin hassas dosyalar bulunamadi.")
            GLib.idle_add(self.log, "  Not: ozel yollarda (sifreleme tabanli) fuzzing ile daha derin kontrol yapilabilir.")
        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
