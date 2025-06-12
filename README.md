# Kumpulan Alat Investigasi Domain dan Aset Web

Proyek ini berisi kumpulan skrip Python yang dirancang untuk membantu dalam investigasi domain, pencarian IP asli di balik layanan CDN, dan analisis aset web.

## Daftar Isi

- Tujuan Proyek
- Alat-alat yang Termasuk
  - `ipFinder.py`
  - `hashLookup.py`
  - `parsing.py`
- Faktor Keberhasilan dan Penghambat Penemuan Origin IP
  - Faktor Pendukung Keberhasilan
  - Faktor Penghambat
- Persyaratan Sistem
- Instalasi
  - Ketergantungan Python
  - Alat Eksternal
- Cara Penggunaan
  - `ipFinder.py`
  - `hashLookup.py`
  - `parsing.py`
- Output
- Catatan Penting

## Tujuan Proyek

Tujuan utama dari kumpulan alat ini adalah untuk:
1.  Mengumpulkan informasi sebanyak mungkin tentang sebuah domain target.
2.  Mencoba menemukan alamat IP asli (origin IP) dari server yang mungkin tersembunyi di balik layanan Content Delivery Network (CDN) atau proksi lainnya.
3.  Menganalisis aset-aset (seperti gambar, skrip JavaScript, CSS) yang terkait dengan sebuah situs web untuk menemukan potensi keterkaitan dengan layanan atau server lain.
4.  Mengekstrak domain eksternal yang direferensikan oleh sebuah halaman web.

## Alat-alat yang Termasuk

### `ipFinder.py`
Skrip ini bertujuan untuk melakukan enumerasi subdomain, resolusi IP, pencarian MX record, dan pengecekan kebocoran file `.env` melalui Wayback Machine untuk domain target.

**Fitur Utama:**
- Enumerasi subdomain menggunakan `subfinder`.
- Resolusi subdomain ke alamat IP dan deteksi CDN menggunakan `httpx`.
- Pencarian MX record dan resolusi IP host MX menggunakan `dig`.
- Pengecekan arsip Wayback Machine untuk file `.env` yang mungkin terekspos.
- Menyediakan tautan cepat ke SecurityTrails dan crt.sh untuk investigasi lebih lanjut.

### `hashLookup.py`
Skrip ini mengekstrak aset (gambar, skrip, stylesheet, dll.) dari URL target, menghitung hash (SHA1, MD5) dari aset tersebut, dan menghasilkan tautan pencarian untuk hash tersebut di berbagai mesin pencari (Google, Censys, Shodan).

**Fitur Utama:**
- Ekstraksi URL aset dari berbagai tag HTML (`<img>`, `<script>`, `<link>`, dll.).
- Pengambilan dan hashing konten aset (SHA1 dan MD5).
- Pembuatan tautan pencarian untuk hash di Google, Censys, dan Shodan.
- Berguna untuk menemukan di mana lagi aset yang sama mungkin di-host, yang berpotensi mengungkap infrastruktur terkait.

### `parsing.py`
Skrip ini mengambil konten dari URL target dan mengekstrak semua domain eksternal yang direferensikan dalam tag HTML seperti `iframe`, `script`, `img`, `link`, dan tag meta refresh.

**Fitur Utama:**
- Pengambilan konten HTML dari URL target.
- Parsing HTML untuk menemukan URL eksternal.
- Ekstraksi dan pemfilteran domain unik dari URL yang ditemukan.
- Berguna untuk memahami layanan pihak ketiga yang digunakan oleh situs web atau domain terkait lainnya.

## Faktor Keberhasilan dan Penghambat Penemuan Origin IP

Penemuan origin IP, terutama ketika sebuah situs menggunakan CDN, bisa menjadi tantangan. Berikut adalah beberapa faktor yang mempengaruhinya:

### Faktor Pendukung Keberhasilan:
*   **Kesalahan Konfigurasi DNS:** Catatan DNS lama (misalnya, A record sebelum migrasi ke CDN) yang masih dapat ditemukan di basis data sejarah DNS.
*   **Subdomain Tidak Terlindungi CDN:** Beberapa subdomain mungkin tidak diarahkan melalui CDN dan langsung menunjuk ke IP asli.
*   **MX Records:** Mail server (MX records) terkadang di-host pada infrastruktur yang sama dengan server web dan tidak melalui CDN.
*   **Layanan Lain pada IP Asli:** Layanan seperti FTP, SSH, atau panel kontrol yang berjalan pada IP asli dan dapat ditemukan melalui pemindaian atau kebocoran informasi.
*   **Kebocoran Informasi:** File sensitif (seperti `.env` yang diarsipkan Wayback Machine), komentar di kode sumber, atau header HTTP kustom dapat membocorkan IP asli.
*   **Sejarah Sertifikat SSL/TLS:** Layanan seperti `crt.sh` dapat menunjukkan sertifikat yang pernah diterbitkan untuk domain, yang mungkin mencakup IP asli sebelum penggunaan CDN.
*   **API atau Endpoint Tersembunyi:** Beberapa API atau endpoint mungkin tidak dikonfigurasi untuk berjalan melalui CDN.
*   **Pencarian Hash Aset (`hashLookup.py`):** Jika aset unik dari situs target ditemukan di situs lain yang tidak menggunakan CDN, ini bisa menjadi petunjuk.

### Faktor Penghambat:
*   **Implementasi CDN yang Baik:** Layanan CDN modern (Cloudflare, Akamai, AWS CloudFront, dll.) sangat efektif dalam menyembunyikan IP asli.
*   **Semua Layanan Melalui CDN:** Jika semua layanan (web, email, API) dirutekan melalui CDN, akan lebih sulit menemukan IP asli.
*   **Penggunaan Alamat IP Dinamis:** Jika server menggunakan IP dinamis atau infrastruktur sering berubah.
*   **Layanan Privasi WHOIS:** Menyembunyikan detail kontak pemilik domain.
*   **Tidak Ada Sejarah DNS yang Signifikan:** Jika domain baru atau selalu menggunakan CDN sejak awal.
*   **Firewall yang Ketat:** Firewall pada server asli yang hanya mengizinkan koneksi dari IP CDN.

## Persyaratan Sistem

*   Python 3.7+
*   Sistem operasi berbasis Linux/macOS (karena ketergantungan pada `dig`, `subfinder`, `httpx`). Windows mungkin memerlukan WSL atau penyesuaian.
*   Koneksi internet aktif.

## Instalasi

1.  **Clone Repositori (jika ada):**
    ```bash
    git clone https://github.com/Eko-347m4n/infra-trace-tools
    cd infra-trace-tools
    ```

2.  **Ketergantungan Python:**
    Disarankan untuk menggunakan virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Untuk Linux/macOS
    # venv\Scripts\activate   # Untuk Windows
    ```
    Instal pustaka Python yang dibutuhkan:
    ```bash
    pip install requests beautifulsoup4
    ```

3.  **Alat Eksternal:**
    Pastikan alat-alat berikut terinstal dan berada dalam PATH sistem Anda:
    *   **Subfinder:** Alat enumerasi subdomain.
        *   Instalasi: `go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest`
        *   Pastikan `$GOPATH/bin` atau `$HOME/go/bin` ada di PATH Anda.
    *   **HTTPX:** Toolkit HTTP serbaguna.
        *   Instalasi: `go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest`
    *   **Dig:** Alat kueri DNS. Biasanya sudah terinstal di sistem Linux/macOS.
        *   Untuk Debian/Ubuntu: `sudo apt-get install dnsutils`
        *   Untuk CentOS/RHEL: `sudo yum install bind-utils`

## Cara Penggunaan

Pastikan Anda berada di direktori tempat skrip disimpan dan virtual environment (jika digunakan) sudah aktif.

### Penggunaan `ipFinder.py`
```bash
python3 ipFinder.py
```
Skrip akan meminta Anda memasukkan domain target.

### Penggunaan `hashLookup.py`
```bash
python3 hashLookup.py
```
Skrip akan meminta Anda memasukkan URL target untuk dianalisis asetnya.

### Penggunaan `parsing.py`
```bash
python3 parsing.py
```
Skrip akan meminta Anda memasukkan URL target untuk mengekstrak domain eksternal.

## Output

*   **`ipFinder.py`**:
    *   Menampilkan output proses di konsol.
    *   Menyimpan daftar subdomain ke file `{domain}_subs.txt`.
    *   Menyimpan subdomain yang teresolusi beserta IP dan info CDN ke file `{domain}_resolved_subs.txt`.
*   **`hashLookup.py`**:
    *   Menampilkan output proses dan tautan pencarian hash di konsol.
*   **`parsing.py`**:
    *   Menampilkan output proses dan daftar domain eksternal yang ditemukan di konsol.

## Catatan Penting

*   **Etika Penggunaan:** Gunakan alat ini secara bertanggung jawab dan hanya pada sistem yang Anda miliki izin untuk diuji. Jangan gunakan untuk aktivitas ilegal atau merugikan.
*   **Ketergantungan Alat:** Pastikan semua alat eksternal (`subfinder`, `httpx`, `dig`) terinstal dengan benar dan dapat diakses melalui PATH sistem Anda.
*   **Konektivitas Internet:** Skrip ini memerlukan koneksi internet untuk mengambil data dan berkomunikasi dengan layanan eksternal.
*   **Batasan API:** Beberapa layanan yang diakses (misalnya, Wayback Machine) mungkin memiliki batasan laju permintaan (rate limiting) untuk pengguna anonim.
