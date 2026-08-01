import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
import socket


class ReverseIpTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Reverse IP Lookup")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Ayni IP uzerinde barinan domainleri bulur. Bir sunucuda baska hangi sitelerin oldugunu gosterir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek.com veya IP adresi")
        self.entry.set_size_request(400, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Sorgula")
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
        target = self.entry.get_text().strip()
        if not target:
            self.status_label.set_text("Domain veya IP girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Sorgulaniyor...")
        thread = threading.Thread(target=self.scan, args=(target,), daemon=True)
        thread.start()

    def scan(self, target):
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', target):
                ip = target
                self.log(f"[+] Hedef IP: {ip}")
            else:
                ip = socket.gethostbyname(target)
                self.log(f"[+] Domain: {target}")
                self.log(f"[+] Cozulen IP: {ip}")

            self.log("")

            try:
                hostname, aliases, ips = socket.gethostbyaddr(ip)
                self.log(f"[+] Reverse DNS: {hostname}")
                self.log("")
            except Exception:
                pass

            self.log("=== Reverse IP Sonuclari ===")
            self.log("[*] Ucretsiz API kullaniliyor (HackerTarget/YouGetSignal)")
            self.log("[*] Sinirli sayida sonuc donebilir\n")

            found = self.query_hackertarget(ip, headers)
            if not found:
                found = self.query_yougetsignal(ip, headers)
            if not found:
                self.log("[-] API'ler yanit vermedi\n")
                self.log("  Manuel alternatifler:")
                self.log("  1. https://www.shodan.io/host/" + ip)
                self.log("  2. https://search.censys.io/search?resource=hosts&query=" + ip)
                self.log("  3. https://securitytrails.com/list/ip/" + ip)

        except socket.gaierror:
            self.log("[-] DNS cozulemedi - gecerli bir domain veya IP girin")
        except Exception as e:
            self.log(f"[-] Hata: {e}")

        GLib.idle_add(self.finish)

    def query_hackertarget(self, ip, headers):
        try:
            resp = requests.get(
                f"https://api.hackertarget.com/reverseiplookup/?q={ip}",
                timeout=15, headers=headers
            )
            text = resp.text.strip()
            if text and "error" not in text.lower() and "API count exceeded" not in text:
                lines = text.split("\n")
                self.log(f"[+] HackerTarget sonuclari ({len(lines)} domain):\n")
                for line in lines[:100]:
                    self.log(f"  {line}")
                if len(lines) > 100:
                    self.log(f"  ... ve {len(lines) - 100} tane daha")
                return True
            elif "API count exceeded" in text:
                self.log("[-] HackerTarget: Gunluk limit doldu")
        except Exception:
            pass
        return False

    def query_yougetsignal(self, ip, headers):
        try:
            resp = requests.post(
                "https://www.yougetsignal.com/tools/web-sites-on-web-server/php/get-web-sites-on-web-server-json.php",
                data={"remoteAddress": ip, "format": "json"},
                timeout=15, headers=headers
            )
            data = resp.json()
            if data.get("status") == "Success":
                domains = data.get("domainArray", [])
                self.log(f"[+] YouGetSignal sonuclari ({len(domains)} domain):\n")
                for domain, ip_addr in domains[:100]:
                    self.log(f"  {domain}")
                if len(domains) > 100:
                    self.log(f"  ... ve {len(domains) - 100} tane daha")
                return True
        except Exception:
            pass
        return False

    def finish(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Sorgu tamamlandi")


import re
