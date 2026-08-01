import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests


class CveLookupTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="CVE & Zaafiyet Aramasi")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="NVD (National Vulnerability Database) uzerinden yazilim adi ve versiyonuna gore bilinen zaafiyetleri (CVE) arar. Ornek: 'nginx 1.20', 'apache 2.4.49', 'wordpress'.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Arama")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="Ornek: nginx 1.20")
        self.entry.set_size_request(350, 30)
        self.entry.connect("activate", lambda _: self.start_search())
        hbox.pack_start(self.entry, False, False, 0)

        self.limit_spin = Gtk.SpinButton.new_with_range(5, 50, 5)
        self.limit_spin.set_value(15)
        hbox.pack_start(self.limit_spin, False, False, 0)

        self.search_btn = Gtk.Button(label="Ara")
        self.search_btn.connect("clicked", lambda _: self.start_search())
        self.search_btn.get_style_context().add_class("suggested-action")
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
        self.pack_start(self.status_label, False, False, 0)

        self.running = False

    def log(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def start_search(self):
        q = self.entry.get_text().strip()
        if not q:
            self.status_label.set_text("Arama terimi girin")
            return
        if self.running:
            return
        self.running = True
        self.search_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("NVD sorgulaniyor...")
        limit = int(self.limit_spin.get_value())
        thread = threading.Thread(target=self.search, args=(q, limit), daemon=True)
        thread.start()

    def search(self, query, limit):
        GLib.idle_add(self.log, f"[*] Arama: '{query}'")
        GLib.idle_add(self.log, "")

        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {
            "keywordSearch": query,
            "resultsPerPage": limit,
        }

        try:
            r = requests.get(url, params=params, timeout=20)
            data = r.json()
        except Exception as e:
            GLib.idle_add(self.log, f"[-] NVD API hatasi: {e}")
            GLib.idle_add(self.log, "    Internet baglantisi veya NVD erisimi kontrol edin.")
            GLib.idle_add(self.finish_search)
            return

        vulns = data.get("vulnerabilities", [])
        total = data.get("totalResults", 0)

        GLib.idle_add(self.log, f"[+] Toplam sonuc: {total} (ilk {min(limit, len(vulns))} gosteriliyor)")
        GLib.idle_add(self.log, "")

        if not vulns:
            GLib.idle_add(self.log, "[-] Sonuc bulunamadi.")
            GLib.idle_add(self.log, "    - Farkli bir anahtar kelime deneyin")
            GLib.idle_add(self.log, "    - Versiyon bilgisini ekleyin (orn: nginx 1.20)")
            GLib.idle_add(self.finish_search)
            return

        for v in vulns:
            try:
                cve = v.get("cve", {})
                cve_id = cve.get("id", "?")
                descs = cve.get("descriptions", [])
                description = ""
                for d in descs:
                    if d.get("lang") == "en":
                        description = d.get("value", "")
                        break
                if not description:
                    description = descs[0].get("value", "") if descs else ""

                metrics = cve.get("metrics", {})
                base_score = None
                severity = None
                for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                    if key in metrics:
                        entry = metrics[key][0]
                        cvss = entry.get("cvssData", {})
                        base_score = cvss.get("baseScore")
                        severity = cvss.get("baseSeverity") or entry.get("baseSeverity")
                        break

                published = (cve.get("published") or "")[:10]

                GLib.idle_add(self.log, f"=== {cve_id} ===")
                GLib.idle_add(self.log, f"  Yayin: {published}")
                if base_score is not None:
                    GLib.idle_add(self.log, f"  CVSS Skor: {base_score} / Seviye: {severity}")
                GLib.idle_add(self.log, f"  {description[:400]}")
                GLib.idle_add(self.log, "")
            except Exception:
                continue

        GLib.idle_add(self.log, "[*] Detay icin: https://nvd.nist.gov/vuln/search")
        GLib.idle_add(self.finish_search)

    def finish_search(self):
        self.running = False
        self.search_btn.set_sensitive(True)
        self.status_label.set_text("Arama tamamlandi")
