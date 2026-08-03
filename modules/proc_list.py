import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import os


def read_proc(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            stat = f.read()
        comm_start = stat.find("(")
        comm_end = stat.rfind(")")
        comm = stat[comm_start + 1:comm_end]
        fields = stat[comm_end + 2:].split()
        state = fields[0]
        ppid = fields[1]
        return comm, state, ppid
    except Exception:
        return None


def get_uid(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("Uid:"):
                    return line.split()[1]
    except Exception:
        return ""


def get_rss(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS"):
                    return int(line.split()[1])
    except Exception:
        return 0


def get_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read().replace(b"\x00", b" ").strip()
        return raw.decode("utf-8", "replace")[:120]
    except Exception:
        return ""


class ProcListTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="SUREC LISTESI")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Calisan tum surecleri PID, kullanici, durum, bellek ve komut satiri ile listeler. Bu makinedeki supheli surecleri (kripto madenciligi, ters kabuk, beklenmeyen process) tespit etmeye yardimci olur.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        btn_box = Gtk.Box(spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        self.collect_btn = Gtk.Button(label="Surecleri Listele")
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
        self.status_label.set_text("Listeleniyor...")
        thread = threading.Thread(target=self.collect, daemon=True)
        thread.start()

    def collect(self):
        pids = []
        try:
            for name in os.listdir("/proc"):
                if name.isdigit():
                    pids.append(int(name))
        except Exception:
            pass
        pids.sort()

        rows = []
        for pid in pids:
            try:
                info = read_proc(pid)
                if not info:
                    continue
                comm, state, ppid = info
                uid = get_uid(pid)
                rss = get_rss(pid)
                cmd = get_cmdline(pid) or comm
                rss = rss if isinstance(rss, int) else 0
                uid = uid if isinstance(uid, str) and uid else "-"
                state = state if state else "?"
                rows.append((pid, uid, state, rss, cmd))
            except Exception:
                continue

        GLib.idle_add(self.log, f"[*] Toplam {len(rows)} surec calisiyor\n")
        GLib.idle_add(self.log, f"{'PID':>6} {'USER':>8} {'ST':>2} {'RSS(MB)':>8}  KOMUT")
        GLib.idle_add(self.log, "-" * 80)
        for pid, uid, state, rss, cmd in rows:
            GLib.idle_add(self.log, f"{pid:>6} {uid:>8} {state:>2} {rss/1024:>7.1f}  {cmd}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== IPUCLARI ===")
        GLib.idle_add(self.log, "  - Sizin bilmediginiz ve yuksek CPU/bellek tuketen surecleri arastirin")
        GLib.idle_add(self.log, "  - Tekrarlanan 'curl'/'wget' surecleri buyuk indirme isaretidir")
        GLib.idle_add(self.log, "  - /tmp veya /dev/shm altinda calisan binary'ler suphelidir")
        GLib.idle_add(self.log, "  - 'nc', 'ncat', 'socat' gibi ag araclari ters kabuk isareti olabilir")
        GLib.idle_add(self.finish_collect)

    def finish_collect(self):
        self.running = False
        self.collect_btn.set_sensitive(True)
        self.status_label.set_text("Listeleme tamamlandi")
