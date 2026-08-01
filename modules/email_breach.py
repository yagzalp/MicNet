import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import hashlib
import requests


class EmailBreachTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="E-posta Sizinti Kontrolu")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="E-posta adresinizin veri ihlallerinde (data breach) sizip sizmadigini kontrol eder. Have I Been Pwned API kullanir, sifrenizi gondermez.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="E-posta Kontrol")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        lbl = Gtk.Label(label="E-posta adresinizi girin. Bilgileriniz API'ye gonderilmez, sadece hash sorgusu yapilir.")
        lbl.set_xalign(0)
        lbl.get_style_context().add_class("desc-label")
        lbl.set_line_wrap(True)
        input_box.pack_start(lbl, False, False, 0)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="ornek@email.com")
        self.entry.set_size_request(350, 30)
        self.entry.connect("activate", lambda _: self.start_check())
        hbox.pack_start(self.entry, False, False, 0)
        self.check_btn = Gtk.Button(label="Kontrol Et")
        self.check_btn.connect("clicked", lambda _: self.start_check())
        self.check_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.check_btn, False, False, 0)
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

    def start_check(self):
        email = self.entry.get_text().strip()
        if not email or "@" not in email:
            self.status_label.set_text("Gecerli bir e-posta girin")
            return
        if self.running:
            return
        self.running = True
        self.check_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.status_label.set_text("Kontrol ediliyor...")
        thread = threading.Thread(target=self.check, args=(email,), daemon=True)
        thread.start()

    def check(self, email):
        headers = {"User-Agent": "MicNet-Security-Tool/1.0"}

        self.log(f"[*] E-posta: {email}")
        self.log("[*] Have I Been Pwned API kullaniliyor (kAnon-sizdirma)\n")

        try:
            sha1 = hashlib.sha1(email.encode()).hexdigest().upper()
            prefix = sha1[:5]
            suffix = sha1[5:]

            self.log(f"[*] Sorgu hash: {prefix}{'X' * (len(suffix))}")
            self.log(f"[*] API sorgusu yapiliyor...")

            resp = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                timeout=10, headers=headers
            )

            if resp.status_code != 200:
                self.log(f"[-] API hatasi: HTTP {resp.status_code}\n")
                self.log("Alternatif yontem:")
                self.log("1. https://haveibeenpwned.com/ sitesine gidin")
                self.log("2. E-postanizi manuel olarak sorgulayin")
                GLib.idle_add(self.finish)
                return

            hashes = resp.text.split("\n")
            found = False
            for line in hashes:
                if line.startswith(suffix):
                    count = int(line.split(":")[1].strip())
                    found = True
                    self.log("")
                    self.log(f"[!!!] UYARI: Bu e-posta {count} KEZ sizintiya ugradi!")
                    self.log(f"\n  Sizintida olabilecek bilgiler:")
                    self.log(f"  - Sifreler (genellikle hashli veya duz metin)")
                    self.log(f"  - Ad, soyad, kullanici adi")
                    self.log(f"  - Telefon numarasi, adres")
                    self.log(f"  - Kredi karti bilgileri (bazi sizintilarda)")
                    self.log("")
                    self.log("  Ne yapmalisiniz?")
                    self.log("  1. Bu e-posta ile kayitli oldugunuz tum sitelerde sifre degistirin")
                    self.log("  2. Her site icin FARKLI sifre kullanin")
                    self.log("  3. Iki faktorlu dogrulama (2FA) aktif edin")
                    self.log("  4. Sifre yoneticisi kullanmaya baslayin")
                    self.log(f"  5. https://haveibeenpwned.com/ adresinden detayli sorgulama yapin")
                    break

            if not found:
                self.log("")
                self.log("[+] Guvenli: Bu e-posta bilinen sizintilarda bulunamadi")
                self.log("")
                self.log("  Yine de dikkatli olun:")
                self.log("  - Her site icin farkli sifre kullanin")
                self.log("  - 2FA aktif edin")
                self.log("  - Supheli e-postalara tiklamayin")

        except requests.exceptions.ConnectionError:
            self.log("[-] API'ye baglanti kurulamadi\n")
            self.log("  1. Internet baglantinizi kontrol edin")
            self.log("  2. VPN/proxy kapali olsun")
            self.log("  3. https://haveibeenpwned.com/ manuel kontrol edin")
        except requests.exceptions.Timeout:
            self.log("[-] API zaman asimi")
        except Exception as e:
            self.log(f"[-] Hata: {e}")

        GLib.idle_add(self.finish)

    def finish(self):
        self.running = False
        self.check_btn.set_sensitive(True)
        self.status_label.set_text("Kontrol tamamlandi")
