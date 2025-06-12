import os
import subprocess
import requests
import json
from urllib.parse import urlparse
import re # For domain sanitization regex

def sanitize_domain(input_str: str) -> str:
    input_str = input_str.strip()
    if not input_str:
        return ""

    # Add a scheme if missing, to help urlparse identify the netloc correctly.
    if not re.match(r"^[a-zA-Z]+://", input_str):
        input_str = "http://" + input_str
    
    parsed_url = urlparse(input_str)
    domain = parsed_url.netloc
    
    # Remove port if present, e.g., example.com:8080
    if domain:
        domain = domain.split(':')[0]
    return domain

def run_command(cmd_list: list[str], check_return_code: bool = True) -> str | None:
    try:
        process = subprocess.run(cmd_list, capture_output=True, text=True, check=False)
        if check_return_code and process.returncode != 0:
            print(f"Error running command: {' '.join(cmd_list)}")
            print(f"Return code: {process.returncode}")
            if process.stdout.strip():
                print(f"Stdout: {process.stdout.strip()}")
            if process.stderr.strip():
                print(f"Stderr: {process.stderr.strip()}")
            return None
        return process.stdout.strip()
    except FileNotFoundError:
        print(f"Error: Command '{cmd_list[0]}' not found. Please ensure it's installed and in your PATH.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while running {' '.join(cmd_list)}: {e}")
        return None

def main():
    raw_domain_input = input("Masukkan domain target (contoh: example.com): ").strip()
    domain = sanitize_domain(raw_domain_input)

    if not domain:
        print("Input domain tidak valid. Keluar.")
        return

    print(f"\n[*] Domain target yang disanitasi: {domain}")

    subdomains_file = f"{domain}_subs.txt"
    resolved_subdomains_file = f"{domain}_resolved_subs.txt"

    print("\n[*] Enumerasi subdomain dengan subfinder...")
    subfinder_cmd_list = ["subfinder", "-d", domain, "-silent", "-o", subdomains_file]
    subfinder_result = run_command(subfinder_cmd_list)

    if subfinder_result is None:
        print(f"Perintah subfinder gagal. File '{subdomains_file}' mungkin tidak dibuat atau kosong.")
    elif not os.path.exists(subdomains_file) or os.path.getsize(subdomains_file) == 0:
        print(f"Subfinder berjalan, tetapi tidak menghasilkan subdomain atau file output '{subdomains_file}' kosong/tidak ditemukan.")
    else:
        print(f"Subdomain disimpan ke {subdomains_file}")

    # Lanjutkan ke httpx hanya jika file subdomain ada dan tidak kosong
    if os.path.exists(subdomains_file) and os.path.getsize(subdomains_file) > 0:
        print("\n[*] Resolusi subdomain dan cek proteksi CDN dengan httpx...")
        httpx_cmd_list = ["httpx", "-l", subdomains_file, "-ip", "-cdn", "-silent", "-o", resolved_subdomains_file]
        httpx_result = run_command(httpx_cmd_list)
        if httpx_result is None:
            print(f"Perintah httpx gagal. File '{resolved_subdomains_file}' mungkin tidak dibuat atau kosong.")
        elif not os.path.exists(resolved_subdomains_file) or os.path.getsize(resolved_subdomains_file) == 0:
            print(f"Httpx berjalan, tetapi file output '{resolved_subdomains_file}' kosong atau tidak ditemukan.")
        else:
             print(f"Subdomain yang diresolusi disimpan ke {resolved_subdomains_file}")
    else:
        print(f"\n[*] Melewati httpx karena '{subdomains_file}' tidak ada atau kosong.")

    print(f"\n[*] Hasil subdomain dan IP ({resolved_subdomains_file}):")
    if os.path.exists(resolved_subdomains_file) and os.path.getsize(resolved_subdomains_file) > 0:
        try:
            with open(resolved_subdomains_file, "r") as f:
                print(f.read())
        except Exception as e:
            print(f"Gagal membaca file '{resolved_subdomains_file}': {e}")
    else:
        print(f"File '{resolved_subdomains_file}' tidak ditemukan atau kosong. Pastikan perintah httpx berjalan dengan benar dan menghasilkan output.")

    print("\n[*] Mencari MX record...")
    dig_mx_cmd_list = ["dig", "mx", domain, "+short"]
    mx_output = run_command(dig_mx_cmd_list)

    if mx_output:
        print(mx_output)
        print("\n[*] Resolving MX record ke IP...")
        for line in mx_output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:  # MX records typically priority host
                mx_host = parts[-1].strip('.') # The last part is the host
                
                # Resolve A records for the MX host
                dig_a_cmd_list = ["dig", "A", mx_host, "+short"]
                ip_output = run_command(dig_a_cmd_list)
                if ip_output:
                    ips = [ip.strip() for ip in ip_output.splitlines() if ip.strip()]
                    if ips:
                        print(f"{mx_host}: {', '.join(ips)}")
                    else:
                        print(f"Tidak ada A record ditemukan untuk MX host: {mx_host}")
                else:
                    print(f"Gagal melakukan resolve A record untuk MX host: {mx_host} (perintah dig gagal)")
            else:
                print(f"Tidak dapat mem-parsing baris MX record: {line}")
    else:
        print(f"Tidak ada MX record ditemukan untuk {domain} atau perintah dig gagal.")

    print("\n[*] Cek Wayback Machine untuk /.env leak...")
    wayback_url = f"http://web.archive.org/cdx/search/cdx?url={domain}/.env&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&showDupeCount=true&collapse=digest"
    try:
        res = requests.get(wayback_url, timeout=15)
        res.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        results = res.json()
        if results and len(results) > 1:  # Header row + data rows
            header = results[0]
            print(f"Hasil Wayback Machine untuk {domain}/.env (Fields: {', '.join(header)}):")
            for entry_list in results[1:]:
                entry_dict = dict(zip(header, entry_list))
                print(f"  - {entry_dict}")
        elif results and len(results) == 1: # Only header returned
             print(f"Tidak ada entri Wayback Machine yang ditemukan untuk {domain}/.env (hanya header yang dikembalikan).")
        else:
            print(f"Tidak ada entri Wayback Machine yang ditemukan untuk {domain}/.env.")
    except requests.exceptions.HTTPError as e:
        print(f"Permintaan Wayback Machine gagal untuk {domain}/.env. Status: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses Wayback Machine untuk {domain}/.env: {e}")
    except json.JSONDecodeError:
        print(f"Error saat men-decode respons JSON dari Wayback Machine untuk {domain}/.env.")
        if 'res' in locals() and hasattr(res, 'text'):
             print(f"Response text (awal): {res.text[:200]}...")


    print("\n[*] Silakan buka URL ini secara manual untuk investigasi lebih lanjut:")
    print(f"  - DNS History: https://securitytrails.com/domain/{domain}/history")
    print(f"  - Certificate Transparency: https://crt.sh/?q=%25.{domain}")

    # Determine which files were successfully created and are non-empty for the final message
    created_file_descriptions = []
    if os.path.exists(subdomains_file) and os.path.getsize(subdomains_file) > 0:
        created_file_descriptions.append(f"'{subdomains_file}' (subdomains)")
    
    if os.path.exists(resolved_subdomains_file) and os.path.getsize(resolved_subdomains_file) > 0:
        created_file_descriptions.append(f"'{resolved_subdomains_file}' (resolved IPs)")

    if created_file_descriptions:
        files_summary = ""
        if len(created_file_descriptions) == 1:
            files_summary = created_file_descriptions[0]
        elif len(created_file_descriptions) == 2:
            files_summary = f"{created_file_descriptions[0]} dan {created_file_descriptions[1]}"
        print(f"\n[✓] Selesai. Analisis hasil di {files_summary}.")
    else:
        print(f"\n[!] Selesai, tetapi tidak ada file output yang berhasil dibuat atau berisi data.")
        print(f"  Harap periksa log di atas untuk detail mengapa '{subdomains_file}' atau '{resolved_subdomains_file}' mungkin tidak dibuat atau ditemukan kosong.")

if __name__ == "__main__":
    main()
