import requests
import hashlib
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Fungsi prepare_url_for_requests dapat diimpor dari parsing.py jika berada dalam satu paket
# atau disalin/disederhanakan di sini. Untuk kemudahan, versi sederhana disertakan.
def prepare_url_for_requests(url_input: str) -> str:
    url_input = url_input.strip()
    if not url_input:
        return ""
    if not re.match(r"^[a-zA-Z]+://", url_input):
        print(f"[*] Skema tidak ditemukan untuk '{url_input}', menambahkan 'http://'.")
        url_input = "http://" + url_input
    return url_input

def generate_lookup_links(asset_hashes):
    lookup_results = []

    for asset in asset_hashes:
        sha1 = asset.get("sha1")
        md5 = asset.get("md5")
        asset_url = asset.get("asset_url")
        
        current_links = {} 
        
        if sha1: 
            current_links["Google (SHA1)"] = f'https://www.google.com/search?q=SHA1%3A{sha1}'
            current_links["Censys (SHA1)"] = f'https://search.censys.io/certificates?q={sha1}'
            current_links["Shodan (raw file)"] = f'https://www.shodan.io/search?query=hash%3A{sha1}'
        
        if md5: 
            current_links["Google (MD5)"] = f'https://www.google.com/search?q=MD5%3A{md5}'
            
        result = {
            "asset_url": asset_url,
            "sha1": sha1,
            "md5": md5,
            "lookup_links": current_links
        }
        lookup_results.append(result)
    
    return lookup_results

def fetch_and_hash_asset(asset_url: str, session: requests.Session):
    """Mengambil konten dari URL aset dan mengembalikan hash SHA1 dan MD5."""
    try:
        print(f"    [*] Mencoba mengambil aset: {asset_url}")
        # Timeout bisa disesuaikan
        response = session.get(asset_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0 (compatible; PythonAssetHasher/1.0)'})
        response.raise_for_status() # Akan raise HTTPError untuk status 4xx/5xx
        content = response.content # Konten biner untuk hashing
        
        sha1_hash = hashlib.sha1(content).hexdigest()
        md5_hash = hashlib.md5(content).hexdigest()
        print(f"    [+] Berhasil di-hash: {asset_url} (SHA1: {sha1_hash[:8]}..., MD5: {md5_hash[:8]}...)")
        return sha1_hash, md5_hash
    except requests.exceptions.HTTPError as e:
        print(f"    [!] Gagal mengambil aset {asset_url}: Kesalahan HTTP {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"    [!] Gagal mengambil aset {asset_url}: {e}")
    except Exception as e:
        print(f"    [!] Kesalahan tak terduga saat memproses aset {asset_url}: {e}")
    return None, None

def extract_assets_from_url(target_url: str, session: requests.Session):
    """
    Mengekstrak URL aset (gambar, skrip, stylesheet) dari URL target,
    mengambilnya, dan menghitung hashnya.
    """
    print(f"\n[*] Memulai ekstraksi aset dari: {target_url}")
    asset_details_list = []
    
    try:
        print(f"[*] Mencoba mengambil konten utama dari: {target_url}")
        response = session.get(target_url, timeout=20, headers={'User-Agent': 'Mozilla/5.0 (compatible; PythonAssetHasher/1.0)'})
        response.raise_for_status()
        html_content = response.text
        print(f"[+] Konten utama berhasil diambil dari {target_url} (Status: {response.status_code})")
    except requests.exceptions.HTTPError as e:
        print(f"[!] Gagal mengambil URL utama {target_url}: Kesalahan HTTP {e.response.status_code}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[!] Gagal mengambil URL utama {target_url}: {e}")
        return []
    except Exception as e:
        print(f"[!] Kesalahan tak terduga saat mengambil URL utama {target_url}: {e}")
        return []

    print("[*] Mem-parsing konten HTML untuk mencari aset...")
    soup = BeautifulSoup(html_content, "html.parser")
    found_asset_urls = set()

    asset_tags_attrs = {
        "img": "src",
        "script": "src",
        "link": "href",      # Biasanya untuk CSS, bisa juga ikon
        "iframe": "src",
        "source": "src",     # Untuk tag <audio> dan <video>
        "object": "data",
        "embed": "src",
    }

    for tag_name, attr_name in asset_tags_attrs.items():
        for tag in soup.find_all(tag_name):
            asset_src = tag.get(attr_name)
            if asset_src:
                absolute_asset_url = urljoin(target_url, asset_src.strip())
                if absolute_asset_url.startswith(("http://", "https://")):
                    found_asset_urls.add(absolute_asset_url)
    
    if not found_asset_urls:
        print("[-] Tidak ada URL aset potensial yang ditemukan di dalam tag HTML.")
        return []
    
    print(f"[+] Ditemukan {len(found_asset_urls)} URL aset unik potensial. Memproses masing-masing...")

    for asset_url in sorted(list(found_asset_urls)): # Urutkan untuk output yang konsisten
        sha1, md5 = fetch_and_hash_asset(asset_url, session)
        # Hanya tambahkan aset ke daftar jika kedua hash berhasil dihitung (artinya aset valid dan dapat diakses)
        if sha1 is not None and md5 is not None:
            asset_details_list.append({
                "asset_url": asset_url,
                "sha1": sha1,
                "md5": md5
            })
        # Jika fetch_and_hash_asset gagal, ia sudah mencetak pesan kesalahan.
        # Kita tidak menambahkan aset ini ke daftar untuk diproses lebih lanjut.
    return asset_details_list

def main():
    print("[*] Selamat datang di skrip Pencarian Hash Aset Otomatis.")
    raw_url_input = input("Masukkan URL target untuk dianalisis (contoh: http://example.com): ").strip()
    
    target_url = prepare_url_for_requests(raw_url_input)

    if not target_url:
        print("[!] URL input tidak valid atau kosong. Keluar.")
        return

    # Gunakan session untuk efisiensi koneksi dan potensi penggunaan kembali cookie/header
    with requests.Session() as session:
        asset_hashes_input = extract_assets_from_url(target_url, session)

    if not asset_hashes_input:
        print("\n[!] Tidak ada aset yang berhasil diekstrak atau di-hash dari URL tersebut. Keluar.")
        return

    print(f"\n[*] Menghasilkan link pencarian untuk {len(asset_hashes_input)} aset yang ditemukan/diproses...")
    results = generate_lookup_links(asset_hashes_input)

    print(f"\n[✓] Analisis Selesai. Hasil link pencarian:")
    for idx, item in enumerate(results):
        print(f"\n--- Hasil untuk Aset #{idx + 1} ---")
        print(f"  URL Aset: {item.get('asset_url', 'Tidak Tersedia')}")
        
        provided_sha1 = item.get('sha1')
        provided_md5 = item.get('md5')

        if provided_sha1:
            print(f"  SHA1: {provided_sha1}")
        else:
            print(f"  SHA1: Tidak dapat dihitung/ditemukan")
            
        if provided_md5:
            print(f"  MD5: {provided_md5}")
        else:
            print(f"  MD5: Tidak dapat dihitung/ditemukan")

        if item["lookup_links"]: # Cek apakah dictionary lookup_links tidak kosong
            print("  Link Pencarian:")
            for name, link in item["lookup_links"].items():
                print(f"    - {name}: {link}")
        else:
            print("  Link Pencarian: Tidak ada hash yang valid untuk menghasilkan link.")

if __name__ == "__main__":
    main()