=================================================================
  MICNET v2.0 - SIBER GUVENLIK ARACI
  Modul Aciklamalari ve Detayli Kullanim Kilavuzu
=================================================================

Bu dokumanda MicNet'teki her bir modulun ne ise yaradigi, nasil
calistigi, hangi teknikleri kullandigi ve hangi durumlarda ne
sonuc verdigi detaylica anlatilmistir.


##################################################################
##  KURULUM VE CALISTIRMA
##################################################################

GEREKSINIMLER:
- Python 3.8+ ve pip
- GTK3 kutuphaneleri (sistem paketi)
- Internet baglantisi (bazi moduller API kullanir)

DEBIAN / UBUNTU / MINT:

  sudo apt install python3 python3-pip python3-gi gir1.2-gtk-3.0
  cd micnet
  pip install -r requirements.txt
  python3 main.py

ARCH LINUX:

  sudo pacman -S python python-pip gtk3 python-gobject
  cd micnet
  pip install -r requirements.txt
  python3 main.py

FEDORA:

  sudo dnf install python3 python3-pip gtk3 python3-gobject
  cd micnet
  pip install -r requirements.txt
  python3 main.py

NOTLAR:
- WifiScanner, Deauth, WifiKir modulleri icin ayrica
  aircrack-ng ve monitor mod destekli bir wifi adaptoru gerekir.
- API anahtarlari (istege bagli) Ayarlar sekmesinden girilir,
  ~/.config/micnet/config.json dosyasinda saklanir.
- Yalnizca KENDI aginizda ve izniniz olan sistemlerde kullanin.
  Aktif tarama yaptiginiz agin kullanim kosullarini ihlal edebilir.


##################################################################
##  YENI EKLENEN MODULLER
##################################################################


=================================================================
1. SQLi (SQL Injection Tarama)
=================================================================

NE ISE YARAR:
Bir web sitesinin veritabanina mudahale edilip edilemeyecegini
test eder. SQL injection, web uygulamalarindaki en kritik
guvenlik aciklarindan biridir. Basarili bir SQLi ile:
- Veritabanindaki tum kullanici bilgileri ele gecirilebilir
- Admin sifresi hash'i alinip kirilabilir
- Siteye admin olarak girilebilir
- Hatta sunucuya tam erisim bile saglanabilir

NASIL CALISIR (2 YONTEM):
1. Error-based: Hedef URL'ye sirasiyla su karakterleri ekler:
   ', ", ', %, "', '--, ), '), "), -- -
   Eger sayfa hata mesaji donduruyorsa (SQL syntax hatasi,
   "mysql_fetch_array()" vb.) zafiyet var demektir.
2. Boolean-based: Once normal sayfayi alir, sonra:
   - ' AND 1=1 --  (sayfa normal goruntulenir)
   - ' AND 1=2 --  (sayfa bos/hatali goruntulenir)
   Iki durum farkliysa zafiyet vardir.

NASIL KULLANILIR:
site.com/sayfa.php?id=1  seklinde bir URL yazilir. Sayfada id=,
page=, no=, urun= gibi parametre olmasi gerekir.

SINIRLAMALAR:
- POST parametrelerini test etmez (sadece GET)
- WAF veya Cloudflare varsa engelleyebilir
- Blind SQLi (zaman bazli) destegi yok, sadece error+boolean

ZAFIYET BULUNURSA:
Ekranda direkt olarak calistirilabilecek sqlmap komutu gosterilir:
  sqlmap -u "site.com/sayfa.php?id=1" --dbs


=================================================================
2. DirBust (Directory/File Brute Force)
=================================================================

NE ISE YARAR:
Web sitesindeki gizli dosya ve dizinleri bulur. Bir web sitesi
genelde herkese acik olmayan dizinler icerir. Ornegin:
- /admin/  (yonetim paneli)
- /backup/ (yedek dosyalari)
- /wp-admin/ (WordPress yonetimi)
- /.git/ (surum kontrol bilgisi, tum kaynak kodu aciga cikar)
- /sifre.txt, /password.zip (duz metin sifreler)
- /shell.php, /cmd.php (hackerin biraktigi shell)

NASIL CALISIR:
200+ kelimelik bir liste kullanir. Her kelimeyi 10 farkli uzanti
ile birlestirip hedef siteye HTTP istegi gonderir:
  site.com/admin/
  site.com/admin.php
  site.com/admin.html
  site.com/admin.asp
  site.com/admin.zip
  site.com/admin.bak
  site.com/admin.sql
  site.com/admin.old
  vs.

Toplam ~2500 istek gonderilir (200 kelime x ~10 uzanti + klasorler).
20 paralel thread ile hizli calisir. Durum kodu 200 veya 403
donen sayfalar "bulundu" olarak listelenir.

OZEL DURUMLAR:
- 403 kodu: Dizin var ama erisim engelli (iceri girme denemesi lazim)
- 301/302: Yonlendirme var, farkli bir sayfaya gidiyor
- 200: Dogrudan erisilebilir, acik demek

NASIL KULLANILIR:
https://site.com  yazilir, "Taramayi Baslat" tiklanir. Progress
bar ile ilerleme takip edilir.

NE BULABILIR:
- Admin panelleri (admin, panel, yonetim, kontrol, dashboard)
- Yedek dosyalari (backup.sql, dump.zip, yedek.bak)
- Config dosyalari (.env, config.php, database.yml)
- Shell'ler (shell.php, cmd.php, webshell.php, 404.php)
- Log dosyalari (access.log, error.log, hata.txt)
- Yukleme klasorleri (upload, files, images, dosyalar)
- API noktalari (api, v1, v2, rest, api.php)


=================================================================
3. CMS Detector (Icerik Yonetim Sistemi Tespiti)
=================================================================

NE ISE YARAR:
Bir web sitesinin hangi icerik yonetim sistemi (CMS) ile
calistigini tespit eder. CMS bilinince:
- Bilinen guvenlik aciklari aranabilir
- Versiyon bilgisi ile spesifik exploit'ler kullanilabilir
- Varsayilan admin yollari bilinir
- Varsayilan kullanici adlari/sifreler bilinir

DESTEKLENEN CMS'LER VE TESPIT YONTEMLERI:

WORDPRESS (pazarin ~%40'i):
  - /wp-admin/ klasoru var mi?
  - /wp-content/ klasoru var mi?
  - /wp-json/ REST API var mi?
  - /readme.html dosyasi var mi? (versiyonu icerir)
  - /wp-includes/ klasoru var mi?
  - Sayfa basliginda "wp-json" linki var mi?

JOOMLA:
  - /administrator/ klasoru var mi?
  - /components/ klasoru var mi?
  - /modules/ klasoru var mi?
  - /templates/ klasoru var mi?
  - /language/ klasoru var mi?

DRUPAL:
  - /CHANGELOG.txt var mi? (versiyon)
  - /node/1 sayfasi var mi?
  - /user/login sayfasi var mi?
  - /includes/ klasoru var mi?

MAGENTO:
  - /js/ klasoru var mi?
  - /skin/ klasoru var mi?
  - /app/ klasoru var mi?
  - /media/ klasoru var mi?
  - /index.php/backend/ admin paneli var mi?

LARAVEL:
  - /composer.json dosyasi var mi?
  - /artisan dosyasi var mi? (framework'e ozgu)
  - /vendor/ klasoru var mi?
  - /storage/ klasoru var mi?
  - /public/storage linki var mi?

ASP.NET:
  - /web.config dosyasi var mi?
  - /bin/ klasoru var mi?
  - /Content/ klasoru var mi?
  - /Scripts/ klasoru var mi?
  - .aspx uzantisi kullaniyor mu?

VERSIYON TESPITI:
Bazi CMS'ler versiyon bilgisini dosyalarinda acikca tasir:
- WordPress: readme.html, wp-includes/version.php, wp-json
- Drupal: CHANGELOG.txt (icinde versiyon numarasi)
- Joomla: language/en-GB/en-GB.xml (versiyon)
- Magento: /js/mage/adminhtml/version.js

NASIL KULLANILIR:
https://site.com yazilir, "Tespit Et" tiklanir.

NEDEN ONEMLI:
WordPress 4.0 ile 6.0 arasinda yuzlerce bilinen acik var.
Hangi surumu bulursan, o surume ait CVE (Common Vulnerabilities
and Exposures) kayitlarina bakip dogrudan exploit kullanabilirsin.
Ornegin "WordPress 5.3 - WooCommerce 3.8" icin bilinen bir
Remote Code Execution (RCE) acigi varsa, siteyi komple ele
gecirebilirsin.


=================================================================
4. ReverseIP (Ters IP Sorgulama)
=================================================================

NE ISE YARAR:
Bir web sitesinin barindigi sunucuda (IP adresinde) baska hangi
web sitelerinin oldugunu bulur. Bu bilgi penetration test'te
cok kritiktir. Sebebi:
- Hedef site guvenli olabilir ama ayni sunucudaki baska bir
  sitede acik bulursan, o acik ustunden ana sunucuya erisip
  tum siteleri ele gecirebilirsin
- "Server-Side Request Forgery" (SSRF) saldirilarinda bu bilgi
  kritiktir
- Virtual host taramasi icin de kullanilir

NASIL CALISIR:
2 farkli ucretsiz API kullanir:
1. HackerTarget: reverseip.hackertarget.com API'sine sorgu
   gonderir, JSON formatinda domain listesi doner
2. YouGetSignal: yougetsignal.com'un web arayuzune POST
   istegi gonderir, sayfayi HTML parse ederek domainleri cikarir

NASIL KULLANILIR:
Domain (site.com) veya IP (185.199.108.153) adresi yazilir.
"Tara"ya basildiginda 2 API'den de sonuc alinmaya calisilir.

ORNEK:
site.com -> 185.199.108.153
Ayni IP'de:
  site.com
  baska-site.com
  test-ortami.org
  forum-site.net
  vs.

SINIRLAMALAR:
- API'ler her zaman dogru sonuc vermeyebilir (ozellikle Cloudflare
  arkasindaki sitelerde)
- Buyuk hosting firmalarinda (AWS, DigitalOcean) ayni IP'de
  binlerce site olabilir
- Ucretsiz API'lerde rate limit olabilir


=================================================================
5. PwdStrength (Sifre Gucluk Testi)
=================================================================

NE ISE YARAR:
Bir sifrenin ne kadar guclu oldugunu matematiksel olarak
hesaplar. Zayif bir sifrenin ne kadar surede kirilacagini
gosterir.

NASIL CALISIR:

1. KARAKTER ANALIZI:
   - Uzunluk: Kac karakter?
   - Buyuk harf: ABC... -> kac tane?
   - Kucuk harf: abc... -> kac tane?
   - Rakam: 012... -> kac tane?
   - Ozel karakter: !@#$... -> kac tane?

2. ENTROPI HESABI (Shannon Entropy):
   Entropi = log2(karakter_seti_buyuklugu) x uzunluk
   - Sadece kucuk harf: 26 karakter -> 4.7 bit/karakter
   - + buyuk harf: 52 -> 5.7 bit/karakter
   - + rakam: 62 -> 5.95 bit/karakter
   - + ozel: 95 -> 6.57 bit/karakter
   Toplam entropi: bit x uzunluk
   Ornek: "Merhaba123!" = 10 x 6.57 = 65.7 bit

3. BRUTE-FORCE SURESI:
   Varsayilan hiz: 1 milyar hash/saniye (GPU ile)
   Sure = (karakter_seti^uzunluk) / (2 x hiz)
   Ornek: 8 karakterli kucuk harf = 26^8 / 2e9 = ~24 saat
   Ornek: 12 karakterli karma = 95^12 / 2e9 = ~milyarlarca yil

4. YAYGIN SIFRE KONTROLU:
   150+ bilinen zayif sifre ile karsilastirir:
   "123456", "password", "qwerty", "sifre12", "ankara06",
   "merhaba12", "admin123", "letmein" vs.
   Bu listede varsa entropiye bakilmaksizin "cok zayif" der.

CIKTI GOSTERGELERI:
- 0-25 bit: Aninda kirilir (saniyeler)
- 25-50 bit: Cok zayif (dakikalar)
- 50-70 bit: Zayif (saatler)
- 70-90 bit: Orta (gunler-haftalar)
- 90-120 bit: Guclu (yillar)
- 120+ bit: Cok guclu (milyonlarca yil)

GERCEK HAYATTA:
- "sifre12" -> ~0.0001 saniye (ani kirilir)
- "Ankara06" -> ~0.5 saniye
- "Merhaba123!" -> ~2 saat
- "Xk9#mP2$vL8q" -> ~15 milyar yil
- "evim" -> 0.000001 saniye


=================================================================
6. EPosta (Email Sizinti / Breach Kontrol)
=================================================================

NE ISE YARAR:
Bir e-posta adresinin gecmis veri sizintilarinda (data breach)
olup olmadigini kontrol eder. 2024 itibariyle milyarlarca hesap
sizdirilmis durumda. Bu modul sayesinde:
- Sifrenin ele gecirilip gecirilmedigini ogrenirsin
- Hangi sitelerdeki sifrenin calindigini gorursun
- Acilen hangi sifreleri degistirmen gerektigini bilirsin

NASIL CALISIR (K-ANONIMITE YONTEMI):
Bu modul sifreni veya e-postani HIBP sunucusuna gonderir.
Bu guvenli mi? Kesinlikle evet. Soyle calisir:

1. E-posta adresinin SHA-1 hash'ini alir
2. Hash'in ilk 5 karakterini HIBP API'sine gonderir
   (ornegin: "21BD1" gibi)
3. API, "21BD1" ile baslayan tum hash sonuclarini dondurur
   (yuzlerce hash doner, arasinda seninki de var)
4. Sen kendi hash'ini bu listede karsilastirirsin
5. Eslesme varsa sizintidasin demektir

Bu yontemde:
- Sifren HIBP sunucusuna HIC gitmez
- E-postan HIC gitmez
- Sadece 5 karakterlik bir hash on eki gonderilir
- HIBP bile hangi e-postayi sorguladigini bilemez

NE GORUNTULENIR:
- Toplam kac sizintida gorundugu
- Hangi sizintilar oldugu (LinkedIn 2012, Adobe 2013,
  Facebook 2019, Twitter 2022, vb.)
- Sizinti yili ve aciklama

ONEMLI:
Bu modul sadece HIBP veritabanindaki sizintilari kontrol
eder. Her sizinti burada olmayabilir. Ayrica sifrenin su an
gecerli olup olmadigini bilmez, sadece bir zamanlar sizdirildigini
soyler.

NASIL KULLANILIR:
ornek@mail.com yaz, "Kontrol Et" tikla.


=================================================================
7. ARP Detector (ARP Spoofing / MITM Tespiti)
=================================================================

NE ISE YARAR:
Agdaki ARP spoofing saldirilarini tespit eder. ARP spoofing
bir bilgisayar korsaninin kendini ag gecidi (gateway/modem)
gibi gostererek tum internet trafigini kendi uzerinden
gecirmesidir. Bu saldiri basarili olursa:

- Internet trafiginin TAMAMI saldirgan tarafindan gorulebilir
- Sifreler, banka bilgileri, mesajlasmalar okunabilir
- HTTPS bile bazen asilabilir (SSL stripping)
- Agdaki tum cihazlarin trafigi dinlenebilir

NASIL CALISIR:

1. ARP TABLOSU OKUMA:
   `ip neigh show` komutunu calistirir. Bu komut ARP
   tablosundaki tum kayitlari gosterir:
   IP -> MAC adresi eslesmeleri

2. ANALIZ:
   - Gateway IP'sini `ip route show default` ile bulur
   - Gateway'in MAC adresini not eder
   - Ayni MAC adresinde birden fazla IPv4 adresi var mi
     kontrol eder (bu spoofing'in en net isaretidir)
   - Gateway'in MAC'i baska bir IP tarafindan kullaniliyor mu
     kontrol eder

3. TESPIT:

   Normal durum:
   ```
   192.168.1.1 (gateway) -> aa:bb:cc:dd:ee:ff
   192.168.1.100 (sen)    -> 11:22:33:44:55:66
   192.168.1.101 (komsu)  -> 77:88:99:aa:bb:cc
   ```
   Herkesin farkli MAC'i var -> TEMIZ

   Spoofing var:
   ```
   192.168.1.1 (gateway) -> aa:bb:cc:dd:ee:ff
   192.168.1.100 (sen)    -> aa:bb:cc:dd:ee:ff  <-- AYNI MAC!
   192.168.1.50 (hacker)  -> aa:bb:cc:dd:ee:ff  <-- AYNI MAC!
   ```
   Senin ve hacker'in MAC'i gateway ile ayni -> SPOOFING VAR

NOT: IPv6 link-local adresleri (fe80:: ile baslayanlar) ayiklanir.
Bunlar normalde gateway'in hem IPv4 hem IPv6 adresinden gelir,
spoofing degildir, yanlis alarm vermemek icin filtrelenir.

OZELLIKLER:
- Tek seferlik tarama
- Surekli izleme modu (3 saniyede bir ARP tablosunu yeniden okur)

NASIL KULLANILIR:
Agda herhangi bir islem yapmaya gerek yok, dogrudan
"ARP Tablosunu Tara" tiklanir.

SINIRLAMALAR:
- Sadece local agdaki cihazlari gorur (modem arkasindakileri)
- Ag izole ise (guest WiFi daire ayri) tum cihazlari gormeyebilir


=================================================================
8. Network Mapper (Ag Haritalama)
=================================================================

NE ISE YARAR:
Yerel agdaki (ev/ofis agi) tum cihazlari bulur. Her cihazin
IP adresini, MAC adresini, ureticisini ve acik portlarini
listeler. Bu sayede:
- Agda kac cihaz var gorursun
- Tanimadigin bir cihaz varsa fark edersin
- Hangi cihazin hangi portlari acik bilirsin
- Cihazlarin markasini gorebilirsin (Apple/Android/TP-Link vs.)

NASIL CALISIR:

1. AG TARAMASI:
   192.168.1.1 - 192.168.1.254 arasindaki tum IP'lere paralel
   ping gonderir (254 ayni anda). Cevap verenler "aktif" kabul
   edilir.

2. MAC ADRESI ALMA:
   Her aktif IP icin ARP tablosundan MAC adresi okunur.
   MAC adresinin ilk 6 karakteri (OUI - Organizationally
   Unique Identifier) IEEE tarafindan kayit altina alinir.
   Bu OUI kodu ureticiyi belirler.

   Ornegin:
   - E0:D3:62 -> AirTies (modem)
   - 8E:46:57 -> Apple (iPhone/iPad)
   - 36:86:93 -> Samsung (Android)
   - F0:4D:A2 -> TP-Link
   - 08:00:28 -> Apple
   - 30:85:A9 -> Intel

3. PORT TARAMASI:
   Her aktif cihazda su portlari kontrol eder (TCP connect):
   - 21 (FTP - dosya transferi)
   - 22 (SSH - uzaktan erisim)
   - 80 (HTTP - web arayuzu)
   - 443 (HTTPS - guvenli web)
   - 8080 (HTTP alternatif)
   - 8443 (HTTPS alternatif)

   Port aciksa cihazin o portta bir servis calistirdigi anlamina
   gelir. Ornegin 80 ve 443 aciksa cihazin web arayuzu vardir.

4. GORUNTULEME:
   Sonuclar bir tabloda gosterilir:
   ```
   IP              MAC              Marka         Portlar
   192.168.1.1     e0:d3:62:07:0f:25 AirTies      80,443
   192.168.1.100   xx:xx:xx:xx:xx:xx (sen)         -
   192.168.1.101   8e:46:57:d3:52:ee Apple         -
   192.168.1.102   36:86:93:4d:32:dd Samsung       -
   ```

NASIL KULLANILIR:
IP (ornegin 192.168.1.0/24) yazilir veya bos birakilip
otomatik algilamaya birakilir. "Ag Tara" tiklanir.

NEDEN ONEMLI:
- Evinde tanimadigin bir cihaz varsa biri agina baglanmis olabilir
- Bir cihazin portu aciksa (ornegin 21/FTP) iceri girmek
  icin kullanilabilir
- Modemin web arayuzu aciksa varsayilan sifre denenebilir
- Guvenlik testi oncesi ag haritasi cikarmak ilk adimdir


=================================================================
9. Site Exploit (Web Sitesi Acik Tarama)
=================================================================

NE ISE YARAR:
Bir web sitesinde bilinen guvenlik aciklarini otomatik olarak
tarar. 3 ayri test yapar:

TEST 1 - ADMIN PANELI BULUCU:
Web sitelerinin yonetici panelleri genelde gizli URL'lerde
bulunur. Bu test 56 farkli populer admin yolunu dener:
   /admin, /panel, /yonetim, /kontrol, /dashboard,
   /wp-admin, /administrator, /backend, /management,
   /adminpanel, /yonetimpaneli, /giris, /login,
   /admin/login.php, /admin/index.php, /admin.php,
   /panel/login, /manager, /control, /adm, /admin1,
   /siteadmin, /webadmin, /sysadmin, /admin_area,
   /yonetim/login, /giris.php, /admin/login.html, ...

Bunlardan 200 kodu donen varsa admin paneline erisilebilir
demektir. 403 donen varsa panel var ama erisim engelli.

TEST 2 - ACIK DOSYA TARAYICI:
Web sitelerinde unutulmus, korunmasiz dosyalari arar:
   /.git/config          -> Tum kaynak kodu aciga cikar
   /.env                 -> Veritabani sifreleri, API anahtarlari
   /backup.sql           -> Tum veritabani
   /backup.zip           -> Site yedegi
   /wp-config.php.bak    -> WordPress sifreleri
   /phpinfo.php          -> Sunucu bilgileri
   /shell.php            -> Hacker shell'i
   /webshell.php         -> Hacker shell'i
   /config.php           -> Config dosyasi
   /database.sql         -> Veritabani
   /admin/backup.sql     -> Admin yedegi
   /dump.sql             -> Veritabani dump
   /robots.txt           -> Gizli dizinler (bazen burada yazar)
   /sitemap.xml          -> Tum sayfa listesi
   /crossdomain.xml      -> Flash guvenlik acigi
   /.htaccess            -> Sunucu yapilandirmasi
   /error.log            -> Hata loglari
   /access.log           -> Erisim loglari
   /wp-json/wp/v2/users  -> WordPress kullanici listesi
   ve 20+ dosya daha

TEST 3 - VARSAYILAN SIFRE DENEME:
Bircok web uygulamasi ve cihaz fabrika ayarlarindaki
kullanici adi ve sifre ile gelir. 43 kombinasyon dener:
   admin/admin, admin/12345, admin/123456, admin/12345678,
   admin/password, admin/1234, admin/1234567890,
   root/root, root/12345, root/toor, root/admin,
   admin/letmein, admin/welcome, admin/monkey,
   user/user, user/12345, user/password,
   guest/guest, test/test, test/12345,
   admin/admin123, admin/password123, admin/sifre,
   admin/parola, admin/123, admin/0, admin/1,
   admin/123456789, admin/11111111, admin/00000000,
   administrator/administrator, administrator/admin,
   Administrator/Administrator, Yonetici/12345,
   admin/admin1234, admin/!@#$%^, admin/admin2024,
   admin/security, admin/secure, admin/changeit,
   admin/abc123, admin/letmein123

KRITIK BULGULAR:
Admin paneli bulunduysa, acik dosya bulunduysa veya sifre
kirildiysa "KRITIK BULGU" olarak ayrica listelenir. Bunlar
dogrudan siteyi ele gecirmek icin kullanilabilir.

NASIL KULLANILIR:
https://site.com yazilir. Test tipi secilir (Admin Panel,
Acik Dosya, Sifre Deneme veya Hepsi). "Taramayi Baslat"
tiklanir.

THREAD POOL:
20 paralel istek ile calisir, hizlidir. Progress bar gosterir.


=================================================================
10. WifiKir (WiFi Sifre Kirma / WPA Cracking)
=================================================================

NE ISE YARAR:
WPA/WPA2 korumali kablosuz aglarin el sikismasi (handshake)
dosyasindan (.cap) sozluk saldirisi ile sifre kirmaya calisir.

NASIL CALISIR:

1. ON HAZIRLIK:
   WPA el sikismasi yakalamak icin once su adimlar gerekir
   (harici olarak):
   a) airodump-ng ile hedef ag taranir (BSSID, kanal, istemci)
   b) airodump-ng hedef aga kilitlenir: `airodump-ng -c KANAL
      --bssid HEDEF_MAC -w dosya wlan0mon`
   c) aireplay-ng ile istemci koparilir (deauth): `aireplay-ng
      -0 2 -a HEDEF_MAC -c ISTEMCI_MAC wlan0mon`
   d) Istemci tekrar baglanirken WPA el sikismasi .cap dosyasina
      kaydedilir

2. DOSYA ANALIZI:
   Scapy kutuphanesi ile .cap dosyasi analiz edilir:
   - Toplam paket sayisi
   - EAPOL paket sayisi (WPA el sikismasi icin en az 4 gerekir)
   - SSID (ag adi) tespiti
   - BSSID (modem MAC'i) tespiti

3. SOZLUK SALDIRISI:
   aircrack-ng binary'si ile sozluk saldirisi yapilir:
   `aircrack-ng -w sozluk.txt dosya.cap`
   Her kelime denenir, eslesme bulunursa "KEY FOUND" mesaji
   goruntulenir.

DAHILI SOZLUK:
200+ Turkce kelime icerir:
- Sehirler: ankara06, istanbul34, izmir35, adana01, konya42...
- Isimler: murat123, ahmet123, mehmet12, ali12345, ayse1234...
- Genel: sifre12, parola123, deneme123, test1234...
- Modem markalari: airties, tplink, netmaster, ttnet,
  turktelekom, superonline, vodafone...
- Yaygin: 12345678, password, qwerty123, admin1234...
- Mevsim: yaz2024, kis2024, bahar2023...
- Ozel: evim123, wifi768, modem123, home1234...

KULLANICI SOZLUGU:
Istegge bagli olarak harici bir sozluk dosyasi da yuklenebilir.
"Gez" butonu ile .txt dosyasi secilir.

AIRCRACK-NG KURULUMU:
Eger aircrack-ng sistemde kurulu degilse, otomatik olarak
~/.local/bin/ dizinindeki binary kullanilir. LD_PRELOAD ile
calistirilir (Arch Linux'ta `/usr/lib` yolunu bulmasi icin).

NASIL KULLANILIR:
.cap dosyasi secilir (Gez butonu ile), sozluk bos birakilirsa
dahili liste kullanilir. "Sifre Kir" tiklanir.

SINIRLAMALAR:
- WPA3 desteklemez (aircrack-ng WPA3 kirabilse de henuz sinirli)
- Dahili sozluk 200+ kelime, cok basit sifreleri kirmak icin
  yeterli; "rockyou.txt" gibi buyuk listeler icin harici
  sozluk kullanmak gerekir
- PMKID saldirisi desteklemez
- Monitor mod gerektiren (canli yakalama) islemleri modulun
  disinda yapilir


=================================================================
11. Settings Panel (Ayarlar / API Anahtar Yonetimi)
=================================================================

NE ISE YARAR:
Bazi modullerin calismasi icin harici API anahtarlari gerekir.
Bu panel sayesinde bu anahtarlar girilir ve kaydedilir.

API'LER:
- Shodan: Ag guvenligi ve IoT cihaz tarama (OSINT modulunde
  IP sorgulama icin)
- VirusTotal: Dosya/URL/domain zararli yazilim tarama
  (OSINT'te domain analizi icin)
- SecurityTrails: Domain ve subdomain bilgileri (OSINT'te
  domain ve subdomain tarama icin)
- AbuseIPDB: IP adresi raporlama ve sorgulama (bir IP'nin
  daha once kotuye kullanilip kullanilmadigini ogrenmek icin)

NASIL CALISIR:
Anahtarlar `~/.config/micnet/config.json` dosyasinda JSON
formatinda saklanir. Dosya soyle gorunur:
```json
{
    "shodan": "ANAHTAR",
    "virustotal": "ANAHTAR",
    "securitytrails": "ANAHTAR",
    "abuseipdb": "ANAHTAR"
}
```
API anahtarlari olmadan da moduller calisir ama bazi ozellikler
sinirli olur. Ornegin Shodan anahtari olmadan OSINT'te IP
sorgulamasi yapilamaz (sadece temel bilgiler gosterilir).


##################################################################
##  BASTAN YAZILAN MODULLER
##################################################################


=================================================================
OSINT (Acik Kaynak Istihbarati)
=================================================================

NE ISE YARAR:
Bir hedef hakkinda acik kaynaklardan (genel internet) bilgi
toplar. 4 ayri sekmesi vardir:

--- EMAIL MODU ---

1. Gecerli mi? -> Email formatini kontrol eder (a@b.c seklinde mi)
2. DNS kaydi var mi? -> Domainin MX (mail) kaydina bakar.
   Eger yoksa email adresi gecersiz sayilir.

3. HIBP sizinti sorgusu -> Email sizintida mi? (EmailBreach
   modulu ile ayni API)

4. Sosyal medya kontrolu -> 9 platformda email ile hesap var mi?
   Nasil yapar:
   - GitHub: `https://api.github.com/users/EMAIL` sorgusu
   - X (Twitter): Gravatar ile baglantili mi kontrol eder
   - Instagram: Kayit sayfasinda email kontrolu dener
   - Reddit: Kullanici profili kontrolu
   - YouTube: Google hesabi ile iliskili mi?
   - TikTok: Profil sayfasina HTTP istegi
   - Facebook: `https://www.facebook.com/search/top/?q=EMAIL`
   - Medium: `https://medium.com/@EMAIL` kontrolu
   - Linktree: `https://linktr.ee/EMAIL` kontrolu

   Her platform icin try/except kullanilir, biri hata verirse
   digerine gecer. Hicbiri calismazsa hata gostermez sadece
   "bulunamadi" der.

--- DOMAIN MODU ---

1. DNS kayitlari:
   - A (IPv4 adresleri)
   - AAAA (IPv6 adresleri)
   - MX (mail sunuculari)
   - NS (isim sunuculari)
   - TXT (SPF, DKIM, DMARC kayitlari - email guvenligi)

2. Web kontrol:
   - HTTP ve HTTPS olarak siteye erisim dener
   - Cloudflare tespiti (cf-ray header, __cfduid cookie)
   - Sunucu bilgisi (Apache, Nginx, IIS...)

3. Whois sorgulama:
   - Domain kime kayitli?
   - Ne zaman kaydedilmis, ne zaman bitiyor?
   - Kayit firmasi?

4. Subdomain tarama:
   200+ kelime ile subdomain taramasi yapar (Subdomain modulu
   ile ayni). Bulunan subdomainleri IP adresleriyle listeler.

5. Port kontrol:
   80 (HTTP) ve 443 (HTTPS) portlarini kontrol eder.

--- KULLANICI ADI MODU ---

Girilen kullanici adini 9 platformda arar:
   github.com/KULLANICIADI
   twitter.com/KULLANICIADI
   instagram.com/KULLANICIADI
   reddit.com/user/KULLANICIADI
   youtube.com/@KULLANICIADI
   tiktok.com/@KULLANICIADI
   facebook.com/KULLANICIADI
   medium.com/@KULLANICIADI
   linktr.ee/KULLANICIADI

Her platforma HTTP istegi gonderir, 200 kodu donuyorsa
hesap var demektir.

--- IP MODU ---

- Reverse DNS: IP'nin PTR kaydini sorgular (hostname bulur)
- Port kontrol: 80, 443, 22, 21, 8080 portlarini kontrol eder
- Web: HTTP/HTTPS arayuzu var mi kontrol eder

GENEL OZELLIK:
Tum istekler 10 saniye timeout ile korunur. Hicbir yerde
program takilip kalmaz. Bir API hata verirse sessizce gecer.


=================================================================
URL Scanner (Baglanti / HTTP Guvenlik Tarayicisi)
=================================================================

NE ISE YARAR:
Bir web sitesinin HTTP guvenlik basliklarini ve genel
guvenlik durumunu analiz eder. Bir sitenin ne kadar guvenli
oldugunu, hangi korumalari kullandigini ve nasil asilabilecegini
gosterir.

NASIL CALISIR:

1. BAGLANTI:
   - Once HTTPS dener (default)
   - HTTPS calismazsa HTTP'ye dusur
   - Chrome 120 User-Agent kullanir (gercek tarayici gibi)
   - 8 saniye timeout
   - Yonlendirmeleri takip eder (301, 302)

2. CLOUDFLARE TESPITI:
   Asagidaki sinyalleri arar:
   - `__cfduid` cookie'si var mi?
   - `cf-ray` header'i var mi?
   - `cf-cache-status` header'i var mi?
   - `server: cloudflare` header'i var mi?
   - HTML'de "Cloudflare" kelimesi geciyor mu?
   - "Attention Required" sayfasi geliyor mu?
   Eger Cloudflare varsa, sitenin gercek IP'sini bulmak
   gerektigi belirtilir.

3. WAF TESPITI (Web Application Firewall):
   Asagidaki WAF'lari algilar:
   - ModSecurity: `server: ModSecurity` header'i
   - AWS WAF: `x-amzn-RequestId`, `x-amzn-ErrorType`
   - Cloudflare: yukaridaki gibi
   - F5 BIG-IP: `x-<???>` pattern
   - Barracuda: `barracuda` header
   - Sucuri: `X-Sucuri-ID` header

4. GUVENLIK BASLIK ANALIZI:
   Her baslik icin 3 sey soyler: Ne ise yarar, neye karsi
   korur, nasil asilir.

   Ornek:
   `Strict-Transport-Security` (HSTS)
   - Ne ise yarar: Tarayiciya "bu siteye sadece HTTPS ile
     baglan" der, HTTP'ye dusurme saldirisini engeller
   - Korur: SSL stripping, MITM
   - Nasil asilir: HSTS preload listesinde degilse ilk
     baglantida atlanabilir

   `X-Frame-Options`
   - Ne ise yarar: Sayfanin iframe icinde goruntulenmesini
     engeller
   - Korur: Clickjacking (tik hirsizligi)
   - Nasil asilir: Yok, sadece bu header olmayan sitelerde
     clickjacking denenebilir

   `Content-Security-Policy`
   - Ne ise yarar: Hangi kaynaklardan icerik yuklenebilecegini
     belirler
   - Korur: XSS (Cross-Site Scripting)
   - Nasil asilir: CSP eksikse XSS acigi aranabilir

   `X-Content-Type-Options`
   - Korur: MIME type sniffing
   - Nasil: Yok, header yoksa zafiyetli sayilir

   `X-XSS-Protection`
   - Korur: Reflected XSS
   - Not: Modern tarayicilar bunu kullanmiyor ama yine de
     onemli bir gosterge

   Ayrica sunucu bilgisi: Apache/Nginx/IIS ve versiyonu

5. PORT KONTROL:
   Hedef IP'de 21, 22, 80, 443, 3306, 8080 portlarini kontrol
   eder. Acik portlar listelenir (ornegin 3306 aciksa MySQL
   veritabanina disaridan erisilebilir demektir).

CIKTI:
- Guvenli basliklar YESIL ile "Meuclud"
- Eksik basliklar KIRMIZI ile "Eksik"
- Cloudflare tespiti varsa belirtilir
- Acik portlar listelenir


##################################################################
##  IYILESTIRILEN MODULLER
##################################################################


=================================================================
Port Scanner (Port Tarama)
==================================================================

NE ISE YARAR:
Hedef IP'deki acik portlari ve bu portlarda calisan servisleri
bulur.

IYILESTIRMELER:

1. BANNER GRABBING:
   Port aciksa, TCP baglantisi yapar ve karsidan gelen ilk
   1024 byte'i okur (banner). Bu banner genelde servisin
   adini ve versiyonunu icerir:
   - "SSH-2.0-OpenSSH_7.4" -> OpenSSH 7.4
   - "220 ProFTPD 1.3.5" -> FTP sunucusu ve versiyon
   - "Apache/2.4.41" -> Web sunucusu

2. PORT ACIKLAMALARI:
   Her port icin Turkce aciklama gosterilir:
   - 21: FTP (Dosya Transferi) - genelde zayif sifreyle korunur
   - 22: SSH (Guvenli Shell) - sunucu yonetimi icin
   - 23: Telnet - sifresiz iletisim, tehlike
   - 25: SMTP (Email Gonderme)
   - 53: DNS (Domain Ad Sistemi)
   - 80: HTTP (Web)
   - 110: POP3 (Email Alma)
   - 143: IMAP (Email Alma)
   - 443: HTTPS (Guvenli Web)
   - 3306: MySQL (Veritabani) - disari aciksa buyuk risk
   - 3389: RDP (Uzak Masaustu)
   - 5432: PostgreSQL (Veritabani)
   - 5900: VNC (Uzak Masaustu)
   - 6379: Redis (Veritabani)
   - 8080: HTTP-Proxy (Web alternatif)
   - 8443: HTTPS-Proxy
   - 27017: MongoDB (Veritabani)


=================================================================
Hash Tools (Hash Islemleri)
=================================================================

NE ISE YARAR:
Metinlerin hash'lerini hesaplar, dogrular ve MD5 kirma yapar.

DESTEKLENEN ALGORITMALAR (12 adet):
- MD5 (128 bit) - en yaygin, kirilmasi en kolay
- SHA1 (160 bit) - eski, guvensiz sayilir
- SHA224 (224 bit)
- SHA256 (256 bit) - standard
- SHA384 (384 bit)
- SHA512 (512 bit) - en guclu SHA2
- SHA3-224 (224 bit) - yeni nesil
- SHA3-256 (256 bit)
- SHA3-384 (384 bit)
- SHA3-512 (512 bit)
- Blake2b (var uzunluk) - hizli ve guvenli
- Blake2s (var uzunluk)

HMAC SEKMESt:
HMAC (Hash-based Message Authentication Code) mesaj dogrulama
icin kullanilir. Bir mesajin gercekten belirtilen kisiden
geldigini ve degistirilmedigini dogrular. Desteklenen:
- HMAC-MD5
- HMAC-SHA1
- HMAC-SHA256
- HMAC-SHA512

MD5 KIRMA:
Genisletilmis sozluk ile MD5 hash'i kirmaya calisir.
Sozlukte yaygin sifreler, kelimeler ve Turkce kelimeler bulunur.
Basit MD5 hash'leri (ornegin `5f4dcc3b5aa765d61d8327deb882cf99`
-> "password") aninda kirilir.

NASIL KULLANILIR:
Metin yazilir, "Hashle" tiklanir, tum hashler tek ekranda
goruntulenir. HMAC icin ayri sekme, MD5 kirma icin ayri sekme.


=================================================================
Subdomain Scanner (Alt Alan Adi Tarama)
=================================================================

NE ISE YARAR:
Bir domainin alt alan adlarini (subdomain) bulur. Ornegin
google.com icin: mail.google.com, drive.google.com,
admin.google.com, calendar.google.com, etc.

IYILESTIRME:
Kelime listesi 200+'e cikarildi. Ornek kelimeler:
   admin, api, dev, test, staging, uat, alpha, beta,
   prod, production, development, qa, stage, sandbox,
   demo, app, web, portal, panel, crm, erp, mail,
   webmail, pop, imap, smtp, exchange, outlook,
   vpn, remote, access, secure, sso, login, auth,
   docs, wiki, confluence, jira, git, github, gitlab,
   bitbucket, svn, jenkins, travis, bamboo, teamcity,
   docker, k8s, kubernetes, swarm, registry,
   monitoring, nagios, zabbix, grafana, prometheus,
   db, database, mysql, postgres, mongo, redis,
   elastic, elk, kibana, logstash, fluentd,
   backup, restore, files, storage, nas, san,
   blog, news, forum, community, support, help,
   shop, store, cart, checkout, payment, billing,
   cloud, aws, azure, gcp, digitalocean, linode,
   xml, json, soap, rest, graphql, grpc,
   www, www2, www3, m, mobile, ios, android, api2,
   static, assets, cdn, media, img, image, video,
   proxy, mirror, cache, lb, loadbalancer,
   ns1, ns2, ns3, dns, mx, mail1, mail2,
   server, server1, node, node1, web1, web2,
   test1, test2, admin1, admin2, dev1, dev2,
   school, edu, uni, campus, ogrenci, personel,
   tr, en, de, fr, es, it, pt, ru, ar, cn, jp

Genisletilmis liste ile daha fazla subdomain bulunur ve 20
paralel thread ile hizli calisir. Progress bar gosterilir.


##################################################################
##  UI EKLENTILERI
##################################################################

- 26 sekme (orijinalde 17'ydi, 9 yeni modul eklendi + OSINT)
- HeaderBar'dan kapat/kucult/kapla butonlari kaldirildi
  (Alt+F4 ile kapatilir)
- "Ciktiyi Kaydet" butonu -> Acik sekmedeki TextView icerigini
  TXT veya HTML olarak kaydeder
- HTTP kod aciklamalari (200 OK, 403 Yasak, 404 Bulunamadi...)
  http_utils.py modulunde tanimlidir
- Port aciklamalari (22: SSH, 3306: MySQL...)
- Progress bar (subdomain, dirbuster, exploit taramalarinda)
- Karanlik tema (catppuccin esintili, indigo/pembe vurgular)
- Toolbar bilgi satiri (surum, saat, export)
- Font: Fira Code / JetBrains Mono (monospace cikti icin)


##################################################################
##  TOPLAM DEGISIKLIK
##################################################################

YENI MODULLER (9):
  sql_injection.py, dir_buster.py, cms_detector.py,
  reverse_ip.py, pwd_strength.py, email_breach.py,
  arp_detector.py, network_mapper.py, site_exploit.py

BASTAN YAZILANLAR (3):
  osint.py, url_scanner.py, wifi_crack.py

IYILESTIRILENLER (5):
  subdomain.py (200+ kelime), hash_tools.py (SHA3, HMAC),
  port_scanner.py (banner), http_utils.py (kod+port aciklama),
  settings_panel.py (API anahtarlari)

YARDIMCI DOSYALAR (3):
  http_utils.py, api_helper.py, settings_panel.py

YAPILANDIRMA:
  ~/.config/micnet/config.json (API anahtarlari)

TOPLAM MODUL DOSYASI: ~28 adet

=================================================================
