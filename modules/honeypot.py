import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import datetime
import ipaddress


SERVICES = [
    ("22", "SSH", "SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u2\r\n"),
    ("80", "HTTP", "HTTP/1.1 200 OK\r\nServer: nginx/1.24.0\r\nContent-Length: 0\r\n\r\n"),
    ("21", "FTP", "220 (vsFTPd 3.0.5)\r\n"),
    ("23", "Telnet", "\xff\xfd\x18\xff\xfd\x20\xff\xfd\x23\xff\xfd\x27\xff\xfd\x24"),
    ("3389", "RDP", "x\x00\x00\x00\x00\x00\x00\x00"),
    ("8080", "HTTP-Alt", "HTTP/1.1 200 OK\r\nServer: Apache/2.4.56\r\nContent-Length: 0\r\n\r\n"),
]


class HoneypotTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Honeypot - Saldiri Izleme")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Kendi makinende sahte servisler acar. Agdan gelen baglanti denemelerini ve verileri kaydeder. Savunma amacli bir guvenlik aracidir - saldirilari tespit etmek icin kullanilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Servis Secimi")
        service_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        service_box.set_border_width(16)

        self.checkbuttons = {}
        for port, name, banner in SERVICES:
            cb = Gtk.CheckButton(label=f"{name} (port {port})")
            cb.set_active(False)
            self.checkbuttons[name] = (port, banner, cb)
            service_box.pack_start(cb, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="Honeypot'u Baslat")
        self.start_btn.connect("clicked", lambda _: self.start_honeypot())
        self.start_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.start_btn, False, False, 0)
        self.stop_btn = Gtk.Button(label="Durdur")
        self.stop_btn.set_sensitive(False)
        self.stop_btn.connect("clicked", lambda _: self.stop_honeypot())
        hbox.pack_start(self.stop_btn, False, False, 0)
        service_box.pack_start(hbox, False, False, 0)

        info = Gtk.Label(label="Not: 1024 alti portlar ve 3389 icin root yetkisi gerekebilir. Calismayan servisler loga yazilir.")
        info.get_style_context().add_class("desc-label")
        info.set_xalign(0)
        service_box.pack_start(info, False, False, 0)

        frame.add(service_box)
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
        self.servers = []
        self.counter = 0

    def log(self, text):
        GLib.idle_add(self._append, text)

    def _append(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")
        self.textview.scroll_to_iter(self.textbuffer.get_end_iter(), 0, False, 0, 0)

    def start_honeypot(self):
        selected = [(name, port, banner) for name, (port, banner, cb) in self.checkbuttons.items() if cb.get_active()]
        if not selected:
            self.status_label.set_text("En az bir servis secin")
            return

        self.running = True
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.textbuffer.set_text("")
        self.counter = 0
        self.servers = []
        self.log("[*] Honeypot baslatiliyor...")
        self.log("[*] Secilen servisler: " + ", ".join(s[0] for s in selected))
        self.log("    " + "-" * 55)
        self.status_label.set_text("Honeypot calisiyor...")

        for name, port, banner in selected:
            t = threading.Thread(target=self._run_server, args=(name, port, banner), daemon=True)
            t.start()

    def _run_server(self, name, port, banner):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", int(port)))
            srv.listen(50)
            srv.settimeout(1)
            self.servers.append(srv)
            self.log(f"[+] [{name}] port {port} acik - dinleniyor")
        except PermissionError:
            self.log(f"[-] [{name}] port {port}: root yetkisi gerekli (1024 alti)")
            return
        except OSError as e:
            self.log(f"[-] [{name}] port {port}: {e}")
            return

        while self.running:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle_conn, args=(conn, addr, name, port, banner), daemon=True).start()

    def _handle_conn(self, conn, addr, name, port, banner):
        self.counter += 1
        cid = self.counter
        ip = addr[0]
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except Exception:
            hostname = "?"
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log(f"\n[{ts}] [#{cid}] [{name}] port {port}")
        self.log(f"  Kaynak: {ip}:{addr[1]}  (hostname: {hostname})")

        try:
            conn.settimeout(8)
            if banner:
                conn.sendall(banner.encode("latin-1", "replace"))
            data = b""
            try:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if len(data) > 4096 or len(chunk) < 4096:
                        break
            except socket.timeout:
                pass
            if data:
                self.log(f"  Veri ({len(data)} bayt):")
                self.log("  " + repr(data[:500]))
                try:
                    text = data.decode("utf-8", "replace")
                    first_line = text.split("\r\n")[0][:200]
                    self.log(f"  Ilk satir: {first_line}")
                except Exception:
                    pass
        except Exception as e:
            self.log(f"  Hata: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
            self.log(f"  [#{cid}] baglanti kapatildi")

    def stop_honeypot(self):
        self.running = False
        for srv in self.servers:
            try:
                srv.close()
            except Exception:
                pass
        self.servers = []
        self.start_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.log("\n[*] Honeypot durduruldu")
        self.status_label.set_text("Durduruldu")
