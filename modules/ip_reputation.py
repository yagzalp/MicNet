import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import dns.resolver
import requests
from modules.api_helper import get_api_key


class IpReputationTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="IP / Domain Kara Liste Kontrolu")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bir IP veya domainin spam/kotu amaçli trafik listelerinde (RBL) kayitli olup olmadigini DNS tabanli kara listeler ve AbuseIPDB uzerinden kontrol eder.")
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
        self.entry = Gtk.Entry(placeholder_text="IP adresi veya domain")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_check())
        hbox.pack_start(self.entry, False, False, 0)
        self.check_btn = Gtk.Button(label="Kontrol Et")
        self.check_btn.connect("clicked", lambda _: self.start_check())
        self.check_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.check_btn, False, False, 0)
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

        self.rbl_list = [
            ("Spamhaus ZEN", "zen.spamhaus.org", "spam/spam kaynakli IP"),
            ("Spamhaus SBL", "sbl.spamhaus.org", "spam kaynakli IP"),
            ("Spamhaus XBL", "xbl.spamhaus.org", "zombi/truva ati bot IP"),
            ("Spamhaus PBL", "pbl.spamhaus.org", "yetkisiz mail sunucusu IP"),
            ("SpamCop", "bl.spamcop.net", "spam bildirilen IP"),
            ("SORBS", "dnsbl.sorbs.net", "spam/kotu IP"),
            ("Barracuda", "b.barracudacentral.org", "spam kaynakli IP"),
            ("SpamRats", "spam.spamrats.com", "spam kaynakli IP"),
            ("dnsbl.dronebl.org", "dnsbl.dronebl.org", "bot/drone IP"),
            ("abuseat.org (SBL-XBL)", "abuseat.org", "reputation"),
        ]

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_check(self):
        target = self.entry.get_text().strip()
        if not target:
            self.status_label.set_text("Hedef girin")
            return
        if self.running:
            return
        self.running = True
        self.check_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Kontrol ediliyor...")
        thread = threading.Thread(target=self.check, args=(target,), daemon=True)
        thread.start()

    def _rbl_lookup(self, ip):
        parts = ip.split(".")
        if len(parts) != 4:
            return None
        reversed_ip = ".".join(reversed(parts))
        for name, rbl_domain, desc in self.rbl_list:
            query = f"{reversed_ip}.{rbl_domain}"
            listed = False
            reason = ""
            try:
                answers = dns.resolver.resolve(query, "A", lifetime=6)
                if answers:
                    listed = True
                    reason = "; ".join(a.to_text() for a in answers)
            except dns.resolver.NXDOMAIN:
                pass
            except dns.resolver.NoAnswer:
                pass
            except Exception:
                pass
            yield (name, listed, reason)

    def check(self, target):
        target = target.strip()
        ip = target

        try:
            socket.inet_aton(target)
        except socket.error:
            GLib.idle_add(self.log, f"[*] Domain cozuluyor: {target}")
            try:
                ip = socket.gethostbyname(target)
            except socket.gaierror:
                GLib.idle_add(self.log, "[-] Domain cozulemedi")
                GLib.idle_add(self.finish_check)
                return

        GLib.idle_add(self.log, f"[*] Hedef: {target}")
        GLib.idle_add(self.log, f"[*] Cozulen IP: {ip}")
        GLib.idle_add(self.log, "")

        GLib.idle_add(self.log, "=== RBL KARA LISTE KONTROL ===")
        listed_count = 0
        for name, listed, reason in self._rbl_lookup(ip):
            if listed:
                listed_count += 1
                GLib.idle_add(self.log, f"  [!] LISTELI: {name} ({reason})")
            else:
                GLib.idle_add(self.log, f"  [-] Temiz: {name}")

        GLib.idle_add(self.log, "")
        if listed_count:
            GLib.idle_add(self.log, f"  [!] {listed_count} kara listede kayit bulundu")
            GLib.idle_add(self.log, "      Bu IP, e-posta filtrelerince bloklanabilir.")
        else:
            GLib.idle_add(self.log, "  [+] Bilinen kara listelerde kayit yok")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== ABUSEIPDB ===")
        api_key = get_api_key("abuseipdb")
        if not api_key:
            GLib.idle_add(self.log, "  [*] AbuseIPDB API anahtari yok (Ayarlar sekmesinden 'abuseipdb' ekleyin)")
        else:
            try:
                r = requests.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": ip},
                    headers={"Key": api_key, "Accept": "application/json"},
                    timeout=15,
                )
                data = r.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                usage = data.get("usageType", "?")
                total = data.get("totalReports", 0)
                country = data.get("countryCode", "?")
                GLib.idle_add(self.log, f"  Abuse Confidence Skoru: {score}/100")
                GLib.idle_add(self.log, f"  Rapor sayisi: {total}")
                GLib.idle_add(self.log, f"  Kullanim tipi: {usage}")
                GLib.idle_add(self.log, f"  Ulke: {country}")
                if score >= 50:
                    GLib.idle_add(self.log, "  [!] Yuksek skor - kotu itibar")
                else:
                    GLib.idle_add(self.log, "  [+] Dusuk skor - genel itibar iyi")
            except Exception as e:
                GLib.idle_add(self.log, f"  [-] AbuseIPDB hatasi: {e}")

        GLib.idle_add(self.finish_check)

    def finish_check(self):
        self.running = False
        self.check_btn.set_sensitive(True)
        self.status_label.set_text("Kontrol tamamlandi")
