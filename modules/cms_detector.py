import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
import re


class CmsDetectorTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="CMS Tespit Araci")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Web sitesinin kullandigi CMS'yi (WordPress, Joomla, Drupal, Magento vb.) tespit eder, versiyon ve eklenti bilgilerini gosterir.")
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
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com")
        self.entry.set_size_request(400, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Tespit Et")
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
        self.status_label.set_xalign(0)
        self.pack_start(self.status_label, False, False, 0)

        self.running = False

    def log(self, text):
        GLib.idle_add(self._append, text)

    def _append(self, text):
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
        self.status_label.set_text("CMS tespit ediliyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        }

        try:
            resp = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            html = resp.text
            h = resp.headers
            base = resp.url.rstrip("/")

            self.log(f"[+] Hedef: {url}")
            self.log(f"[+] Durum: {resp.status_code}")
            self.log(f"[+] Son URL: {base}\n")

            detected = []

            # WordPress
            if self.check_wp(base, html, h):
                detected.append("WordPress")
                self.log_cms("WordPress", base, html, h)

            # Joomla
            if self.check_joomla(base, html, h):
                detected.append("Joomla")
                self.log_cms_joomla(base, html, h)

            # Drupal
            if self.check_drupal(base, html, h):
                detected.append("Drupal")
                self.log_cms_drupal(base, html, h)

            # Magento
            if self.check_magento(base, html, h):
                detected.append("Magento")
                self.log_cms_magento(base, html, h)

            # Laravel
            if self.check_laravel(base, html, h):
                detected.append("Laravel")

            # ASP.NET
            if self.check_aspnet(base, html, h):
                detected.append("ASP.NET")

            self.log("=== SONUC ===")
            if detected:
                for cms in detected:
                    self.log(f"  [+] {cms}")
            else:
                self.log("  [-] Bilinen bir CMS tespit edilemedi")
                self.log("  Muhtemel: Ozel gelistirme, statik site, bilinmeyen CMS")

            meta_gen = re.search(r'<meta\s+name="[Gg]enerator"[^>]*content="([^"]+)"', html)
            if meta_gen:
                self.log(f"\n[+] Generator meta tag: {meta_gen.group(1)}")

        except Exception as e:
            self.log(f"[-] Hata: {e}")

        GLib.idle_add(self.finish)

    def check_wp(self, base, html, h):
        checks = [
            "/wp-content/" in html,
            "/wp-includes/" in html,
            "/wp-json/" in html,
            "wp-emoji-release" in html,
            "wordpress" in html.lower(),
            "WordPress" in h.get("X-Powered-By", ""),
            "WordPress" in h.get("X-Generator", ""),
            "wp-login.php" in html,
        ]
        return any(checks)

    def log_cms(self, name, base, html, h):
        self.log(f"=== {name} ===")
        ver = re.search(r'<meta\s+name="[Gg]enerator"[^>]*content="WordPress\s*([^"]+)"', html)
        if ver:
            self.log(f"  Versiyon: {ver.group(1)}")
            major = ver.group(1).split(".")
            if int(major[0]) < 5:
                self.log(f"  [!] Eski versiyon - guvenlik riski!")
        else:
            self.log(f"  Versiyon: Gizli (iyi guvenlik)")
        self.log(f"  Tema: wp-content/themes/")
        self.log(f"  Admin: {base}/wp-admin/")
        self.log(f"  XML-RPC: {base}/xmlrpc.php")

        # check vulnerabilities
        self.log(f"\n  Zafiyet Kontrolu:")
        wp_paths = [
            ("/wp-admin/", "Admin paneli acik"),
            ("/xmlrpc.php", "XML-RPC (brute force riski)"),
            ("/wp-json/", "REST API acik"),
            ("/wp-content/debug.log", "Debug log acik"),
            ("/readme.html", "Readme acik (versiyon bilgisi)"),
            ("/wp-config.php.bak", "Konfigurasyon yedegi"),
            ("/wp-content/uploads/", "Uploads dizini"),
        ]
        for path, risk in wp_paths:
            try:
                r = requests.get(base + path, timeout=5, headers={
                    "User-Agent": "Mozilla/5.0"
                })
                if r.status_code not in (403, 404):
                    self.log(f"    [{r.status_code}] {risk}: {path}")
            except Exception:
                pass

    def check_joomla(self, base, html, h):
        checks = [
            "/components/" in html,
            "/modules/" in html,
            "/templates/" in html,
            "/media/system/js/" in html,
            "joomla" in html.lower(),
            "Joomla" in h.get("X-Generator", ""),
            "Joomla" in h.get("X-Content-Encoded-By", ""),
        ]
        return any(checks)

    def log_cms_joomla(self, base, html, h):
        self.log(f"=== Joomla ===")
        ver = re.search(r'<meta\s+name="[Gg]enerator"[^>]*content="Joomla!\s*([^"]+)"', html)
        if ver:
            self.log(f"  Versiyon: {ver.group(1)}")
        else:
            self.log(f"  Versiyon: Gizli")
        self.log(f"  Admin: {base}/administrator/")

    def check_drupal(self, base, html, h):
        checks = [
            "/sites/" in html,
            "/core/" in html,
            "Drupal" in h.get("X-Generator", ""),
            "drupal" in html.lower(),
            'drupal.js' in html,
            'Drupal.settings' in html,
        ]
        return any(checks)

    def log_cms_drupal(self, base, html, h):
        self.log(f"=== Drupal ===")
        ver = re.search(r'Drupal\s*(\d+\.\d+)', html)
        if ver:
            self.log(f"  Versiyon: {ver.group(1)}")
        self.log(f"  Admin: {base}/user/login/")

    def check_magento(self, base, html, h):
        checks = [
            "Magento" in h.get("X-Magento-*", ""),
            "Magento" in h.get("X-Powered-By", ""),
            "Magento" in html,
            "/static/version" in html,
            "mage/calendar.css" in html,
            "Mage.Cookies" in html,
        ]
        return any(checks)

    def log_cms_magento(self, base, html, h):
        self.log(f"=== Magento ===")
        ver = re.search(r'Magento[^0-9]*(\d+\.\d+)', html)
        if ver:
            self.log(f"  Versiyon: {ver.group(1)}")
        self.log(f"  Admin: {base}/admin/")

    def check_laravel(self, base, html, h):
        checks = [
            "Laravel" in h.get("X-Powered-By", ""),
            "laravel" in html.lower(),
            "csrf-token" in html,
            "laravel_session" in html,
            "Laravel" in h.get("Set-Cookie", ""),
        ]
        return any(checks)

    def check_aspnet(self, base, html, h):
        checks = [
            "ASP.NET" in h.get("X-Powered-By", ""),
            "__VIEWSTATE" in html,
            "__EVENTVALIDATION" in html,
            "aspnet" in html.lower(),
        ]
        return any(checks)

    def finish(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("CMS tespit tamamlandi")
