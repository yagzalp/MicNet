import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests


class RobotsAnalyzerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="robots.txt & Guvenlik Dosyalari Analizi")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Sitenin robots.txt, security.txt, sitemap.xml ve humans.txt dosyalarini indirir, yasaklanan dizinleri ve sizdirilan bilgileri listeler. Guvenlik testlerinde hedef yuzeyini cikarir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef URL")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek.com")
        self.entry.set_size_request(350, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Analiz Et")
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
        url = self.entry.get_text().strip()
        if not url:
            self.status_label.set_text("URL girin")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.entry.set_text(url)
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Analiz ediliyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def fetch(self, url, timeout=10):
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        return None

    def scan(self, url):
        base = url.rstrip("/")
        host = base.split("://", 1)[1].split("/")[0]

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, "")

        GLib.idle_add(self.log, "=== robots.txt ===")
        robots = self.fetch(base + "/robots.txt")
        if robots is None:
            GLib.idle_add(self.log, "  [-] robots.txt yok veya erisilemedi")
        else:
            GLib.idle_add(self.log, "  --- icerik (ilk 80 satir) ---")
            lines = robots.splitlines()
            for line in lines[:80]:
                GLib.idle_add(self.log, f"  {line}")
            if len(lines) > 80:
                GLib.idle_add(self.log, f"  ... {len(lines)-80} satir daha")
            GLib.idle_add(self.log, "")
            GLib.idle_add(self.log, "  --- ilginc yollar ---")
            disallowed = []
            for line in lines:
                line = line.strip()
                if line.lower().startswith("disallow"):
                    path = line.split(":", 1)[1].strip() if ":" in line else ""
                    if path and not path.startswith("/"):
                        path = "/" + path
                    disallowed.append(path)
            for path in disallowed:
                GLib.idle_add(self.log, f"    Yasak: {path}")
            sensitive = ["admin", "backup", "config", ".git", ".env", "wp-admin",
                         "login", "panel", "phpmyadmin", "database", "sql", "private",
                         "internal", "cgi-bin", "shell", "password", "dashboard"]
            found = []
            for path in disallowed:
                low = path.lower()
                if any(s in low for s in sensitive):
                    found.append(path)
            if found:
                GLib.idle_add(self.log, "  [!] HASSAS YOLLAR BULUNDU:")
                for f in found:
                    GLib.idle_add(self.log, f"      - {f}")
            else:
                GLib.idle_add(self.log, "  [*] Ayrik hassas yol yok")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== security.txt ===")
        sec = self.fetch(base + "/.well-known/security.txt")
        if sec is None:
            sec = self.fetch(base + "/security.txt")
        if sec is None:
            GLib.idle_add(self.log, "  [-] security.txt yok")
        else:
            GLib.idle_add(self.log, "  --- icerik ---")
            for line in sec.splitlines():
                GLib.idle_add(self.log, f"  {line}")
            GLib.idle_add(self.log, "  [+] Guvenlik iletisim politikasi mevcut (sorumlu ifsa icin iyi pratiktir)")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== sitemap.xml ===")
        sitemap = self.fetch(base + "/sitemap.xml")
        if sitemap is None:
            GLib.idle_add(self.log, "  [-] sitemap.xml yok")
        else:
            import re
            urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
            GLib.idle_add(self.log, f"  [+] {len(urls)} URL bulundu (ilk 30):")
            for u in urls[:30]:
                GLib.idle_add(self.log, f"    - {u}")
            if len(urls) > 30:
                GLib.idle_add(self.log, f"    ... ve {len(urls)-30} daha")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== humans.txt ===")
        humans = self.fetch(base + "/humans.txt")
        if humans is None:
            GLib.idle_add(self.log, "  [-] humans.txt yok")
        else:
            GLib.idle_add(self.log, "  --- icerik (ilk 40 satir) ---")
            for line in humans.splitlines()[:40]:
                GLib.idle_add(self.log, f"  {line}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== OZET ===")
        GLib.idle_add(self.log, "  [*] robots.txt: hedef yuzeyini (dizin yapisi, panel adlari) sizdirir")
        GLib.idle_add(self.log, "  [*] Bulunan yollar dirbust gibi tarayicilarla oncelikli denenmeli")

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Analiz tamamlandi")
