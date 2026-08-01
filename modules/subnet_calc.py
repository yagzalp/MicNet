import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import ipaddress


class SubnetCalcTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Subnet / CIDR Hesaplayici")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bir IP/CIDR degerinden ag adresini, broadcast adresini, kullanilabilir host araligini ve maske bilgilerini hesaplar. Ag yapilandirmasinda temel yardimci.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="CIDR")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="Ornek: 192.168.1.0/24 veya 10.0.0.5/16")
        self.entry.set_size_request(350, 30)
        self.entry.connect("activate", lambda _: self.start_calc())
        hbox.pack_start(self.entry, False, False, 0)
        self.calc_btn = Gtk.Button(label="Hesapla")
        self.calc_btn.connect("clicked", lambda _: self.start_calc())
        self.calc_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.calc_btn, False, False, 0)
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

    def start_calc(self):
        cidr = self.entry.get_text().strip()
        if not cidr:
            self.status_label.set_text("CIDR girin")
            return
        if self.running:
            return
        self.running = True
        self.calc_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Hesaplaniyor...")
        thread = threading.Thread(target=self.calc, args=(cidr,), daemon=True)
        thread.start()

    def calc(self, cidr):
        try:
            net = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            GLib.idle_add(self.log, f"[-] Gecersiz CIDR: {e}")
            GLib.idle_add(self.finish_calc)
            return

        GLib.idle_add(self.log, f"[*] Girdi: {cidr}")
        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== AG BILGILERI ===")
        GLib.idle_add(self.log, f"  Ag adresi: {net.network_address}")
        GLib.idle_add(self.log, f"  Broadcast: {net.broadcast_address}")
        GLib.idle_add(self.log, f"  Ag maskesi: {net.netmask}")
        GLib.idle_add(self.log, f"  Ters maske: {net.hostmask}")
        GLib.idle_add(self.log, f"  Toplam host: {net.num_addresses}")
        if net.num_addresses > 2:
            usable = net.num_addresses - 2
        else:
            usable = 1 if net.num_addresses == 2 else net.num_addresses
        GLib.idle_add(self.log, f"  Kullanilabilir host: {usable}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== ARALIKLAR ===")
        hosts = list(net.hosts())
        if hosts:
            GLib.idle_add(self.log, f"  Ilk host: {hosts[0]}")
            GLib.idle_add(self.log, f"  Son host: {hosts[-1]}")
            if len(hosts) > 8:
                GLib.idle_add(self.log, "  Ilk birkaç:")
                for h in hosts[:5]:
                    GLib.idle_add(self.log, f"    - {h}")
                GLib.idle_add(self.log, "  Son birkaç:")
                for h in hosts[-5:]:
                    GLib.idle_add(self.log, f"    - {h}")
            else:
                GLib.idle_add(self.log, "  Tum hostlar:")
                for h in hosts:
                    GLib.idle_add(self.log, f"    - {h}")

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== ALT AG ACILIMI (/24 veya daha buyukse) ===")
        if net.prefixlen <= 24:
            for sub in net.subnets(new_prefix=24):
                GLib.idle_add(self.log, f"  - {sub}  ({sub.num_addresses} host)")
                if int(sub.network_address) > int(net.network_address) + 65536:
                    GLib.idle_add(self.log, "    ... (daha fazlasi gosterilmiyor)")
                    break

        GLib.idle_add(self.log, "")
        GLib.idle_add(self.log, "=== IP SINIFI ===")
        ip = net.network_address
        first_octet = int(ip).to_bytes(4, "big")[0]
        if 1 <= first_octet <= 126:
            cls = "A"
        elif 128 <= first_octet <= 191:
            cls = "B"
        elif 192 <= first_octet <= 223:
            cls = "C"
        elif 224 <= first_octet <= 239:
            cls = "D (multicast)"
        else:
            cls = "E (reserved)"
        GLib.idle_add(self.log, f"  IP sinifi: {cls}")
        GLib.idle_add(self.log, f"  Private ag mi: {'Evet' if ip.is_private else 'Hayir'}")
        GLib.idle_add(self.log, f"  Loopback: {'Evet' if ip.is_loopback else 'Hayir'}")

        GLib.idle_add(self.finish_calc)

    def finish_calc(self):
        self.running = False
        self.calc_btn.set_sensitive(True)
        self.status_label.set_text("Hesaplama tamamlandi")
