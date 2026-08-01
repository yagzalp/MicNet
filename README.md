<div align="center">

<img src="https://raw.githubusercontent.com/yagzalp/Micnet/main/icon.svg" width="110" alt="MicNet Logo"/>

# 🛡️ MicNet

### Açık Kaynaklı, 37 Modüllü Siber Güvenlik Süiti

**Ağ Keşfi**  ·  **Port Tarama**  ·  **WiFi Analizi**  ·  **OSINT**  ·  **Web Güvenlik Testleri**  ·  **Şifre & Hash Araçları**

*Hepsi tek masaüstü uygulamasında.*

<br/>

[![License](https://img.shields.io/badge/Lisans-GPLv3-blue.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](#-kurulum)
[![GTK3](https://img.shields.io/badge/UI-GTK3-4A90D9?style=for-the-badge&logo=gtk&logoColor=white)](#)

[![Stars](https://img.shields.io/github/stars/yagzalp/Micnet?style=flat-square&color=yellow)](https://github.com/yagzalp/Micnet/stargazers)
[![Forks](https://img.shields.io/github/forks/yagzalp/Micnet?style=flat-square&color=blue)](https://github.com/yagzalp/Micnet/forks)
[![Issues](https://img.shields.io/github/issues/yagzalp/Micnet?style=flat-square&color=red)](https://github.com/yagzalp/Micnet/issues)
[![Last Commit](https://img.shields.io/github/last-commit/yagzalp/Micnet?style=flat-square&color=green)](https://github.com/yagzalp/Micnet/commits/main)

<br/>

[Kurulum](#-kurulum) • [Modüller](#-modüller) • [Kullanım](#-hızlı-başlangıç) • [Katkıda Bulunma](#-katkıda-bulunma) • [Lisans](#-lisans)

</div>

<br/>

---

## 📖 İçindekiler

<table>
<tr>
<td width="33%" valign="top">

**Genel**
- [Hakkında](#-hakkında)
- [Neden MicNet?](#-neden-micnet)
- [Hızlı Başlangıç](#-hızlı-başlangıç)

</td>
<td width="33%" valign="top">

**Kurulum**
- [Gereksinimler](#-kurulum)
- [Dağıtıma Göre Kurulum](#-kurulum)
- [Masaüstü Kısayolu](#️-masaüstü-kısayolu)

</td>
<td width="33%" valign="top">

**Detaylar**
- [Modül Listesi](#-modüller)
- [Yapılandırma](#-yapılandırma)
- [SSS](#-sık-sorulan-sorular)

</td>
</tr>
</table>

---

## 🎯 Hakkında

**MicNet**, sızma testi (pentest), ağ analizi ve OSINT çalışmaları için ihtiyaç duyulan araçları tek bir GTK3 masaüstü uygulamasında birleştiren, açık kaynaklı bir siber güvenlik paketidir.

<div align="center">

| 📊 26 | 🧩 37 | 📁 ~28 | 🐍 100% |
|:---:|:---:|:---:|:---:|
| Sekme | Modül | Dosya | Python |

</div>

SQL injection taramasından WiFi şifre kırmaya, ağ haritalamadan e-posta veri sızıntısı kontrolüne kadar geniş bir araç yelpazesi sunar — hepsi karanlık temalı, tek bir arayüzde.

> 💡 **AppImage** kullanıcıları için kurulum derdi yok — indir, çift tıkla, masaüstü kısayolu otomatik oluşsun.

### ✨ Neden MicNet?

- 🎨 **Tek arayüz** — 10+ farklı araç yerine tek bir uygulama
- 🇹🇷 **Türkçe odaklı** — arayüz, sözlükler ve açıklamalar Türkçe kullanıcılar için optimize edildi
- ⚡ **Paralel tarama** — çoğu modül thread pool ile hızlı çalışır
- 🔓 **Tamamen açık kaynak** — GPL-3.0 lisansı, kod tabanı şeffaf
- 🧱 **Modüler yapı** — her araç bağımsız bir Python dosyası, kolayca genişletilebilir

---

## 🚀 Hızlı Başlangıç

```bash
git clone https://github.com/yagzalp/Micnet.git
cd Micnet
pip install -r requirements.txt
python3 main.py
```

Alternatif olarak **AppImage** sürümünü indirip çift tıklamanız yeterli — kurulum gerekmez.

---

## ⚙️ Kurulum

<div align="center">

| Gereksinim | Açıklama |
|:---|:---|
| 🐍 Python | 3.8 veya üzeri |
| 📦 pip | Paket yöneticisi |
| 🖼️ GTK3 | Sistem paketi olarak kurulmalı |
| 🌐 İnternet | Bazı modüller (OSINT, breach kontrol) API kullanır |

</div>

<table>
<tr><th>Dağıtım</th><th>Komut</th></tr>
<tr>
<td><b>Debian / Ubuntu / Mint</b></td>
<td>

```bash
sudo apt install python3 python3-pip python3-gi gir1.2-gtk-3.0
```

</td>
</tr>
<tr>
<td><b>Arch Linux</b></td>
<td>

```bash
sudo pacman -S python python-pip gtk3 python-gobject
```

</td>
</tr>
<tr>
<td><b>Fedora</b></td>
<td>

```bash
sudo dnf install python3 python3-pip gtk3 python3-gobject
```

</td>
</tr>
</table>

Ardından her dağıtımda ortak adımlar:

```bash
cd micnet
pip install -r requirements.txt
python3 main.py
```

> ⚠️ **WifiScanner**, **Deauth** ve **WifiKir** modülleri için ayrıca `aircrack-ng` ve monitor mod destekli bir WiFi adaptörü gerekir.

### 🖥️ Masaüstü Kısayolu

MicNet'i terminalsiz, çift tıklayarak açmak için:

```bash
chmod +x install.sh
./install.sh
```

<div align="center">

| Script ne yapar? |
|:---|
| ✅ `run.sh` dosyasını çalıştırılabilir yapar |
| ✅ `micnet.desktop`'ı uygulama menüsüne (`~/.local/share/applications`) kaydeder |
| ✅ Masaüstüne kısayol ekler (varsa) |
| ✅ `Exec` / `Icon` yollarını kurulum dizininize göre otomatik ayarlar |

</div>

Kurulumdan sonra uygulama menüsünde **"MicNet"** arayabilir veya masaüstü simgesine çift tıklayabilirsiniz.

> 💡 GNOME/Nautilus'ta ilk açılışta *"Güvenilir mi? / Trust and Launch"* uyarısı çıkabilir — bu normaldir, onaylayın.

<details>
<summary><b>🔧 Manuel kurulum (script kullanmadan)</b></summary>
<br/>

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
| Modül | Açıklama |
|---|---|
| **Port Scanner** | Banner grabbing + Türkçe port açıklamaları |
| **Network Mapper** | Yerel ağdaki cihazları, MAC/üretici, açık portları haritalar |
| **ARP Detector** | ARP spoofing / MITM tespiti (tekli veya sürekli izleme) |

### 🕵️ OSINT
| Modül | Açıklama |
|---|---|
| **OSINT** | E-posta, domain, kullanıcı adı, IP modları; 9 platformda arama |
| **ReverseIP** | Aynı sunucudaki diğer siteleri bulur |
| **Subdomain Scanner** | 200+ kelime, 20 paralel thread |

### 🔑 Şifre & Hash
| Modül | Açıklama |
|---|---|
| **PwdStrength** | Entropi hesabı + brute-force süre tahmini |
| **Hash Tools** | 12 algoritma (MD5→SHA3, Blake2), HMAC, MD5 kırma |
| **EPosta Breach** | HIBP k-anonimite yöntemiyle sızıntı kontrolü |

</td><td width="50%" valign="top">

### 🌍 Web Güvenliği
| Modül | Açıklama |
|---|---|
| **SQLi** | Error-based & boolean-based SQL injection taraması |
| **DirBust** | 200+ kelime × 10 uzantı ile dizin/dosya keşfi |
| **CMS Detector** | WordPress, Joomla, Drupal, Magento, Laravel, ASP.NET |
| **URL Scanner** | Güvenlik başlıkları, Cloudflare/WAF tespiti |
| **Site Exploit** | Admin panel bulucu, açık dosya, varsayılan şifre denemesi |

### 📶 WiFi
| Modül | Açıklama |
|---|---|
| **WifiKir** | WPA/WPA2 handshake (.cap) sözlük saldırısı, 200+ dahili sözlük |

### ⚙️ Diğer
| Modül | Açıklama |
|---|---|
| **Settings Panel** | Shodan, VirusTotal, SecurityTrails, AbuseIPDB API yönetimi |

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

## ❓ Sık Sorulan Sorular

<details>
<summary><b>Uygulama açılmıyor, GTK hatası veriyor</b></summary>
<br/>

`python3-gi` ve `gir1.2-gtk-3.0` (veya dağıtımınıza göre karşılığı) paketlerinin kurulu olduğundan emin olun. Kurulum bölümündeki komutları tekrar çalıştırın.
</details>

<details>
<summary><b>WiFi modülleri çalışmıyor</b></summary>
<br/>

`aircrack-ng` kurulu olmalı ve WiFi adaptörünüz monitor moda geçebilmeli. Tüm adaptörler bu özelliği desteklemez.
</details>

<details>
<summary><b>API anahtarı olmadan hangi modüller sınırlı çalışır?</b></summary>
<br/>

Shodan olmadan OSINT'te IP sorgulaması temel seviyede kalır; VirusTotal, SecurityTrails ve AbuseIPDB anahtarları olmadan ilgili zenginleştirme adımları atlanır. Diğer tüm modüller anahtarsız da tam çalışır.
</details>

---

## 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Yeni bir modül eklemek, mevcut bir modülü iyileştirmek veya hata bildirmek isterseniz:

1. Bu repoyu **fork**'layın
2. Yeni bir dal oluşturun (`git checkout -b ozellik/yeni-modul`)
3. Değişikliklerinizi commit'leyin (`git commit -m 'Yeni modül: XYZ'`)
4. Dalınızı push'layın (`git push origin ozellik/yeni-modul`)
5. Bir **Pull Request** açın

Hata bildirimleri ve öneriler için [Issues](https://github.com/yagzalp/Micnet/issues) sekmesini kullanabilirsiniz.

---

## ⚠️ Uyarı ve Sorumluluk Reddi

> Bu araç **yalnızca kendi ağınızda** veya **yazılı izniniz olan sistemlerde** kullanılmak üzere tasarlanmıştır.
> İzinsiz aktif tarama, hedef sistemin kullanım koşullarını ve yürürlükteki yasaları ihlal edebilir.
> Geliştirici, aracın kötüye kullanımından doğacak sonuçlardan sorumlu tutulamaz.

---

## 📄 Lisans

Bu proje **[GPL-3.0](LICENSE)** lisansı altında dağıtılmaktadır.

<div align="center">
<br/>

**Geliştirici:** [@yagzalp](https://github.com/yagzalp)

⭐ *Projeyi faydalı bulduysanız bir yıldız bırakmayı unutmayın!* ⭐

<br/>

[![GitHub](https://img.shields.io/badge/GitHub-yagzalp-181717?style=for-the-badge&logo=github)](https://github.com/yagzalp)

</div>
