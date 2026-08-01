import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json


class FakeMailTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Sahte Mail Gönderme")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="SMTP veya Mailgun API uzerinden sahte e-posta gonderimi yapar. Kimden adresini degistirerek e-posta gonderebilirsiniz.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        # Yöntem seçici
        method_frame = Gtk.Frame(label="Yöntem")
        method_frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        method_frame_box.set_border_width(16)
        method_box = Gtk.Box(spacing=8)
        method_box.pack_start(Gtk.Label(label="Yöntem:"), False, False, 0)
        self.method_combo = Gtk.ComboBoxText()
        self.method_combo.append("smtp", "SMTP")
        self.method_combo.append("mailgun", "Mailgun API")
        self.method_combo.set_active(0)
        self.method_combo.connect("changed", lambda _: self.toggle_method())
        method_box.pack_start(self.method_combo, False, False, 0)
        method_frame_box.pack_start(method_box, False, False, 0)
        method_frame.add(method_frame_box)
        self.pack_start(method_frame, False, False, 0)

        # SMTP ayarları
        self.frame_smtp = Gtk.Frame(label="SMTP Sunucu Ayarları")
        grid_smtp = Gtk.Grid()
        grid_smtp.set_border_width(16)
        grid_smtp.set_row_spacing(8)
        grid_smtp.set_column_spacing(8)

        grid_smtp.attach(Gtk.Label(label="SMTP Sunucu:"), 0, 0, 1, 1)
        self.smtp_entry = Gtk.Entry()
        self.smtp_entry.set_placeholder_text("smtp.gmail.com")
        self.smtp_entry.set_text("smtp.gmail.com")
        grid_smtp.attach(self.smtp_entry, 1, 0, 1, 1)

        grid_smtp.attach(Gtk.Label(label="Port:"), 0, 1, 1, 1)
        self.port_spin = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.port_spin.set_value(587)
        grid_smtp.attach(self.port_spin, 1, 1, 1, 1)

        grid_smtp.attach(Gtk.Label(label="Kullanıcı:"), 0, 2, 1, 1)
        self.user_entry = Gtk.Entry()
        self.user_entry.set_placeholder_text("ornek@gmail.com")
        grid_smtp.attach(self.user_entry, 1, 2, 1, 1)

        grid_smtp.attach(Gtk.Label(label="Şifre:"), 0, 3, 1, 1)
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_placeholder_text("********")
        self.pass_entry.set_visibility(False)
        grid_smtp.attach(self.pass_entry, 1, 3, 1, 1)

        grid_smtp.attach(Gtk.Label(label="SSL Kullan:"), 0, 4, 1, 1)
        self.ssl_check = Gtk.CheckButton()
        grid_smtp.attach(self.ssl_check, 1, 4, 1, 1)

        self.frame_smtp.add(grid_smtp)
        self.pack_start(self.frame_smtp, False, False, 0)

        # Mailgun ayarları
        self.frame_mailgun = Gtk.Frame(label="Mailgun API Ayarları")
        grid_mg = Gtk.Grid()
        grid_mg.set_border_width(16)
        grid_mg.set_row_spacing(8)
        grid_mg.set_column_spacing(8)

        grid_mg.attach(Gtk.Label(label="API Key:"), 0, 0, 1, 1)
        self.mg_key_entry = Gtk.Entry()
        self.mg_key_entry.set_placeholder_text("key-xxxxxxxxxxxxxxxxxxxx")
        self.mg_key_entry.set_visibility(False)
        grid_mg.attach(self.mg_key_entry, 1, 0, 1, 1)

        grid_mg.attach(Gtk.Label(label="Domain:"), 0, 1, 1, 1)
        self.mg_domain_entry = Gtk.Entry()
        self.mg_domain_entry.set_placeholder_text("mg.ornek.com")
        grid_mg.attach(self.mg_domain_entry, 1, 1, 1, 1)

        grid_mg.attach(Gtk.Label(label="Bölge:"), 0, 2, 1, 1)
        self.mg_region_combo = Gtk.ComboBoxText()
        self.mg_region_combo.append("us", "ABD (api.mailgun.net)")
        self.mg_region_combo.append("eu", "AB (api.eu.mailgun.net)")
        self.mg_region_combo.set_active(0)
        grid_mg.attach(self.mg_region_combo, 1, 2, 1, 1)

        self.frame_mailgun.add(grid_mg)
        self.pack_start(self.frame_mailgun, False, False, 0)
        self.frame_mailgun.hide()

        # Mail içeriği
        frame_mail = Gtk.Frame(label="Mail İçeriği")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(16)

        hbox_from = Gtk.Box(spacing=6)
        hbox_from.pack_start(Gtk.Label(label="Kimden:"), False, False, 0)
        self.from_entry = Gtk.Entry()
        self.from_entry.set_placeholder_text("fake@ornek.com")
        hbox_from.pack_start(self.from_entry, True, True, 0)
        vbox.pack_start(hbox_from, False, False, 0)

        hbox_to = Gtk.Box(spacing=6)
        hbox_to.pack_start(Gtk.Label(label="Kime:"), False, False, 0)
        self.to_entry = Gtk.Entry()
        self.to_entry.set_placeholder_text("hedef@ornek.com")
        hbox_to.pack_start(self.to_entry, True, True, 0)
        vbox.pack_start(hbox_to, False, False, 0)

        hbox_subj = Gtk.Box(spacing=6)
        hbox_subj.pack_start(Gtk.Label(label="Konu:"), False, False, 0)
        self.subject_entry = Gtk.Entry()
        self.subject_entry.set_text("Önemli Bilgi")
        hbox_subj.pack_start(self.subject_entry, True, True, 0)
        vbox.pack_start(hbox_subj, False, False, 0)

        vbox.pack_start(Gtk.Label(label="Mesaj:"), False, False, 0)
        self.body_textview = Gtk.TextView()
        self.body_textview.set_size_request(-1, 150)
        self.body_buffer = self.body_textview.get_buffer()
        self.body_buffer.set_text("Merhaba,\n\nBu bir test mesajıdır.\n\nSaygılarımla")
        sw_body = Gtk.ScrolledWindow()
        sw_body.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw_body.add(self.body_textview)
        vbox.pack_start(sw_body, True, True, 0)

        frame_mail.add(vbox)
        self.pack_start(frame_mail, True, True, 0)

        # Buton
        hbox_btn = Gtk.Box(spacing=8)
        hbox_btn.set_halign(Gtk.Align.CENTER)
        self.send_btn = Gtk.Button(label="Mail Gönder")
        self.send_btn.connect("clicked", lambda _: self.send_mail())
        self.send_btn.get_style_context().add_class("suggested-action")
        hbox_btn.pack_start(self.send_btn, False, False, 0)
        self.pack_start(hbox_btn, False, False, 0)

        self.status_label = Gtk.Label(label="")
        self.pack_start(self.status_label, False, False, 0)

    def toggle_method(self):
        method = self.method_combo.get_active_id()
        if method == "mailgun":
            self.frame_smtp.hide()
            self.frame_mailgun.show()
        else:
            self.frame_mailgun.hide()
            self.frame_smtp.show()

    def send_mail(self):
        from_addr = self.from_entry.get_text().strip()
        to_addr = self.to_entry.get_text().strip()
        subject = self.subject_entry.get_text().strip()
        buf = self.body_buffer
        body = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

        if not all([from_addr, to_addr, subject, body]):
            self.status_label.set_text("Kimden, Kime, Konu ve Mesaj gerekli")
            return

        self.send_btn.set_sensitive(False)
        self.status_label.set_text("Gönderiliyor...")

        method = self.method_combo.get_active_id()
        if method == "mailgun":
            api_key = self.mg_key_entry.get_text().strip()
            domain = self.mg_domain_entry.get_text().strip()
            region = self.mg_region_combo.get_active_id()
            if not api_key or not domain:
                self.status_label.set_text("API Key ve Domain gerekli")
                self.send_btn.set_sensitive(True)
                return
            thread = threading.Thread(
                target=self.do_send_mailgun,
                args=(api_key, domain, region, from_addr, to_addr, subject, body),
                daemon=True,
            )
        else:
            smtp = self.smtp_entry.get_text().strip()
            port = int(self.port_spin.get_value())
            user = self.user_entry.get_text().strip()
            pwd = self.pass_entry.get_text().strip()
            if not all([smtp, user, pwd]):
                self.status_label.set_text("SMTP ayarlarını doldurun")
                self.send_btn.set_sensitive(True)
                return
            thread = threading.Thread(
                target=self.do_send_smtp,
                args=(smtp, port, user, pwd, from_addr, to_addr, subject, body),
                daemon=True,
            )
        thread.start()

    def do_send_smtp(self, smtp, port, user, pwd, from_addr, to_addr, subject, body):
        try:
            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            use_ssl = self.ssl_check.get_active()
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp, port)
            else:
                server = smtplib.SMTP(smtp, port)
                server.starttls()

            server.login(user, pwd)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
            GLib.idle_add(self.status_label.set_text, "Mail başarıyla gönderildi!")
        except smtplib.SMTPAuthenticationError:
            GLib.idle_add(self.status_label.set_text,
                          "Hata: Kimlik doğrulama başarısız. "
                          "Gmail için Uygulama Şifresi kullanın.")
        except Exception as e:
            GLib.idle_add(self.status_label.set_text, f"Hata: {e}")
        finally:
            GLib.idle_add(self.send_btn.set_sensitive, True)

    def do_send_mailgun(self, api_key, domain, region, from_addr, to_addr, subject, body):
        try:
            base_url = f"https://api.{region}.mailgun.net/v3/{domain}/messages"
            response = requests.post(
                base_url,
                auth=("api", api_key),
                data={
                    "from": from_addr,
                    "to": [to_addr],
                    "subject": subject,
                    "text": body,
                },
                timeout=30,
            )
            if response.status_code == 200:
                GLib.idle_add(self.status_label.set_text, "Mail başarıyla gönderildi!")
            else:
                msg = response.json().get("message", str(response.text))
                GLib.idle_add(self.status_label.set_text, f"Hata: {msg}")
        except requests.exceptions.ConnectionError:
            GLib.idle_add(self.status_label.set_text, "Hata: Bağlantı kurulamadı (İnternet yok mu?)")
        except Exception as e:
            GLib.idle_add(self.status_label.set_text, f"Hata: {e}")
        finally:
            GLib.idle_add(self.send_btn.set_sensitive, True)
