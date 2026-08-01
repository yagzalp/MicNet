import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import dns.resolver
import dns.exception
import requests


class DomainAnalyzerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Domain Analiz")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bir domainin guvenlik yapilandirmasini analiz eder: IP, SPF, DKIM, DMARC, web guvenlik basliklari ve SSL sertifikasi.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Domain")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek.com")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        self.scan_btn = Gtk.Button(label="Analiz Et")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.entry, False, False, 0)
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

    def append_text(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_scan(self):
        domain = self.entry.get_text().strip()
        if not domain:
            self.status_label.set_text("Lütfen bir domain girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Analiz ediliyor...")
        thread = threading.Thread(target=self.analyze, args=(domain,), daemon=True)
        thread.start()

    def log(self, text):
        GLib.idle_add(self.append_text, text)

    def analyze(self, domain):
        try:
            self.log("")
            self.log("===== IP ADRESI =====")
            try:
                ip = socket.gethostbyname(domain)
                self.log(f"  [+] IP: {ip}")
            except socket.gaierror:
                self.log("  [-] IP: Cozulemedi")

            self.log("")
            self.log("===== MX KAYITLARI (Mail Sunuculari) =====")
            try:
                answers = dns.resolver.resolve(domain, "MX")
                for rdata in answers:
                    self.log(f"  [+] Mail: {rdata.exchange} (priority {rdata.preference})")
            except dns.resolver.NoAnswer:
                self.log("  [-] MX: Kayit bulunamadi")
            except dns.resolver.NXDOMAIN:
                self.log("  [-] MX: Domain bulunamadi")
            except Exception as e:
                self.log(f"  [-] MX: Hata - {e}")

            self.log("")
            self.log("===== SPF (Email Spoofing Korumasi) =====")
            try:
                answers = dns.resolver.resolve(domain, "TXT")
                spf_found = False
                for rdata in answers:
                    txt = "".join(rdata.strings)
                    if txt.startswith("v=spf1"):
                        spf_found = True
                        if "~all" in txt:
                            self.log("  [-] SPF: SoftFail (~all) - Zayif koruma")
                        elif "-all" in txt:
                            self.log("  [+] SPF: HardFail (-all) - Iyi koruma")
                        elif "+all" in txt or "?all" in txt:
                            self.log("  [-] SPF: Gevsek/Etkisiz - Koruma yok")
                        else:
                            self.log("  [-] SPF: Mevcut (all politasi eksik)")
                        self.log(f"       Kayit: {txt[:80]}...")
                        break
                if not spf_found:
                    self.log("  [-] SPF: Kayit bulunamadi - KORUMA YOK")
            except dns.resolver.NoAnswer:
                self.log("  [-] SPF: Kayit bulunamadi - KORUMA YOK")
            except dns.resolver.NXDOMAIN:
                self.log("  [-] SPF: Domain bulunamadi")
            except Exception as e:
                self.log(f"  [-] SPF: Hata - {e}")

            self.log("")
            self.log("===== DKIM (Email Imzalama) =====")
            try:
                answers = dns.resolver.resolve(f"default._domainkey.{domain}", "TXT")
                dkim_found = False
                for rdata in answers:
                    txt = "".join(rdata.strings)
                    if "v=DKIM1" in txt:
                        dkim_found = True
                        algo = "sha256" if "h=sha256" in txt else ("sha1 (zayif)" if "h=sha1" in txt else "bulundu")
                        self.log(f"  [+] DKIM: Aktif ({algo})")
                        self.log(f"       Kayit: {txt[:80]}...")
                        break
                if not dkim_found:
                    self.log("  [-] DKIM: Kayit bulunamadi - KORUMA YOK")
            except dns.resolver.NoAnswer:
                self.log("  [-] DKIM: Kayit bulunamadi - KORUMA YOK")
            except dns.resolver.NXDOMAIN:
                self.log("  [-] DKIM: Kayit bulunamadi - KORUMA YOK")
            except Exception as e:
                self.log(f"  [-] DKIM: Hata - {e}")

            self.log("")
            self.log("===== DMARC (Email Politikasi) =====")
            try:
                answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
                dmarc_found = False
                for rdata in answers:
                    txt = "".join(rdata.strings)
                    if txt.startswith("v=DMARC1"):
                        dmarc_found = True
                        if "p=reject" in txt:
                            self.log("  [+] DMARC: Reject (Sikica korumali)")
                        elif "p=quarantine" in txt:
                            self.log("  [+] DMARC: Quarantine (Orta duzey koruma)")
                        elif "p=none" in txt:
                            self.log("  [-] DMARC: None (Sadece izleme, koruma yok)")
                        else:
                            self.log("  [-] DMARC: Mevcut (politika belirtilmemis)")
                        self.log(f"       Kayit: {txt[:80]}...")
                        break
                if not dmarc_found:
                    self.log("  [-] DMARC: Kayit bulunamadi - KORUMA YOK")
            except dns.resolver.NoAnswer:
                self.log("  [-] DMARC: Kayit bulunamadi - KORUMA YOK")
            except dns.resolver.NXDOMAIN:
                self.log("  [-] DMARC: Kayit bulunamadi - KORUMA YOK")
            except Exception as e:
                self.log(f"  [-] DMARC: Hata - {e}")

            self.log("")
            self.log("===== WEB GUVENLIK BASLIKLARI =====")
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,*/*",
                }
                resp = requests.get(f"https://{domain}", timeout=8, allow_redirects=True, headers=headers)
                h = resp.headers

                server = h.get("Server", "")
                cloudflare = "cloudflare" in server.lower() or "CF-Ray" in h

                if cloudflare:
                    self.log("  [+] WAF: Cloudflare ile korunuyor")
                else:
                    self.log("  [-] WAF: Cloudflare veya benzeri WAF tespit edilmedi")

                checks = [
                    ("Strict-Transport-Security", "HSTS (HTTPS zorlamasi)",
                     "SSL Strip - HTTPS HTTP'ye dusurulup trafik dinlenebilir"),
                    ("X-Frame-Options", "X-Frame-Options (Clickjacking)",
                     "Clickjacking - Site baska site icinde frame'de gosterilebilir"),
                    ("X-Content-Type-Options", "MIME Sniffing Korumasi",
                     "MIME Sniffing - Zararli dosya farkli turde algilanip calistirilabilir"),
                    ("Content-Security-Policy", "CSP (XSS Korumasi)",
                     "XSS - Zararli script enjekte edilip calistirilabilir"),
                    ("Referrer-Policy", "Referrer Politikasi",
                     "Bilgi sizintisi - URL bilgisi harici sitelere gidebilir"),
                ]

                for key, name, risk in checks:
                    if h.get(key):
                        self.log(f"  [+] {name}: KORUMALI")
                    else:
                        self.log(f"  [-] {name}: KORUMASIZ")
                        self.log(f"      Risk: {risk}")

                self.log("")
                if cloudflare:
                    self.log("  Cloudflare degerlendirmesi:")
                    self.log("    Korur: DDoS, SQLi, XSS, L7 saldirilari")
                    self.log("    Asil IP bulunursa Cloudflare baypas edilir")
                    self.log("    Shodan/Censys ile IP tespit edilebilir")
                else:
                    self.log("  WAF olmadigi icin dogrudan saldiriya acik:")
                    self.log("    - Port tarama, exploit, SQLi, XSS denenebilir")

            except requests.exceptions.ConnectionError:
                self.log("  [-] HTTP: Baglanti kurulamadi (site kapali veya engelliyor)")
            except requests.exceptions.Timeout:
                self.log("  [-] HTTP: Zaman asimi (8sn)")
            except Exception as e:
                self.log(f"  [-] HTTP: {e}")

            self.log("")
            self.log("===== SSL/TLS =====")
            try:
                import ssl
                from datetime import datetime
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
                    s.settimeout(10)
                    s.connect((domain, 443))
                    cert = s.getpeercert()
                    subj = dict(cert["subject"][0])
                    issuer = dict(cert["issuer"][0])
                    self.log(f"  [+] Sertifika: {subj.get('commonName', '?')}")
                    self.log(f"  [+] Tur: {issuer.get('organizationName', '?')}")
                    expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                    days = (expires - datetime.now()).days
                    if days > 30:
                        self.log(f"  [+] Gecerlilik: {days} gun (sorunsuz)")
                    elif days > 0:
                        self.log(f"  [-] Gecerlilik: {days} gun (yaklasiyor)")
                    else:
                        self.log("  [-] Gecerlilik: SURESI DOLMUS")
            except Exception as e:
                self.log(f"  [-] SSL: {e}")

            GLib.idle_add(self.finish_scan, domain)

        except Exception as e:
            GLib.idle_add(self.finish_scan_error, str(e))

    def finish_scan(self, domain):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text(f"Analiz tamamlandi: {domain}")

    def finish_scan_error(self, err):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Hata olustu")
