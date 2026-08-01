<div align="center">

# 🛡️ Micnet

**Açık kaynaklı, 37 modüllü siber güvenlik aracı**

Ağ keşfi ve port tarama · WiFi analizi · OSINT · Web güvenlik testleri · Şifre araçları — hepsi tek uygulamada.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux-yellow?logo=linux)
![GTK3](https://img.shields.io/badge/UI-GTK3-4A90D9)

</div>

---

## 📋 İçindekiler

- [Hakkında](#-hakkında)
- [Hızlı Başlangıç](#-hızlı-başlangıç)
- [Kurulum](#️-kurulum)
- [Modüller](#-modüller)
- [Yapılandırma](#-yapılandırma)
- [Uyarı ve Sorumluluk Reddi](#️-uyarı-ve-sorumluluk-reddi)
- [Lisans](#-lisans)

---

## 🎯 Hakkında

Micnet, sızma testi (pentest), ağ analizi ve OSINT çalışmaları için gereken araçları tek bir masaüstü uygulamasında toplayan, GTK3 tabanlı açık kaynaklı bir siber güvenlik paketidir. **26 sekme** ve **~28 modül dosyası** içerir; SQL injection taramasından WiFi şifre kırmaya, ağ haritalamadan e-posta sızıntı kontrolüne kadar geniş bir yelpazede araç sunar.

> 💡 **AppImage** kullanıcıları için kurulum gerektirmez — indirip çift tıklamanız yeterli, masaüstü kısayolu otomatik oluşturulur.

---

## 🚀 Hızlı Başlangıç

```bash
git clone https://github.com/yagzalp/Micnet.git
cd Micnet
pip install -r requirements.txt
python3 main.py
```

---

## ⚙️ Kurulum

### Gereksinimler

- Python 3.8+
- pip
- GTK3 kütüphaneleri (sistem paketi)
- İnternet bağlantısı (bazı modüller API kullanır)

### Debian / Ubuntu / Mint

```bash
sudo apt install python3 python3-pip python3-gi gir1.2-gtk-3.0
cd micnet
pip install -r requirements.txt
python3 main.py
```

### Arch Linux

```bash
sudo pacman -S python python-pip gtk3 python-gobject
cd micnet
pip install -r requirements.txt
python3 main.py
```

### Fedora

```bash
sudo dnf install python3 python3-pip gtk3 python3-gobject
cd micnet
pip install -r requirements.txt
python3 main.py
```

> ⚠️ **WifiScanner**, **Deauth** ve **WifiKir** modülleri için ayrıca `aircrack-ng` ve monitor mod destekli bir WiFi adaptörü gerekir.

### 🖥️ Masaüstü Kısayolu (Uygulama Menüsüne Ekleme)

Kurulumdan sonra MicNet'i terminalsiz, çift tıklayarak açmak için:

```bash
chmod +x install.sh
./install.sh
```

Bu script otomatik olarak:
- `run.sh` dosyasını çalıştırılabilir yapar
- `micnet.desktop` dosyasını mevcut kullanıcının **uygulama menüsüne** (`~/.local/share/applications`) kaydeder
- Varsa **masaüstüne** de bir kısayol ekler
- Yolları (`Exec`, `Icon`) bulunduğunuz dizine göre otomatik ayarlar — elle düzenlemenize gerek kalmaz

Kurulumdan sonra:
- Uygulama menüsünde **"MicNet"** araması yapabilir,
- veya masaüstündeki simgeye çift tıklayabilirsiniz.

> 💡 GNOME/Nautilus kullanıyorsanız masaüstü simgesine ilk çift tıklamada *"Güvenilir mi? / Trust and Launch"* uyarısı çıkabilir — bu normaldir, onaylamanız yeterli.

<details>
<summary>Manuel kurulum (script kullanmadan)</summary>

```bash
chmod +x run.sh
mkdir -p ~/.local/share/applications
cp micnet.desktop ~/.local/share/applications/
# Exec= ve Icon= satırlarındaki yolları kendi kurulum dizininize göre düzenleyin
nano ~/.local/share/applications/micnet.desktop
update-desktop-database ~/.local/share/applications/
```

</details>

---

## 🧩 Modüller

<table>
<tr><td width="50%" valign="top">

### 🌐 Ağ & Sistem
- **Port Scanner** — banner grabbing + Türkçe port açıklamaları
- **Network Mapper** — yerel ağdaki cihazları, MAC/üretici ve açık portları haritalar
- **ARP Detector** — ARP spoofing / MITM tespiti (tek seferlik veya sürekli izleme)

### 🕵️ OSINT
- **OSINT** — e-posta, domain, kullanıcı adı ve IP modları; 9 sosyal platformda arama
- **ReverseIP** — aynı sunucudaki diğer siteleri bulur
- **Subdomain Scanner** — 200+ kelimelik liste, 20 paralel thread

### 🔑 Şifre & Hash
- **PwdStrength** — entropi hesabı + brute-force süre tahmini
- **Hash Tools** — 12 algoritma (MD5→SHA3, Blake2), HMAC, MD5 kırma
- **EPosta (Breach Kontrol)** — HIBP k-anonimite yöntemiyle sızıntı kontrolü

</td><td width="50%" valign="top">

### 🌍 Web Güvenliği
- **SQLi** — error-based & boolean-based SQL injection taraması
- **DirBust** — 200+ kelime × 10 uzantı ile dizin/dosya keşfi
- **CMS Detector** — WordPress, Joomla, Drupal, Magento, Laravel, ASP.NET tespiti
- **URL Scanner** — güvenlik başlıkları, Cloudflare/WAF tespiti
- **Site Exploit** — admin paneli bulucu, açık dosya tarayıcı, varsayılan şifre denemesi

### 📶 WiFi
- **WifiKir** — WPA/WPA2 handshake (.cap) sözlük saldırısı, 200+ Türkçe dahili sözlük

### ⚙️ Diğer
- **Settings Panel** — Shodan, VirusTotal, SecurityTrails, AbuseIPDB API anahtar yönetimi

</td></tr>
</table>

---

## 🔧 Yapılandırma

İsteğe bağlı API anahtarları `~/.config/micnet/config.json` dosyasında saklanır:

```json
{
    "shodan": "ANAHTAR",
    "virustotal": "ANAHTAR",
    "securitytrails": "ANAHTAR",
    "abuseipdb": "ANAHTAR"
}
```

API anahtarları olmadan da modüller çalışır, ancak bazı özellikler (örn. Shodan IP sorgulama) sınırlı olur.

---

## ⚠️ Uyarı ve Sorumluluk Reddi

Bu araç **yalnızca kendi ağınızda** veya **yazılı izniniz olan sistemlerde** kullanılmak üzere tasarlanmıştır. İzinsiz aktif tarama, hedef sistemin kullanım koşullarını ve yürürlükteki yasaları ihlal edebilir. Geliştirici, aracın kötüye kullanımından doğacak sonuçlardan sorumlu tutulamaz.

---

## 📄 Lisans

Bu proje [GPL-3.0](LICENSE) lisansı altında dağıtılmaktadır.

<div align="center">

Geliştirici: [@yagzalp](https://github.com/yagzalp)

</div>
