import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
import subprocess
import re


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except Exception:
        return ""


class NetInfoTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="AG BILGILERI")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bu makinenin ag yapilandirmasini gosterir: ag arayuzleri ve IP adresleri, ag geçidi (gateway), DNS sunuculari, yonlendirme tablosu. Yalnizca okuma islemidir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        btn_box = Gtk.Box(spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        self.collect_btn = Gtk.Button(label="Bilgileri Topla")
        self.collect_btn.connect("clicked", lambda _: self.start_collect())
        self.collect_btn.get_style_context().add_class("suggested-action")
        btn_box.pack_start(self.collect_btn, False, False, 0)
        self.pack_start(btn_box, False, False, 0)

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

    def start_collect(self):
        if self.running:
            return
        self.running = True
        self.collect_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Toplaniyor...")
        thread = threading.Thread(target=self.collect, daemon=True)
        thread.start()

    def collect(self):
        GLib.idle_add(self.log, f"=== MAKINE ===")
        GLib.idle_add(self.log, f"  Hostname  : {socket.gethostname()}")
        try:
            ip = socket.gethostbyname(socket.gethostname())
            GLib.idle_add(self.log, f"  Ana IP    : {ip}")
        except Exception:
            pass

        GLib.idle_add(self.log, "\n=== AG ARAYUZLERI ===")
        try:
            with open("/proc/net/dev") as f:
                for line in f.readlines()[2:]:
                    iface, data = line.split(":", 1)
                    iface = iface.strip()
                    if iface.startswith("lo"):
                        continue
                    fields = data.split()
                    rx, tx = int(fields[0]), int(fields[8])
                    GLib.idle_add(self.log, f"  {iface:>8}  RX: {rx/1024:.1f} KB  TX: {tx/1024:.1f} KB")
        except Exception:
            pass

        ip_out = run(["ip", "-o", "addr", "show"])
        if ip_out:
            GLib.idle_add(self.log, "")
            for line in ip_out.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "inet":
                    GLib.idle_add(self.log, f"  {parts[1]} -> {parts[3]}")
                elif len(parts) >= 4 and parts[2] == "inet6" and parts[3].lower() != "::1":
                    GLib.idle_add(self.log, f"  {parts[1]} -> {parts[3]}")

        GLib.idle_add(self.log, "\n=== YONLENDIRME (ROUTE) ===")
        route = run(["ip", "route"])
        if route:
            for line in route.splitlines():
                GLib.idle_add(self.log, f"  {line}")
        else:
            try:
                with open("/proc/net/route") as f:
                    for line in f.readlines()[1:]:
                        parts = line.split()
                        if len(parts) >= 3 and parts[2] != "00000000":
                            GLib.idle_add(self.log, f"  {parts[0]} gw {'.'.join(str(int(parts[2][i:i+2], 16)) for i in (6,4,2,0))}")
            except Exception:
                pass

        GLib.idle_add(self.log, "\n=== DNS SUNUCULARI ===")
        try:
            with open("/etc/resolv.conf") as f:
                found = False
                for line in f:
                    if line.startswith("nameserver"):
                        GLib.idle_add(self.log, f"  {line.strip()}")
                        found = True
                if not found:
                    GLib.idle_add(self.log, "  [-] DNS sunucusu tanimli degil")
        except Exception:
            GLib.idle_add(self.log, "  [-] resolv.conf okunamadi")

        GLib.idle_add(self.log, "\n=== ARP TABLOSU (yerel ag) ===")
        arp = run(["ip", "neigh"])
        if arp:
            for line in arp.splitlines()[:10]:
                GLib.idle_add(self.log, f"  {line}")
        else:
            GLib.idle_add(self.log, "  [-] Yerel ag komsulari goruntulenemedi")

        GLib.idle_add(self.log, "\n[*] Not: Ag yapilandirma detaylari (DHCP, DNS, VPN) sisteme gore degisir. Kali/Parrot'ta 'ip addr' ve 'ip route' ciktisi baz alinmistir.")
        GLib.idle_add(self.finish_collect)

    def finish_collect(self):
        self.running = False
        self.collect_btn.set_sensitive(True)
        self.status_label.set_text("Bilgiler toplandi")
