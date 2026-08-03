import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
import re
import json
import xml.etree.ElementTree as ET
from urllib.parse import quote

NS = "http://s3.amazonaws.com/doc/2006-03-01/"


class S3ScannerTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="S3 Bucket Tarayici (Detayli)")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Amazon S3 bucket'larini detayli inceler: varlik, bolge, genel listeleme, ACL (kim okuyabilir/yazabilir), bucket politikasi, versiyonlama, web barindirma ve ornek nesnelerin erisilebilirligi. Girilen isme gore yaygin varyasyonlar da test edilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Bucket Adi / Domain")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek (ornek.com veya ornek yazabilirsiniz)")
        self.entry.set_size_request(340, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        hbox.pack_start(self.entry, False, False, 0)
        self.scan_btn = Gtk.Button(label="Taramayi Baslat")
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
        name = self.entry.get_text().strip()
        if not name:
            self.status_label.set_text("Bucket adi girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(name,), daemon=True)
        thread.start()

    def scan(self, name):
        base = name.split("/")[0]
        if "." in base:
            base = base.split(".")[0]
        if not base:
            base = name
        candidates = [base]
        for suffix in ["-backup", "-bak", "-prod", "-production", "-dev", "-test", "-data", "-bucket", "-files", "-assets", "-public", "-uploads", "-media", "-storage"]:
            candidates.append(base + suffix)

        public_list = []
        public_write = []
        for bucket in candidates:
            url = f"https://{bucket}.s3.amazonaws.com/"
            try:
                r = requests.get(url, timeout=6, verify=False)
                if r.status_code == 404:
                    GLib.idle_add(self.log, f"[-] Bucket yok: {bucket}")
                    continue
                if r.status_code in (200, 403):
                    GLib.idle_add(self.log, f"=== {bucket} ===")
                    self.inspect_bucket(bucket, url, r.status_code, r.text)
                    if r.status_code == 200 and "<ListBucketResult" in r.text:
                        public_list.append(bucket)
                    GLib.idle_add(self.log, "")
            except requests.exceptions.SSLError:
                GLib.idle_add(self.log, f"[-] SSL hatasi: {bucket}")
            except Exception as e:
                GLib.idle_add(self.log, f"[-] Hata: {bucket} -> {e}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "================ OZET ================")
        if public_list:
            GLib.idle_add(self.log, "[!] GENEL LISTELENEBILIR BUCKETLAR:")
            for b in public_list:
                GLib.idle_add(self.log, f"    - {b}.s3.amazonaws.com")
            GLib.idle_add(self.log, "    Bunlar 'kapali' SANILIP acik birakilmis olabilir;")
            GLib.idle_add(self.log, "    dosya listesi ve veriler herkese gorunur.")
        else:
            GLib.idle_add(self.log, "[-] Genel listelenebilir bucket bulunamadi.")
        if public_write:
            GLib.idle_add(self.log, "[!!!] GENEL YAZILABILIR BUCKETLAR (cok kritik):")
            for b in public_write:
                GLib.idle_add(self.log, f"    - {b}.s3.amazonaws.com")
        GLib.idle_add(self.log, "=======================================")
        GLib.idle_add(self.finish_scan)

    def inspect_bucket(self, bucket, url, status, listing_text):
        details = []
        try:
            head = requests.head(url, timeout=6, verify=False)
            region = head.headers.get("x-amz-bucket-region", "belirsiz")
            GLib.idle_add(self.log, f"  Bolge: {region}")
        except Exception:
            pass

        if status == 403:
            GLib.idle_add(self.log, "  Durum: Bucket MEVCUT ama genel liste kapali (403)")

        if status == 200:
            GLib.idle_add(self.log, "  Durum: Bucket MEVCUT ve liste ACIK")
            keys = [k for k in re.findall(r"<Key>(.*?)</Key>", listing_text, re.S) if k]
            if keys:
                GLib.idle_add(self.log, f"  Nesne sayisi (ilk sayfa): {len(keys)}")
                GLib.idle_add(self.log, "  Ornek nesneler:")
                for k in keys[:5]:
                    GLib.idle_add(self.log, f"    - {k}")
                self.check_object_access(url, keys)

        self.check_acl(bucket, url)
        self.check_policy(bucket, url)
        self.check_versioning(url)
        self.check_website(bucket, url)

    def check_object_access(self, url, keys):
        files = [k for k in keys if not k.endswith("/")]
        if not files:
            return
        sample = files[0]
        try:
            r = requests.get(f"{url}{quote(sample)}", timeout=6, verify=False, headers={"Range": "bytes=0-0"})
            if r.status_code in (200, 206):
                GLib.idle_add(self.log, f"  [!] Ornek nesne HERKESE acik: {sample} (HTTP {r.status_code})")
                GLib.idle_add(self.log, "      Saldirgan bu dosyayi indirebilir.")
            else:
                GLib.idle_add(self.log, f"  [-] Ornek nesne korumali: {sample} (HTTP {r.status_code})")
        except Exception:
            pass

    def check_acl(self, bucket, url):
        try:
            r = requests.get(url, timeout=6, verify=False, params={"acl": ""})
            if r.status_code == 200:
                public = []
                try:
                    root = ET.fromstring(r.text)
                    for grant in root.iter(f"{{{NS}}}Grant"):
                        perms = [p.text for p in grant.findall(f"{{{NS}}}Permission")]
                        for g in grant.findall(f"{{{NS}}}Grantee"):
                            uri = g.find(f"{{{NS}}}URI")
                            if uri is not None and "AllUsers" in uri.text:
                                public.extend(perms)
                except ET.ParseError:
                    public = []
                if public:
                    GLib.idle_add(self.log, f"  [!] ACL: GENEL ERISIM -> {', '.join(set(public))}")
                    GLib.idle_add(self.log, f"      ({bucket} dosyalari herkese acik)")
                    if any("WRITE" in p for p in public):
                        GLib.idle_add(self.log, "      [!!!] HERKES YAZABILIR: zararli dosya yuklenebilir!")
                else:
                    GLib.idle_add(self.log, "  [-] ACL: genel erisim yok")
            elif r.status_code == 403:
                GLib.idle_add(self.log, "  [-] ACL: kontrol kapali (korumali)")
        except Exception:
            pass

    def check_policy(self, bucket, url):
        try:
            r = requests.get(url, timeout=6, verify=False, params={"policy": ""})
            if r.status_code == 200:
                try:
                    pol = r.json()
                except Exception:
                    pol = {}
                text = json.dumps(pol)
                if '"*"' in text and "Effect" in text:
                    GLib.idle_add(self.log, "  [!!!] Bucket POLITIKASI herkese izin veriyor!")
                    for st in pol.get("Statement", []):
                        action = st.get("Action", "?")
                        effect = st.get("Effect", "?")
                        GLib.idle_add(self.log, f"      Effect={effect} Action={action}")
                    GLib.idle_add(self.log, "      Politika ile genel okuma/yazma acik olabilir.")
                else:
                    GLib.idle_add(self.log, "  [-] Bucket politikasi: genel erisim yok")
            elif r.status_code == 404:
                GLib.idle_add(self.log, "  [-] Bucket politikasi yok")
            elif r.status_code == 403:
                GLib.idle_add(self.log, "  [-] Bucket politikasi: kontrol kapali (korumali)")
        except Exception:
            pass

    def check_versioning(self, url):
        try:
            r = requests.get(url, timeout=6, verify=False, params={"versioning": ""})
            status = "Yok"
            m = re.search(r"<Status>(\w+)</Status>", r.text)
            if m:
                status = m.group(1)
            if status == "Enabled":
                GLib.idle_add(self.log, "  [i] Versiyonlama: ACIK (silinen veriler kurtarilabilir)")
            elif status == "Suspended":
                GLib.idle_add(self.log, "  [i] Versiyonlama: Durdurulmus")
            else:
                GLib.idle_add(self.log, "  [-] Versiyonlama: Yok")
        except Exception:
            pass

    def check_website(self, bucket, url):
        try:
            r = requests.get(url, timeout=6, verify=False, params={"website": ""})
            if r.status_code == 200 and "<WebsiteConfiguration" in r.text:
                GLib.idle_add(self.log, "  [!] Statik WEB BARINDIRMA acik")
                GLib.idle_add(self.log, f"      http://{bucket}.s3-website-{self._region(url)}.amazonaws.com")
            elif r.status_code == 404:
                GLib.idle_add(self.log, "  [-] Statik web barindirma yok")
            elif r.status_code == 403:
                GLib.idle_add(self.log, "  [-] Statik web barindirma: kontrol kapali (korumali)")
        except Exception:
            pass

    def _region(self, url):
        try:
            head = requests.head(url, timeout=6, verify=False)
            return head.headers.get("x-amz-bucket-region", "us-east-1")
        except Exception:
            return "us-east-1"

    def finish_scan(self):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.status_label.set_text("Tarama tamamlandi")
