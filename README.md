<div align="center">
<img src="icon.svg" width="110" alt="MicNet icon">

# MicNet

### Açık Kaynaklı, Çok Modüllü Siber Güvenlik Test Aracı

Ağ keşfi ve port tarama · WiFi analizi · OSINT · Web güvenlik testleri · Şifre/hash araçları

Hepsi tek bir masaüstü uygulamasında.

<p>
<img src="https://img.shields.io/badge/version-v3.0-blue" alt="Version">
<img src="https://img.shields.io/badge/modules-57-brightgreen" alt="Modules">
<img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License">
<img src="https://img.shields.io/badge/platform-Linux-2f2f2f?logo=linux&logoColor=white" alt="Platform">
<img src="https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/GUI-GTK3-e01b24?logo=gtk&logoColor=white" alt="GTK3">
</p>

<p>
<a href="https://github.com/yagzalp/MicNet/releases/latest"><img src="https://img.shields.io/badge/⬇️_Download-AppImage-success?style=for-the-badge" alt="Download"></a>
</p>

<p>
  <a href="#-hızlı-başlangıç"><b>Hızlı Başlangıç</b></a> ·
  <a href="#-modüller"><b>Modüller</b></a> ·
  <a href="#️-yapılandırma"><b>Yapılandırma</b></a> ·
  <a href="#-bilinen-sorunlar"><b>Bilinen Sorunlar</b></a> ·
  <a href="#️-sorumluluk-reddi"><b>Sorumluluk Reddi</b></a>
</p>

</div>

<br>

> MicNet, sızma testi ve güvenlik değerlendirmesi sürecinde ihtiyaç duyacağınız araçları — ağ haritalamadan WPA kırmaya, SQL injection taramasından OSINT'e kadar — **tek bir masaüstü uygulamasında** birleştirir.

<br>

## ⚠️ Bilinen Sorunlar

> **AppImage bazı dağıtımlarda açılmayabilir.** Mevcut AppImage, güncel bir glibc (2.43+) gerektiren kütüphanelerle derlenmiş durumda. Arch Linux / Manjaro gibi rolling-release dağıtımlarda sorunsuz çalışır; ancak Ubuntu, Debian, Fedora gibi bazı stabil dağıtımlarda **"GLIBC_2.43 not found"** hatasıyla açılmayabilir.
>
> Bu durumda **kaynak koddan kurulum** ([aşağıya bakın](#-kaynak-koddan-kurulum)) sorunsuz çalışır. AppImage'ın daha eski/uyumlu bir ortamda yeniden derlenmesi planlanıyor.

<br>

## 🚀 Hızlı Başlangıç

En hızlı yol — **kurulum yok, derleme yok**:

1. [**Releases**](https://github.com/yagzalp/MicNet/releases/latest) sayfasından `MicNet-x86_64.AppImage` dosyasını indirin
2. Çalıştırılabilir yapın:
   ```bash
   chmod +x MicNet-x86_64.AppImage
   ```
3. Çift tıklayın veya çalıştırın:
   ```bash
   ./MicNet-x86_64.AppImage
   ```

İlk çalıştırmada uygulama otomatik olarak masaüstünüze ve uygulama menünüze bir kısayol ekler — bir sonraki açılışta doğrudan oradan başlatabilirsiniz.

AppImage açılmıyorsa yukarıdaki [Bilinen Sorunlar](#-bilinen-sorunlar) bölümüne bakıp kaynak koddan kuruluma geçin.

<br>

## 🛠 Kaynak Koddan Kurulum

**Gereksinimler:** Python 3.8+, pip, GTK3 kütüphaneleri, internet bağlantısı (bazı modüller API kullanır). WiFi kırma modülleri için ayrıca `aircrack-ng` ve monitor moda uygun bir kablosuz adaptör gerekir.

<table>
<tr><th>Dağıtım</th><th>Komutlar</th></tr>
<tr>
<td><b>Debian / Ubuntu / Mint</b></td>
<td>

```bash
sudo apt install python3 python3-pip python3-gi gir1.2-gtk-3.0
git clone https://github.com/yagzalp/MicNet.git && cd MicNet
pip install -r requirements.txt
python3 main.py
```

</td>
</tr>
<tr>
<td><b>Arch Linux</b></td>
<td>

```bash
sudo pacman -S python python-pip gtk3 python-gobject
git clone https://github.com/yagzalp/MicNet.git && cd MicNet
pip install -r requirements.txt
python3 main.py
```

</td>
</tr>
<tr>
<td><b>Fedora</b></td>
<td>

```bash
sudo dnf install python3 python3-pip gtk3 python3-gobject
git clone https://github.com/yagzalp/MicNet.git && cd MicNet
pip install -r requirements.txt
python3 main.py
```

</td>
</tr>
</table>

**Masaüstü kısayolu istiyorsanız** (opsiyonel), kurulumdan sonra:

```bash
chmod +x install.sh
./install.sh
```

Bu, uygulama menünüze ve masaüstünüze bir MicNet kısayolu ekler.

<br>

## 📦 Modüller

`app.py` içindeki modül tanımlarına göre MicNet **5 kategoride toplam 57 modül** içerir.

### 🔎 Keşif & Analiz (19)

Subdomain · OSINT · Domain · WHOIS · DNS · Reverse IP · Konum · Port · URL · CMS · DNSZone · Headers · Robots · Metadata · Status · S3 · Tech · Links · Emails

### 🕸️ Web Güvenliği (15)

SQLi · DirBust · Exploit · SSL · WAF · CVE · Blacklist · EPosta · XSS · Redirect · LFI · Komut · CORS · Yedek · SHead

### 📡 Ağ & WiFi (8)

WiFi · WiFi Crack · Deauth · ARP · Ağ · MITM · Honeypot · Cihazlar

### 🧰 Araç Kutusu (10)

Şifre · Password Test · Hash · MAC · Kodla · Subnet · Mail · Password Leak · JWT · File Hash

### ⚙️ Sistem (5)

Ayarlar · Sistem Bilgi · Ağ Bilgi · Süreçler · Temalar

<br>

## ⚙️ Yapılandırma

Bazı modüller (ör. IP itibar sorgulama, gelişmiş domain analizi) harici API anahtarları ile daha kapsamlı sonuç verir. Bu anahtarlar **isteğe bağlıdır** — girilmese de modüller temel işlevleriyle çalışmaya devam eder.

Anahtarlar, uygulama içindeki **Ayarlar** sekmesinden girilir ve şu dosyada saklanır:

```
~/.config/micnet/config.json
```

```json
{
    "shodan": "ANAHTARINIZ",
    "virustotal": "ANAHTARINIZ",
    "securitytrails": "ANAHTARINIZ",
    "abuseipdb": "ANAHTARINIZ"
}
```

<br>

## 🧱 Proje Yapısı

```
MicNet/
├── modules/              # Tüm modül dosyaları (57 modül)
├── app.py                # Arayüz mantığı / ana uygulama sınıfı
├── main.py               # Giriş noktası
├── icon.svg              # Uygulama ikonu
├── micnet.desktop         # Linux masaüstü kısayolu şablonu
├── install.sh             # Kaynak koddan kurulumda kısayol oluşturur
├── run.sh                 # Bağımlılık kontrolü + başlatma betiği
├── requirements.txt      # Python bağımlılıkları
└── LICENSE               # GPL-3.0 lisansı
```

<br>

## ⚠️ Sorumluluk Reddi

> MicNet **yalnızca eğitim ve yasal sızma testi** amaçlıdır.

- Bu aracı **yalnızca kendi ağınızda** veya **yazılı izniniz olan** sistemlerde kullanın.
- İzinsiz sistemlere yönelik tarama, brute-force veya kimlik bilgisi denemesi bulunduğunuz ülkenin yasalarına göre **suç teşkil edebilir**.
- Aktif ağ taraması hedef ağın kullanım koşullarını ihlal edebilir.
- Geliştirici, bu aracın kötüye kullanımından doğacak zararlardan **sorumlu tutulamaz**.

<br>

## 📄 Lisans

Bu proje **GPL-3.0** lisansı altındadır — detaylar için [LICENSE](LICENSE) dosyasına bakın.

<br>

<div align="center">

### ⭐ Projeyi Beğendiyseniz

Bir yıldız bırakmak, projenin gelişmesine katkı sağlar ve daha fazla kişiye ulaşmasına yardımcı olur.

**[⭐ Star ver](https://github.com/yagzalp/MicNet)** · **[🐛 Hata bildir](https://github.com/yagzalp/MicNet/issues)** · **[🔀 Fork'la](https://github.com/yagzalp/MicNet/fork)**

<br>

Made with 🛡️ by [**yagzalp**](https://github.com/yagzalp)

</div>
