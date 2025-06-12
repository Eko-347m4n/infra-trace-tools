from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urlparse, urlunparse

def prepare_url_for_requests(url_input: str) -> str:
    # Prepares a URL by adding a scheme if missing.
    url_input = url_input.strip()
    if not url_input:
        return ""
    if not re.match(r"^[a-zA-Z]+://", url_input):
        print(f"[*] Skema tidak ditemukan untuk '{url_input}', "
              "menambahkan 'http://'.")
        url_input = "http://" + url_input
    return url_input

def extract_external_domains(target_url: str):
    print(f"\n[*] Memulai ekstraksi domain eksternal dari: {target_url}")
    try:
        print(f"[*] Mencoba mengambil konten dari: {target_url}")
        response = requests.get(target_url, timeout=10,
                                 headers={'User-Agent': 'Mozilla/5.0'})
        # Akan raise HTTPError untuk status 4xx/5xx
        response.raise_for_status()
        html = response.text
        print(f"[+] Konten berhasil diambil dari {target_url} "
              f"(Status: {response.status_code})")
    except requests.exceptions.HTTPError as e:
        print(f"[!] Gagal mengambil {target_url}: "
              f"Kesalahan HTTP {e.response.status_code}")
        return {
            "error": (
                f"Gagal mengambil {target_url}: Kesalahan HTTP "
                f"{e.response.status_code} - {e.response.reason}"
            )
        }
    except Exception as e:
        print(f"[!] Gagal mengambil {target_url}: {e}")
        return {"error": f"Gagal mengambil {target_url}: {e}"}

    print("[*] Mem-parsing konten HTML...")
    soup = BeautifulSoup(html, "html.parser")
    found_urls = set()

    print("[*] Mencari URL di tag: iframe, script, img, link...")
    for tag in soup.find_all(["iframe", "script", "img", "link"]):
        src = tag.get("src") or tag.get("href")
        if src and (src.startswith("http") or src.startswith("//")):
            found_urls.add(src)

    print("[*] Mencari URL redirect di tag meta refresh...")
    for meta in soup.find_all("meta", attrs={"http-equiv": re.compile("^refresh$", re.I)}):
        content = meta.get("content", "")
        match = re.search(r'url=(.+)', content, re.IGNORECASE)
        if match:
            found_urls.add(match.group(1).strip())
    
    if not found_urls:
        print("[-] Tidak ada URL potensial yang ditemukan di dalam tag HTML.")
    else:
        print(f"[+] Ditemukan {len(found_urls)} URL potensial "
              "dari tag.")

    print("[*] Mengekstrak dan memfilter domain unik "
          "dari URL yang ditemukan...")
    external_domains = set()
    for full_url in found_urls:
        match = re.match(r"(?:https?:)?//([^/]+)", full_url)
        if match:
            domain_with_port = match.group(1)
            domain_only = domain_with_port.split(':')[0]  # Hapus port jika ada
            external_domains.add(domain_only)
    parsed_url = urlparse(target_url)
    # Construct the base URL without path, query, fragment
    structured_url = urlunparse((
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        '', '', ''
    ))
    print(f"[+] Ekstraksi domain selesai untuk {structured_url}.")

    return {
        "source_url": structured_url,
        "external_domains": sorted(external_domains),
        "total_found": len(external_domains)
    }

if __name__ == "__main__":
    raw_url_input = input(
        "Masukkan URL untuk dianalisis (contoh: http://example.com): "
    )
    target_url = prepare_url_for_requests(raw_url_input)

    if not target_url:
        print("[!] URL input tidak valid atau kosong. Keluar.")
    else:
        result = extract_external_domains(target_url)

        if "error" in result:
            print(f"\n[!] Proses ekstraksi gagal: {result['error']}")
        else:
            print(f"\n[✓] Analisis Selesai untuk: {result['source_url']}")
            total_found = result['total_found']
            external_domains = result['external_domains']

            if total_found > 0:
                print(f"[+] Ditemukan {total_found} domain eksternal unik:")
                for domain in external_domains:
                    print(f"  - {domain}")
            else:
                print("[-] Tidak ada domain eksternal yang ditemukan.")
