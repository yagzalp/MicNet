import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import requests
import time
from modules.http_utils import status_str

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


class HttpStatusTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="HTTP Durum Kontrolu")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Birden fazla URL'nin erisilebilirligini kontrol eder. Yonlendirmeler otomatik takip edilir, https olmazsa http denenir ve sorunun nedeni net bir dille aciklanir. Her satira bir URL yazin.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="URL Listesi")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        self.entry = Gtk.TextView()
        self.entry.set_size_request(-1, 90)
        self.entry.get_style_context().add_class("output-text")
        buf = self.entry.get_buffer()
        buf.set_text("https://ornek.com\nhttps://ornek.com/admin\nornek.com:8080")
        sw_in = Gtk.ScrolledWindow()
        sw_in.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw_in.add(self.entry)
        input_box.pack_start(sw_in, False, False, 0)

        opt_box = Gtk.Box(spacing=12)
        opt_box.set_halign(Gtk.Align.CENTER)
        self.chk_redirect = Gtk.CheckButton(label="Yonlendirmeleri takip et (301/302 sonrasi son durumu goster)")
        self.chk_redirect.set_active(True)
        opt_box.pack_start(self.chk_redirect, False, False, 0)
        self.chk_fallback = Gtk.CheckButton(label="https basarisizsa http dene")
        self.chk_fallback.set_active(True)
        opt_box.pack_start(self.chk_fallback, False, False, 0)
        input_box.pack_start(opt_box, False, False, 0)

        self.check_btn = Gtk.Button(label="Kontrolleri Baslat")
        self.check_btn.connect("clicked", lambda _: self.start_check())
        self.check_btn.get_style_context().add_class("suggested-action")
        self.check_btn.set_halign(Gtk.Align.CENTER)
        input_box.pack_start(self.check_btn, False, False, 0)

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

    def start_check(self):
        if self.running:
            return
        buf = self.entry.get_buffer()
        urls = [u.strip() for u in buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).splitlines() if u.strip()]
        if not urls:
            self.status_label.set_text("En az bir URL girin")
            return
        self.running = True
        self.check_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Kontrol ediliyor...")
        thread = threading.Thread(target=self.check, args=(urls,), daemon=True)
        thread.start()

    def describe_error(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            return "Zaman asimi - site yanit vermiyor veya cok yavas"
        if isinstance(e, requests.exceptions.ConnectionError):
            return "Baglanti kurulamadi - site kapali, IP yanlis veya erisim engellenmis"
        if isinstance(e, requests.exceptions.SSLError):
            return "SSL/TLS hatasi - sertifika gecersiz olabilir"
        if isinstance(e, requests.exceptions.InvalidURL):
            return "Gecersiz URL format"
        return f"Hata: {e}"

    def check(self, urls):
        up = 0
        follow = self.chk_redirect.get_active()
        fallback = self.chk_fallback.get_active()
        for i, url in enumerate(urls):
            GLib.idle_add(self.log, f"[{i+1}/{len(urls)}] {url}")
            ok, lines = self.check_one(url, follow, fallback)
            for line in lines:
                GLib.idle_add(self.log, "    " + line)
            if ok:
                up += 1
            GLib.idle_add(self.log, "")
        GLib.idle_add(self.finish_check, up, len(urls))

    def check_one(self, url, follow, fallback):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if url.startswith("http://"):
            attempts = ["http"]
        else:
            attempts = ["https"]
            if fallback:
                attempts.append("http")
        err_lines = []
        for scheme in attempts:
            u = url
            if scheme == "http" and u.startswith("https://"):
                u = "http://" + u[len("https://"):]
            t0 = time.time()
            try:
                r = requests.get(u, timeout=8, verify=False, allow_redirects=follow,
                                 headers={"User-Agent": UA})
                dt = (time.time() - t0) * 1000
                server = r.headers.get("Server", "-")
                lines = [f"Protokol: {scheme}://"]
                if follow and r.history:
                    chain = " -> ".join(str(h.status_code) for h in r.history)
                    lines.append(f"Yonlendirme zinciri: {chain} -> {r.status_code}")
                lines.append(f"HTTP {r.status_code} | {status_str(r.status_code)}")
                lines.append(f"Sure: {dt:.0f} ms | Sunucu: {server}")
                if follow and r.history:
                    lines.append(f"Son adres: {r.url or u}")
                if r.status_code < 400:
                    return True, lines
                return False, lines
            except Exception as e:
                msg = self.describe_error(e)
                if scheme == "https":
                    err_lines.append(f"[-] https: {msg}")
                    continue
                err_lines.append(f"[-] {scheme}: {msg}")
                if err_lines:
                    return False, err_lines
                return False, [f"[-] {msg}"]
        if err_lines:
            return False, err_lines
        return False, ["[-] Erisilemedi"]

    def finish_check(self, up, total):
        self.running = False
        self.check_btn.set_sensitive(True)
        self.status_label.set_text(f"Tamamlandi - {up}/{total} erisilebilir")
