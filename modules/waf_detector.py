import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests


class WafDetectorTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="WAF Tespiti")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef sitenin arkasinda web uygulama guvenlik duvari (WAF) olup olmadigini parmak izi bilgileriyle tespit eder. Guvenlik testlerinde hedefin koruma katmanini bilmek onemlidir.")
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

        self.WAF_SIGNATURES = [
            ("Cloudflare", ["cf-ray", "cf-cache-status", "cf-connecting-ip", "__cfduid", "cf-wan"], ["cloudflare"]),
            ("Akamai", ["akamai", "ak_bmsc", "akavpau"], ["reference #"],),
            ("AWS WAF / Shield", ["x-amzn-", "awswaf", "aws"], ["request blocked"]),
            ("F5 BIG-IP / ASM", ["bigip", "f5"], ["the requested url was rejected", "support.f5.com"]),
            ("ModSecurity (OWASP CRS)", ["mod_security"], ["not acceptable", "mod_security", "error detected by modsecurity"]),
            ("Imperva / Incapsula", ["incap_ses", "visid_incap", "imperva"], ["incapsula", "imperva"]),
            ("Sucuri", ["sucuri", "x-sucuri-id", "x-sucuri-cache"], ["sucuri cloudproxy"]),
            ("Barracuda", ["barracuda"], ["barracuda waf", "bfactor"]),
            ("Citrix NetScaler", ["netscaler", "citrix"], ["netscaler"]),
            ("Radware", ["radware"], ["radware", "captcha"]),
            ("DDoS-Guard", ["ddos-guard"], ["ddos-guard", "vqkqf"]),
            ("StackPath / Sucuri CDN", ["stackpath"], ["cdn"]),
            ("Wordfence", ["wf-"], ["wordfence", "blocked by wordfence"]),
            ("Comodo WAF", ["comodo"], ["comodo"]),
            ("Cloudbric", ["cloudbric"], ["cloudbric"]),
            ("Airlock", ["al-lb", "al_ltc"], ["airlock"]),
            ("Kona (Akamai)", ["x-kona"], ["kona"]),
            ("CrawlProtect", ["crawlprotect"], ["crawlprotect"]),
            ("360 (Qihoo)", ["qh-"], ["360wzb"]),
            ("Yundun", ["yundun"], ["yundun"]),
            ("Aliyun WAF", ["aliyun"], ["aliyun", "error.waf"]),
            ("Baidu Yunjiasu", ["yunjiasu"], ["yunjiasu"]),
            ("Tencent WAF", ["tencent"], ["tencent", "waf"]),
            ("Azure WAF / Front Door", ["x-azure-", "x-ms-"], ["azure", "front door"]),
            ("GCP Load Balancer", ["gcp-", "x-goog-"], ["google"]),
            ("Varnish/nginx proxy", ["varnish", "x-varnish"], []),
            ("HAProxy", ["x-haproxy", "server: haproxy"], []),
        ]

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
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        ua = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}

        GLib.idle_add(self.log, f"[*] Hedef: {url}")
        GLib.idle_add(self.log, "")

        responses = []

        try:
            r = requests.get(url, timeout=10, headers=ua)
            responses.append(("normal", r))
        except Exception as e:
            GLib.idle_add(self.log, f"[-] Baglanti kurulamadi: {e}")
            GLib.idle_add(self.finish_scan)
            return

        payloads = [
            "?id=1' OR '1'='1",
            "?id=<script>alert(1)</script>",
            "?id=../../etc/passwd",
            "?id=1 AND 1=1 UNION SELECT 1,2,3",
        ]
        for p in payloads:
            try:
                r = requests.get(url + p, timeout=10, headers=ua)
                responses.append(("payload", r))
            except Exception:
                pass

        hits = []
        for name, header_markers, body_markers in self.WAF_SIGNATURES:
            found = False
            detail = []
            for _, resp in responses:
                for k in resp.headers:
                    kl = k.lower()
                    if any(m in kl for m in header_markers):
                        found = True
                        detail.append(f"Header: {k}={resp.headers[k][:50]}")
                        break
                for m in body_markers:
                    if m and m.lower() in resp.text[:2000].lower():
                        found = True
                        detail.append(f"Body: '{m}'")
                        break
            if found:
                hits.append((name, detail))

        cf = any(name == "Cloudflare" for name, _ in hits)

        GLib.idle_add(self.log, "=== SONUC ===")
        if hits:
            seen = set()
            for name, detail in hits:
                if name in seen:
                    continue
                seen.add(name)
                GLib.idle_add(self.log, f"  [+] {name} TESPIT EDILDI")
                for d in detail[:3]:
                    GLib.idle_add(self.log, f"      {d}")
        else:
            GLib.idle_add(self.log, "  [-] Bilinen bir WAF tespit edilemedi")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== KORUMA KATMANI DEGERLENDIRMESI ===")
        first = responses[0][1]
        if hits:
            names = ", ".join(n for n, _ in hits)
            GLib.idle_add(self.log, f"  Koruma: {names}")
            GLib.idle_add(self.log, "  [*] WAF tespit edildi - tarama sinirlandirilabilir/engellenebilir")
        else:
            GLib.idle_add(self.log, "  [*] Gorusunurde WAF yok veya tanisamayan ozel bir koruma")
            GLib.idle_add(self.log, "  [*] Dogrudan uygulama katmani testlerine gecilebilir")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== GOREVLI RESPONSE ===")
        r0 = first
        GLib.idle_add(self.log, f"  Normal istek: {r0.status_code}, {len(r0.content)} bayt")
        for p, r in responses[1:]:
            GLib.idle_add(self.log, f"  Payload istek: {r.status_code}, {len(r.content)} bayt")
        if len(responses) > 1 and len({r.status_code for _, r in responses}) > 1:
            GLib.idle_add(self.log, "  [!] Payload isteklerine farkli yanit - aktif filtreleme var")

        GLib.idle_add(self.finish_scan)

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
