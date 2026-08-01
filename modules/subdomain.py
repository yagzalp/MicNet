import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import threading
import socket
class SubdomainTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(24)

        title = Gtk.Label(label="Subdomain Scanner")
        title.get_style_context().add_class("title-label")
        title.set_xalign(0)
        self.pack_start(title, False, False, 0)

        desc = Gtk.Label(label="Bir domainin alt alan adlarini (subdomain) keşfeder. Hedef domain hakkinda daha fazla bilgi toplamak icin kullanilir.")
        desc.get_style_context().add_class("desc-label")
        desc.set_line_wrap(True)
        desc.set_xalign(0)
        self.pack_start(desc, False, False, 0)

        sep = Gtk.Separator()
        self.pack_start(sep, False, False, 4)

        frame = Gtk.Frame(label="Hedef Domain")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_border_width(16)

        hbox = Gtk.Box(spacing=8)
        hbox.set_halign(Gtk.Align.CENTER)
        self.entry = Gtk.Entry(placeholder_text="örnek: example.com")
        self.entry.set_size_request(300, 30)
        self.entry.connect("activate", lambda _: self.start_scan())
        self.scan_btn = Gtk.Button(label="Tara")
        self.scan_btn.connect("clicked", lambda _: self.start_scan())
        self.scan_btn.get_style_context().add_class("suggested-action")
        hbox.pack_start(self.entry, False, False, 0)
        hbox.pack_start(self.scan_btn, False, False, 0)
        input_box.pack_start(hbox, False, False, 0)

        frame.add(input_box)
        self.pack_start(frame, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.pack_start(self.progress, False, False, 0)

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

        self.common_subdomains = [
            "www", "mail", "ftp", "admin", "blog", "dev", "api", "test",
            "webmail", "smtp", "pop", "ns1", "ns2", "dns", "vpn", "ssh",
            "remote", "git", "jenkins", "jira", "confluence", "wiki",
            "docs", "help", "support", "status", "app", "m", "mobile",
            "mobil", "panel", "cpanel", "whm", "webdisk", "forum",
            "shop", "store", "billing", "payment", "login", "register",
            "sso", "auth", "oauth", "cdn", "static", "img", "images",
            "media", "video", "tv", "radio", "stream", "assets",
            "download", "uploads", "file", "files", "backup", "db",
            "database", "mysql", "redis", "elastic", "kibana",
            "grafana", "prometheus", "monitor", "monitoring",
            "nagios", "zabbix", "splunk", "log", "logs",
            "stage", "staging", "prod", "production", "dev",
            "development", "test", "testing", "qa", "demo",
            "beta", "alpha", "release", "old", "new",
            "gateway", "router", "switch", "firewall", "proxy",
            "mail2", "mail1", "pop3", "imap", "smtp2",
            "ns3", "ns4", "dns2", "dns1", "ns0",
            "server", "server1", "server2", "webserver", "web1",
            "mailserver", "sql", "sqlserver", "db1", "mongodb",
            "api2", "api1", "api3", "graphql", "rest",
            "ws", "websocket", "wss", "rtmp", "rtsp",
            "sip", "voip", "phone", "fax", "printer",
            "camera", "security", "alarm", "sensor", "iot",
            "updates", "update", "patch", "patchserver",
            "license", "activation", "key", "keyserver",
            "tracking", "analytics", "stats", "counter",
            "job", "jobs", "career", "careers", "hr",
            "intranet", "portal", "my", "office", "outlook",
            "owa", "exchange", "lync", "skype", "teams",
            "zoom", "meet", "webex", "gotomeeting", "anydesk",
            "teamviewer", "rdp", "terminal", "console",
            "docker", "k8s", "kubernetes", "swarm", "rancher",
            "nexus", "artifactory", "maven", "npm", "pypi",
            "ci", "cd", "build", "deploy", "release",
            "sonar", "sonarqube", "codequality", "codacy",
            "hooks", "webhooks", "callback", "notify",
            "service", "services", "micro", "microservice",
            "soap", "xmlrpc", "rpc", "grpc", "thrift",
            "ldap", "ldaps", "radius", "tacacs", "kerberos",
            "ntp", "time", "clock", "timesync",
            "syslog", "syslog2", "snmp", "snmp2",
            "tftp", "sftp", "scp", "rsync", "webdav",
            "caldav", "carddav", "dav", "davs",
            "moodle", "canvas", "blackboard", "lms", "learn",
            "wordpress", "wp", "joomla", "drupal", "magento",
            "laravel", "symfony", "yii", "codeigniter", "cakephp",
            "ruby", "rails", "python", "django", "flask",
            "node", "nodejs", "express", "react", "vue",
            "angular", "next", "nuxt", "gatsby", "sapper",
            "index", "home", "main", "default", "landing",
            "page", "pages", "content", "contents", "blog2",
            "news", "newsletter", "magazine", "press", "basin",
            "partner", "partners", "ortak", "affiliate",
            "member", "members", "membership", "membersonly",
            "premium", "vip", "gold", "silver", "bronze",
            "dashboard", "kontrol", "yonetim", "management",
            "adminpanel", "admin2", "adm", "yönetim",
            "uygulama", "application", "apps", "app2",
        ]

        self.running = False

    def start_scan(self):
        domain = self.entry.get_text().strip()
        if not domain:
            self.status_label.set_text("Lütfen bir domain girin")
            return
        if self.running:
            return
        self.running = True
        self.scan_btn.set_sensitive(False)
        self.textbuffer.set_text("")
        self.progress.set_fraction(0)
        self.status_label.set_text("Taranıyor...")
        thread = threading.Thread(target=self.scan, args=(domain,), daemon=True)
        thread.start()

    def append_text(self, text):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, text + "\n")

    def scan(self, domain):
        found = 0
        total = len(self.common_subdomains)
        self.append_text(f"[*] {total} subdomain kontrol ediliyor...\n")
        for i, sub in enumerate(self.common_subdomains):
            if not self.running:
                break
            hostname = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(hostname)
                found += 1
                GLib.idle_add(self.append_text, f"[+] {hostname} -> {ip}")
            except socket.gaierror:
                pass
            GLib.idle_add(self.progress.set_fraction, (i + 1) / total)
        GLib.idle_add(self.finish_scan, domain, found)

    def finish_scan(self, domain, found):
        self.running = False
        self.scan_btn.set_sensitive(True)
        self.progress.set_fraction(1)
        self.status_label.set_text(f"Tarama tamamlandı: {found} subdomain bulundu ({domain})")
