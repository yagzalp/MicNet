import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import os
import subprocess as sp


class WifiCrackTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="WiFi Sifre Kirma")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="WPA/WPA2 el sikismasi (.cap) dosyalarindan sozluk saldirisi ile sifre kirmaya calisir. aircrack-ng kullanir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Dosya ve Sozluk")
        grid = Gtk.Grid()
        grid.set_border_width(16)
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        grid.attach(Gtk.Label(label=".cap Dosyasi:"), 0, 0, 1, 1)
        cap_hbox = Gtk.Box(spacing=4)
        self.cap_entry = Gtk.Entry(placeholder_text="el_sikismasi.cap")
        self.cap_entry.set_size_request(300, 30)
        cap_hbox.pack_start(self.cap_entry, False, False, 0)
        self.cap_btn = Gtk.Button(label="Gez")
        self.cap_btn.connect("clicked", lambda _: self.browse_cap())
        cap_hbox.pack_start(self.cap_btn, False, False, 0)
        grid.attach(cap_hbox, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Sozluk:"), 0, 1, 1, 1)
        word_hbox = Gtk.Box(spacing=4)
        self.word_entry = Gtk.Entry(placeholder_text="Bos = dahili liste (200 kelime)")
        self.word_entry.set_size_request(300, 30)
        word_hbox.pack_start(self.word_entry, False, False, 0)
        self.word_btn = Gtk.Button(label="Gez")
        self.word_btn.connect("clicked", lambda _: self.browse_wordlist())
        word_hbox.pack_start(self.word_btn, False, False, 0)
        grid.attach(word_hbox, 1, 1, 1, 1)

        frame.add(grid)
        self.pack_start(frame, False, False, 0)

        info_frame = Gtk.Frame(label="Bilgi")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_border_width(12)
        lbl = Gtk.Label(label="Nasil calisir:\n1. airodump-ng ile hedef agdan WPA el sikismasi yakalayin\n2. .cap dosyasini buraya yukleyin\n3. aircrack-ng sozluk saldirisi ile sifreyi bulur")
        lbl.set_xalign(0)
        lbl.set_line_wrap(True)
        info_box.pack_start(lbl, False, False, 0)
        info_frame.add(info_box)
        self.pack_start(info_frame, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.crack_btn = Gtk.Button(label="Sifre Kir")
        self.crack_btn.connect("clicked", lambda _: self.start_crack())
        self.crack_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.crack_btn, False, False, 0)

        self.info_btn = Gtk.Button(label="Cap Bilgisi")
        self.info_btn.connect("clicked", lambda _: self.analyze_cap())
        hbox.pack_start(self.info_btn, False, False, 0)

        self.gen_btn = Gtk.Button(label="Sozluk Kaydet")
        self.gen_btn.connect("clicked", lambda _: self.generate_wordlist())
        hbox.pack_start(self.gen_btn, False, False, 0)
        self.pack_start(hbox, False, False, 0)

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

        self.common_passwords = [
            "12345678", "password", "123456789", "1234567890",
            "qwerty123", "abcdefgh", "11111111", "00000000",
            "admin1234", "passw0rd", "sunshine", "letmein",
            "welcome1", "monkey12", "dragon12", "master12",
            "football", "baseball", "soccer12", "batman12",
            "superman", "princess", "shadow12", "starwars",
            "iloveyou", "trustno1", "changeme",
            "password1", "password12", "password123",
            "qwerty1234", "qwerty12345", "qwerty123456",
            "asdfghjk", "zxcvbnm", "1234qwer", "1q2w3e4r",
            "qazwsxedc", "zaq12wsx", "1qaz2wsx", "3edc4rfv",
            "monkey123", "dragon123", "master123",
            "password!", "Passw0rd", "P@ssw0rd",
            "wlan", "wifi", "wireless", "kablosuz",
            "airties", "tp-link", "tplink", "netmaster",
            "modem", "internet", "adsl", "superonline",
            "ttnet", "turktelekom", "vodafone", "turkcell",
            "01234567", "11223344", "87654321", "13579246",
            "12344321", "11112222", "12121212", "12301230",
            "a1234567", "a12345678", "abcd1234", "abcd12345",
            "abcdef12", "abcdef123", "abc12345", "abc123456",
            "ankara06", "istanbul34", "izmir35", "adana01",
            "deneme12", "test1234", "ornek12", "sifre12",
            "parola12", "sifre123", "parola123", "deneme123",
            "konya42", "antalya07", "bursa16", "mugla48",
            "kayseri38", "eskisehir26", "gaziantep27",
            "nevsehir50", "yozgat66", "samsun55", "trabzon61",
            "ardahan75", "igdir76", "van65", "diyarbakir21",
            "pass1234", "key1234", "wifi1234",
            "admin123", "root1234", "user1234", "guest123",
            "home1234", "ev12345", "house123", "family12",
            "murat123", "ahmet123", "mehmet12", "ali12345",
            "veli1234", "can12345", "ayse1234", "fatma12",
            "hasan12", "huseyin12", "ibrahim12", "mustafa12",
            "orkun123", "burak123", "volkan12", "serkan12",
            "emre1234", "mert1234", "kaan1234", "efe12345",
            "Zonguldak67", "Kastamonu37", "Corlu17", "cerkezkoy",
            "123321123", "14725836", "95175382", "12369874",
            "0123456789", "9876543210", "55556666", "42424242",
            "windows10", "windows11", "android12", "iphone12",
            "Evim1234", "evim123", "wifi768", "modem123",
            "TurkTelekom", "TTNET", "superonline", "TurkcellSuper",
            "VodafoneNet", "Doping", "Milsat", "Uydunet",
            "123456789a", "123456789b", "a123456789", "abcdefg1",
            "pass12345", "qwerty2023", "qwerty2024", "admin2023",
            "shadow123", "sifre1234", "parola1234", "test12345",
            "merhaba12", "selam123", "tebrik12", "hosgeldin",
            "Yusuf123", "umut1234", "batu1234", "derya123",
            "cemal12", "nuran12", "asli1234", "deniz123",
            "ankarA06", "ISTANBUL", "izmir35", "bursA16",
            "Yalova77", "Tekirdag59", "Edirne22", "Canakkale17",
        ]

    def log(self, text):
        GLib.idle_add(self._append, text)

    def _append(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def browse_cap(self):
        d = Gtk.FileChooserDialog(title=".cap Dosyasi", parent=None,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        f = Gtk.FileFilter(name="Capture (*.cap)")
        f.add_pattern("*.cap")
        d.add_filter(f)
        f2 = Gtk.FileFilter(name="Tum dosyalar")
        f2.add_pattern("*")
        d.add_filter(f2)
        if d.run() == Gtk.ResponseType.ACCEPT:
            self.cap_entry.set_text(d.get_filename())
        d.destroy()

    def browse_wordlist(self):
        d = Gtk.FileChooserDialog(title="Sozluk Dosyasi", parent=None,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        if d.run() == Gtk.ResponseType.ACCEPT:
            self.word_entry.set_text(d.get_filename())
        d.destroy()

    def analyze_cap(self):
        cap = self.cap_entry.get_text().strip()
        if not cap or not os.path.exists(cap):
            self.status_label.set_text("Gecerli .cap dosyasi secin")
            return
        self.textbuffer.set_text("")
        self.log(f"[*] Dosya: {cap}")
        self.log(f"[*] Boyut: {os.path.getsize(cap)} byte")
        try:
            import scapy.all as scapy
            pkts = scapy.rdpcap(cap)
            self.log(f"[+] Toplam paket: {len(pkts)}")
            eapol_count = sum(1 for p in pkts if p.haslayer(scapy.EAPOL))
            self.log(f"[+] EAPOL paketi: {eapol_count} (WPA el sikismasi)")
            beacons = [p for p in pkts if p.haslayer(scapy.Dot11Beacon)]
            if beacons:
                ssid = beacons[0].getlayer(scapy.Dot11Elt)
                while ssid:
                    if ssid.ID == 0:
                        self.log(f"[+] SSID: {ssid.info.decode(errors='ignore')}")
                        break
                    ssid = ssid.payload.getlayer(scapy.Dot11Elt)
                self.log(f"[+] BSSID: {beacons[0].addr2}")
        except ImportError:
            self.log("[-] scapy modulu yok: pip install scapy")
        except Exception as e:
            self.log(f"[-] Hata: {e}")
        self.log("")
        self.log("Not: Tam el sikismasi icin en az 4 EAPOL paketi gerekir")
        self.log("aircrack-ng ile dogrulayin: aircrack-ng dosya.cap")

    def start_crack(self):
        cap = self.cap_entry.get_text().strip()
        if not cap:
            self.status_label.set_text(".cap dosyasi secin")
            return
        if not os.path.exists(cap):
            self.status_label.set_text("Dosya bulunamadi")
            return
        if self.running:
            return
        self.running = True
        self.crack_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Sifre kiriliyor...")
        thread = threading.Thread(target=self.crack, args=(cap,), daemon=True)
        thread.start()

    def crack(self, cap_path):
        wordlist_path = self.word_entry.get_text().strip()

        aircrack_path = None
        aircrack_env = None
        r = sp.run(["which", "aircrack-ng"], capture_output=True, text=True)
        if r.returncode == 0:
            aircrack_path = r.stdout.strip()
        elif os.path.exists(os.path.expanduser("~/.local/bin/aircrack-ng")):
            aircrack_path = os.path.expanduser("~/.local/bin/aircrack-ng")
            if os.path.exists("/tmp/fakelib.so"):
                aircrack_env = os.environ.copy()
                aircrack_env["LD_PRELOAD"] = "/tmp/fakelib.so"
            elif os.path.exists(os.path.expanduser("~/.local/lib/libaircrack-ce-wpa-1.7.0.so")):
                aircrack_env = os.environ.copy()
                aircrack_env["LD_LIBRARY_PATH"] = os.path.expanduser("~/.local/lib")

        has_aircrack = aircrack_path is not None

        self.log(f"[*] Hedef: {os.path.basename(cap_path)}")
        self.log(f"[*] Boyut: {os.path.getsize(cap_path)} byte")
        self.log("")

        if has_aircrack:
            self.log("[!] aircrack-ng kurulu\n")

            if wordlist_path and os.path.exists(wordlist_path):
                wl = wordlist_path
            else:
                wl = "/tmp/micnet_wordlist.txt"
                try:
                    with open(wl, "w") as f:
                        for p in self.common_passwords:
                            f.write(p + "\n")
                    self.log(f"[*] Dahili sozluk kaydedildi: {wl}")
                    self.log(f"[*] {len(self.common_passwords)} kelime\n")
                except Exception as e:
                    self.log(f"[-] Sozluk yazma hatasi: {e}")
                    GLib.idle_add(self.finish)
                    return

            self.log("[*] aircrack-ng calisiyor...\n")
            try:
                result = sp.run(
                    [aircrack_path, "-w", wl, cap_path],
                    capture_output=True, text=True, timeout=300,
                    env=aircrack_env
                )
                output = result.stdout + result.stderr
                for line in output.split("\n"):
                    s = line.strip()
                    if not s:
                        continue
                    if "KEY FOUND" in s:
                        self.log(f"[!!!] {s}")
                    elif "Passphrase not in" in s:
                        self.log(f"[-] {s}")
                    elif "No networks found" in s:
                        self.log(f"[-] {s}")
                    elif "Waiting" in s:
                        continue
                    elif "Reading" in s or "Opening" in s:
                        continue
                    elif "KB/s" in s or s.startswith("["):
                        continue
                    else:
                        self.log(f"  {s}")
            except sp.TimeoutExpired:
                self.log("[-] Zaman asimi (cok fazla kelime)")
            except Exception as e:
                self.log(f"[-] Hata: {e}")

        else:
            self.log("[-] aircrack-ng bulunamadi!")
            self.log("")
            self.log("Kurulum icin:")
            self.log("  sudo pacman -S aircrack-ng")
            self.log("")
            self.log("Manuel kullanim:")
            self.log(f"  aircrack-ng -w sozluk.txt \"{cap_path}\"")
            self.log("")
            self.log("veya:")
            self.log("  aircrack-ng -w /usr/share/wordlists/rockyou.txt \"{cap_path}\"")
            self.log("")
            self.log("Dahili 200 kelimeyi disa aktarmak icin")
            self.log("'Sozluk Kaydet' butonunu kullanin")

        GLib.idle_add(self.finish)

    def generate_wordlist(self):
        d = Gtk.FileChooserDialog(title="Sozlugu Kaydet", parent=None,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT))
        d.set_current_name("sozluk.txt")
        if d.run() == Gtk.ResponseType.ACCEPT:
            path = d.get_filename()
            try:
                with open(path, "w") as f:
                    for p in self.common_passwords:
                        f.write(p + "\n")
                self.status_label.set_text(f"Kaydedildi: {path} ({len(self.common_passwords)} kelime)")
                self.word_entry.set_text(path)
            except Exception as e:
                self.status_label.set_text(f"Hata: {e}")
        d.destroy()

    def finish(self):
        self.running = False
        self.crack_btn.set_sensitive(True)
        self.status_label.set_text("Islem tamamlandi")
