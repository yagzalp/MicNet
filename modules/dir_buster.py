import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
from urllib.parse import urlparse, urljoin


class DirBusterTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Directory Buster")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef web sitesinde gizli dizin ve dosyalari bulmak icin brute-force yapar. Yaygin dizin/dosya isimlerini dener.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef")
        grid = Gtk.Grid()
        grid.set_border_width(16)
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        grid.attach(Gtk.Label(label="URL:"), 0, 0, 1, 1)
        self.entry = Gtk.Entry(placeholder_text="https://ornek.com")
        self.entry.set_size_request(350, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        grid.attach(self.entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Uzanti:"), 0, 1, 1, 1)
        self.ext_entry = Gtk.Entry(text="php,html,asp,jsp,txt,xml,zip,sql,json,ini,log,bak,old")
        self.ext_entry.set_size_request(350, 30)
        grid.attach(self.ext_entry, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Thread:"), 2, 0, 1, 1)
        self.thread_spin = Gtk.SpinButton.new_with_range(1, 20, 1)
        self.thread_spin.set_value(5)
        grid.attach(self.thread_spin, 3, 0, 1, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.scan_btn = Gtk.Button(label="Taramayi Baslat")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.scan_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop())
        self.stop_btn.get_style_context().add_class("destructive-action")
        hbox.pack_start(self.stop_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

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
        self.stopped = False

        self.wordlist = [
            "admin", "login", "wp-admin", "administrator", "panel", "cpanel",
            "backup", "backups", "dump", "sql", "database", "db",
            "config", "configuration", "config.php", "config.php.bak",
            "wp-config.php", "settings", "setup",
            "phpmyadmin", "pma", "mysql", "phpPgAdmin",
            ".git", ".svn", ".env", ".htaccess", ".htpasswd",
            "robots.txt", "sitemap.xml", "crossdomain.xml",
            "api", "v1", "v2", "rest", "graphql", "swagger",
            "test", "tests", "dev", "beta", "staging",
            "upload", "uploads", "download", "downloads",
            "images", "img", "css", "js", "assets", "static",
            "scripts", "includes", "classes", "lib",
            "server-status", "server-info", "status",
            "index", "index.html", "index.php", "default",
            "login.php", "register.php", "signup.php",
            "forgot.php", "reset.php", "profile.php",
            "user.php", "users.php", "account.php",
            "search.php", "contact.php", "about.php",
            "error.php", "404.php", "error_log",
            "tmp", "temp", "logs", "log", "error.log",
            "xmlrpc.php", "wp-login.php", "wp-content",
            "wp-includes", "wp-json", "wp-cron.php",
            "shell.php", "cmd.php", "exec.php", "info.php",
            "phpinfo.php", "test.php", "admin.php",
        ]

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
        self.stopped = False
        self.scan_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def stop(self):
        self.stopped = True
        self.status_label.set_text("Durduruldu")

    def scan(self, url):
        url = url.rstrip("/")
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        }

        exts = [e.strip() for e in self.ext_entry.get_text().split(",") if e.strip()]

        self.log(f"[*] Hedef: {url}")
        self.log(f"[*] Kelime sayisi: {len(self.wordlist)}")
        self.log(f"[*] Uzantilar: {', '.join(exts)}")
        self.log(f"[*] Basliyor...\n")

        found = 0
        total = len(self.wordlist) * (len(exts) + 1)
        done = 0

        try:
            base = requests.get(url, timeout=10, headers=headers)
            self.log(f"[+] Ana sayfa: {base.status_code} ({len(base.text)} byte)\n")
        except Exception as e:
            self.log(f"[-] Ana sayfa erisilemez: {e}\n")
            GLib.idle_add(self.finish)
            return

        for word in self.wordlist:
            if self.stopped:
                break

            paths_to_try = [f"/{word}"]
            for ext in exts:
                paths_to_try.append(f"/{word}.{ext}")

            for path in paths_to_try:
                if self.stopped:
                    break
                test_url = url.rstrip("/") + path
                try:
                    resp = requests.get(test_url, timeout=5, headers=headers)
                    done += 1
                    if resp.status_code == 200:
                        found += 1
                        self.log(f"  [200] {test_url} ({len(resp.text)} byte)")
                    elif resp.status_code == 301 or resp.status_code == 302:
                        loc = resp.headers.get("Location", "?")
                        self.log(f"  [{resp.status_code}] {test_url} -> {loc}")
                    elif resp.status_code == 401:
                        self.log(f"  [401] {test_url} (Yetkilendirme gerekli)")
                    elif resp.status_code == 403:
                        self.log(f"  [403] {test_url} (Yasak)")
                    elif resp.status_code == 500:
                        self.log(f"  [500] {test_url} (Sunucu hatasi)")
                    elif resp.status_code == 404:
                        continue
                    else:
                        self.log(f"  [{resp.status_code}] {test_url}")
                except requests.exceptions.ConnectionError:
                    done += 1
                    self.log(f"  [-] {test_url} Baglanti hatasi")
                except requests.exceptions.Timeout:
                    done += 1
                    self.log(f"  [-] {test_url} Zaman asimi")
                except Exception:
                    done += 1

            if done % 20 == 0:
                GLib.idle_add(self.status_label.set_text,
                    f"Taranıyor... {done}/{total} ({found} bulundu)")

        self.log("")
        if self.stopped:
            self.log(f"[!] Durduruldu. {found} dosya/dizin bulundu ({done}/{total})")
        else:
            self.log(f"[+] Tarama tamam. {found} dosya/dizin bulundu ({total} denendi)")
            if found == 0:
                self.log("[*] Hicbir sey bulunamadi - site guvenli veya kelime listesi yetersiz")

        GLib.idle_add(self.finish)

    def finish(self):
        self.running = False
        self.stopped = False
        self.scan_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.status_label.set_text("Tarama tamamlandi")
