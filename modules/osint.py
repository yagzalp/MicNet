import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
import socket
import re
from modules.http_utils import status_str, port_str


class OsintTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="OSINT")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Email, kullanici adi, domain veya IP uzerinden acik kaynak istihbarati. DNS, web, port ve sosyal medya kontrolleri yapar.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Sorgu")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="email / kullanici_adi / domain / IP")
        self.entry.set_size_request(350, 30)
        self.entry.connect("activate", lambda _: self.search())
        self.search_btn = Gtk.Button(label="Ara")
        self.search_btn.connect("clicked", lambda _: self.search())
        self.search_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.entry, False, False, 0)
        hbox.pack_start(self.search_btn, False, False, 0)
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

    def search(self):
        query = self.entry.get_text().strip()
        if not query or self.running:
            return
        self.running = True
        self.search_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Araniyor...")
        thread = threading.Thread(target=self.do_search, args=(query,), daemon=True)
        thread.start()

    def do_search(self, query):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

            is_email = "@" in query and "." in query.split("@")[1]
            is_ip = re.match(r'^\d+\.\d+\.\d+\.\d+$', query)
            is_domain = "." in query and not is_email and not is_ip

            self.log(f"[*] Sorgu: {query}")
            self.log(f"[*] Tur: {'E-posta' if is_email else 'IP' if is_ip else 'Domain' if is_domain else 'Kullanici adi'}")
            self.log("")

            if is_email:
                self.analyze_email(query, headers)
            elif is_ip:
                self.analyze_ip(query, headers)
            elif is_domain:
                self.analyze_domain(query, headers)
            else:
                self.analyze_username(query, headers)

            self.log("")
            self.log("=== KAYNAKLAR ===")
            self.log(f"  Shodan: https://www.shodan.io/search?query={query}")
            if is_email:
                self.log(f"  HIBP: https://haveibeenpwned.com/account/{query}")
            if is_domain or is_email:
                dom = query.split("@")[1] if is_email else query
                self.log(f"  CRT: https://crt.sh/?q={dom}")
            self.log(f"  Google: https://google.com/search?q={query}")

        except Exception as e:
            self.log(f"[-] HATA: {e}")

        GLib.idle_add(self.finish)

    def analyze_email(self, email, headers):
        domain = email.split("@")[1]
        username = email.split("@")[0]

        self.log("=== DNS ===")
        try:
            ip = socket.gethostbyname(domain)
            self.log(f"  IP: {ip}")
            try:
                h, a, ip_list = socket.gethostbyaddr(ip)
                self.log(f"  Host: {h}")
            except Exception:
                pass
        except Exception:
            self.log("  DNS cozulemedi")

        self.log("")
        self.log("=== WEB ===")
        for scheme in ["https://", "http://"]:
                try:
                    r = requests.get(f"{scheme}{domain}", timeout=5, headers=headers)
                    self.log(f"  {scheme}{domain} -> {status_str(r.status_code)}")
                    server = r.headers.get("Server", r.headers.get("server", "?"))
                    self.log(f"  Sunucu: {server}")
                    break
                except Exception:
                    continue

        self.log("")
        self.log("=== SIZINTI KONTROLU ===")
        try:
            import hashlib
            sha1 = hashlib.sha1(email.encode()).hexdigest().upper()
            r = requests.get(f"https://api.pwnedpasswords.com/range/{sha1[:5]}", timeout=5, headers=headers)
            if r.status_code == 200:
                for line in r.text.split("\n"):
                    if line.startswith(sha1[5:]):
                        count = int(line.split(":")[1].strip())
                        self.log(f"  [!] {count} sizintida bulundu!")
                        break
                else:
                    self.log("  [-] Bilinen sizinti yok")
            else:
                self.log("  [-] API erisilemez")
        except Exception:
            self.log("  [-] API sorgulanamadi")

        self.log("")
        self.log("=== SOSYAL MEDYA ===")
        self.check_platforms(username)

    def analyze_username(self, username, headers):
        self.log("=== SOSYAL MEDYA ===")
        self.check_platforms(username)

        self.log("")
        self.log("=== WEB ARAMA ===")
        try:
            r = requests.get(f"https://www.google.com/search?q=%22{username}%22",
                             timeout=5, headers=headers)
            matches = re.findall(r'<em>([^<]*)</em>', r.text)
            self.log(f"  Google: {len(matches)}+ sonuc")
        except Exception:
            self.log("  Google: erisilemedi")

    def analyze_domain(self, domain, headers):
        self.log("=== DNS ===")
        try:
            ip = socket.gethostbyname(domain)
            self.log(f"  IP: {ip}")
            try:
                nm = socket.gethostbyaddr(ip)
                self.log(f"  Host: {nm[0]}")
            except Exception:
                pass
        except Exception:
            self.log("  Cozulemedi")

        self.log("")
        self.log("=== WEB ===")
        for scheme in ["https://", "http://"]:
            try:
                r = requests.get(f"{scheme}{domain}", timeout=5, headers=headers, allow_redirects=True)
                self.log(f"  {scheme}{domain} -> {status_str(r.status_code)}")
                server = r.headers.get("Server", "?")
                title = re.search(r'<title>([^<]+)</title>', r.text)
                t = f" - Title: {title.group(1)[:50]}" if title else ""
                self.log(f"  Sunucu: {server} | {len(r.text)} byte{t}")
                cf = "cloudflare" in server.lower() or "CF-Ray" in r.headers
                self.log(f"  Cloudflare: {'EVET' if cf else 'HAYIR'}")
                break
            except Exception:
                continue

        self.log("")
        self.log("=== SUBDOMAIN ===")
        for sub in ["www", "mail", "admin", "api", "blog", "dev", "ftp", "cdn"]:
            try:
                socket.gethostbyname(f"{sub}.{domain}")
                self.log(f"  [+] {sub}.{domain}")
            except Exception:
                pass

    def analyze_ip(self, ip, headers):
        try:
            h, a, ip_list = socket.gethostbyaddr(ip)
            self.log(f"  Host: {h}")
        except Exception:
            self.log("  Reverse DNS yok")

        self.log("")
        self.log("=== PORT ===")
        for port in [22, 80, 443, 8080, 3306, 3389]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex((ip, port)) == 0:
                    self.log(f"  [+] {port_str(port)}")
                s.close()
            except Exception:
                pass

        self.log("")
        self.log("=== WEB ===")
        try:
            r = requests.get(f"http://{ip}", timeout=5, headers=headers)
            self.log(f"  HTTP: {status_str(r.status_code)} ({len(r.text)} byte)")
            title = re.search(r'<title>([^<]+)</title>', r.text)
            if title:
                self.log(f"  Title: {title.group(1)[:50]}")
        except Exception:
            self.log("  HTTP erisilemez")

    def check_platforms(self, username):
        from urllib.parse import quote_plus
        platforms = [
            ("GitHub", f"https://github.com/{quote_plus(username)}"),
            ("X/Twitter", f"https://x.com/{quote_plus(username)}"),
            ("Instagram", f"https://www.instagram.com/{quote_plus(username)}"),
            ("Reddit", f"https://www.reddit.com/user/{quote_plus(username)}"),
            ("YouTube", f"https://www.youtube.com/@{quote_plus(username)}"),
            ("TikTok", f"https://www.tiktok.com/@{quote_plus(username)}"),
            ("Facebook", f"https://www.facebook.com/{quote_plus(username)}"),
            ("Medium", f"https://medium.com/@{quote_plus(username)}"),
            ("Linktree", f"https://linktr.ee/{quote_plus(username)}"),
        ]

        found = 0
        for name, url in platforms:
            try:
                r = requests.get(url, timeout=3, headers={
                    "User-Agent": "Mozilla/5.0"
                }, allow_redirects=False)
                if r.status_code in (200, 301, 302):
                    self.log(f"  [+] {name}: {url} ({r.status_code})")
                    found += 1
            except Exception:
                pass

        self.log(f"  {found} platformda hesap bulundu")

    def finish(self):
        self.running = False
        self.search_btn.set_sensitive(True)
        self.status_label.set_text("Arama tamamlandi")
