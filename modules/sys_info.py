import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import os
import platform
import subprocess
import shutil
import socket


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except Exception:
        return ""


def mb(val):
    try:
        return f"{int(val) / 1024:,.1f} MB"
    except Exception:
        return str(val)


class SysInfoTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="SISTEM BILGILERI")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Mevcut makinenin donanim ve isletim sistemi bilgilerini toplar: islemci, bellek, disk, isletim sistemi, kernel ve calisma suresi. Yalnizca okuma islemidir, hicbir sey degistirmez.")
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
        GLib.idle_add(self.log, "=== ISLETIM SISTEMI ===")
        os_name = ""
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("=", 1)[1].strip().strip('"')
                        break
        except Exception:
            pass
        GLib.idle_add(self.log, f"  Dagilim   : {os_name or 'bilinmiyor'}")
        GLib.idle_add(self.log, f"  Kernel    : {platform.release()}")
        GLib.idle_add(self.log, f"  Mimari    : {platform.machine()}")
        GLib.idle_add(self.log, f"  Hostname  : {socket.gethostname()}")
        try:
            with open("/proc/uptime") as f:
                uptime_s = float(f.read().split()[0])
            days, rem = divmod(int(uptime_s), 86400)
            hours, rem = divmod(rem, 3600)
            mins = rem // 60
            GLib.idle_add(self.log, f"  Calisma   : {days} gun {hours} saat {mins} dk")
        except Exception:
            pass

        GLib.idle_add(self.log, "\n=== ISLEMCI ===")
        GLib.idle_add(self.log, f"  Cekirdek  : {os.cpu_count()}")
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        GLib.idle_add(self.log, f"  Model     : {line.split(':', 1)[1].strip()}")
                        break
        except Exception:
            pass
        ghz = run(["lscpu"]) 
        for line in ghz.splitlines():
            if line.lower().startswith("cpu mhz"):
                GLib.idle_add(self.log, f"  Frekans   : {line.split(':',1)[1].strip()} MHz")

        GLib.idle_add(self.log, "\n=== BELLEK ===")
        mem = {}
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":")
                    mem[k.strip()] = v.strip()
            GLib.idle_add(self.log, f"  Toplam    : {mb(mem.get('MemTotal','0').split()[0])}")
            GLib.idle_add(self.log, f"  Kullanilabilir: {mb(mem.get('MemAvailable','0').split()[0])}")
            GLib.idle_add(self.log, f"  Swap      : {mb(mem.get('SwapTotal','0').split()[0])}")
        except Exception:
            pass

        GLib.idle_add(self.log, "\n=== DISK ===")
        try:
            total, used, free = shutil.disk_usage("/")
            GLib.idle_add(self.log, f"  Kok bolum : toplam {total/1024**3:.1f} GB | kullanilan {used/1024**3:.1f} GB | bos {free/1024**3:.1f} GB")
        except Exception:
            pass
        df = run(["df", "-h", "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs", "-x", "overlay"])
        if df:
            lines = df.splitlines()
            if lines:
                GLib.idle_add(self.log, f"  {lines[0]}")
                for l in lines[1:8]:
                    GLib.idle_add(self.log, f"  {l}")

        GLib.idle_add(self.log, "\n=== DIGER ===")
        if shutil.which("python3"):
            GLib.idle_add(self.log, f"  Python    : {run(['python3','--version'])}")
        if shutil.which("curl"):
            GLib.idle_add(self.log, f"  curl      : {run(['curl','--version']).splitlines()[0]}")

        GLib.idle_add(self.finish_collect)

    def finish_collect(self):
        self.running = False
        self.collect_btn.set_sensitive(True)
        self.status_label.set_text("Bilgiler toplandi")
