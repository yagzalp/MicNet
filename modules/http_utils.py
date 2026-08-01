HTTP_STATUS = {
    200: "200 OK - Sayfa normal calisiyor, her sey yolunda",
    201: "201 Created - Kaynak basariyla olusturuldu",
    204: "204 No Content - Icerik yok, islem basarili",
    301: "301 Moved Permanently - Sayfa kalici olarak tasinmis",
    302: "302 Found - Sayfa gecici olarak baska adrese yonlendiriliyor",
    303: "303 See Other - Baska adrese yonlen",
    304: "304 Not Modified - Sayfa degismemis, cache kullanilabilir",
    307: "307 Temporary Redirect - Gecici yonlendirme",
    308: "308 Permanent Redirect - Kalici yonlendirme",
    400: "400 Bad Request - Istek hatali, sunucu anlamadi",
    401: "401 Unauthorized - Giris yapilmadi, yetkilendirme gerekli",
    403: "403 Forbidden - Erisim yasak, yetkiniz yok",
    404: "404 Not Found - Sayfa bulunamadi",
    405: "405 Method Not Allowed - Bu metoda izin verilmiyor",
    408: "408 Request Timeout - Istek zamani asimi",
    429: "429 Too Many Requests - Cok fazla istek, rate limit",
    500: "500 Internal Server Error - Sunucu ic hatasi",
    501: "501 Not Implemented - Sunucu bu metodu desteklemiyor",
    502: "502 Bad Gateway - Sunucu gecersiz yanit aldi",
    503: "503 Service Unavailable - Hizmet kullanilamiyor (bakim/asisiri yuk)",
    504: "504 Gateway Timeout - Ust sunucu zaman asimi",
}

COMMON_PORTS = {
    21: "FTP (Dosya Transferi) - sifresiz dosya transferi",
    22: "SSH (Guvenli Shell) - uzaktan komut satiri erisimi",
    23: "Telnet - guvenli OLMAYAN uzaktan erisim",
    25: "SMTP - e-posta gonderme",
    53: "DNS - domain cozumleme",
    80: "HTTP - web (sifresiz)",
    110: "POP3 - e-posta alma (sifresiz)",
    111: "RPC - uzak islem cagrisi",
    135: "RPC - Windows servisi",
    139: "NetBIOS - Windows dosya paylasimi",
    143: "IMAP - e-posta okuma",
    443: "HTTPS - guvenli web",
    445: "SMB - Windows dosya paylasimi",
    993: "IMAPS - guvenli IMAP",
    995: "POP3S - guvenli POP3",
    1433: "MSSQL - Microsoft SQL veritabani",
    1521: "Oracle - Oracle veritabani",
    2049: "NFS - dosya paylasimi",
    3306: "MySQL - MySQL veritabani",
    3389: "RDP - Windows uzak masaustu",
    5432: "PostgreSQL - PostgreSQL veritabani",
    5900: "VNC - uzak masaustu",
    6379: "Redis - Redis veritabani",
    8080: "HTTP-Proxy - alternatif HTTP (genelde proxy)",
    8443: "HTTPS-Alt - alternatif HTTPS",
    27017: "MongoDB - MongoDB veritabani",
}


def status_str(code):
    s = HTTP_STATUS.get(code)
    if s:
        return s
    if code < 300:
        return f"{code} Basarili"
    if code < 400:
        return f"{code} Yonlendirme"
    if code < 500:
        return f"{code} Istek hatasi"
    return f"{code} Sunucu hatasi"


def port_str(port):
    s = COMMON_PORTS.get(port)
    if s:
        return f"Port {port}: {s}"
    return f"Port {port}"
