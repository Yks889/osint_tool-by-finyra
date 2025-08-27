#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINT Social Media Finder - Finyra Software Design Studio
Safe + Fallback Search Version
"""

import os, sys, json, time, random, urllib.parse, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import signal
import csv
import instaloader
from instaloader import Instaloader, Profile
import re 

# ================= CONFIG =================
APP_TITLE = "OSINT Social Media Finder"
APP_OWNER = "Finyra Software Design Studio"
REQ_TIMEOUT = 15
MAX_RETRIES = 3
BACKOFF_BASE = 2
SCRAPE_DELAY = (1.0, 2.5)  # lebih aman
SEARCH_FALLBACK = True  # fallback via Google/DuckDuckGo

SOCIAL_DOMAINS = {
    # Sosial media umum
    "facebook.com": "Facebook",
    "twitter.com": "Twitter",
    "instagram.com": "Instagram",
    "linkedin.com": "LinkedIn",
    "tiktok.com": "TikTok",
    "snapchat.com": "Snapchat",
    "pinterest.com": "Pinterest",
    "reddit.com": "Reddit",
    "tumblr.com": "Tumblr",
    "vk.com": "VK",
    "weibo.com": "Weibo",
    "mastodon.social": "Mastodon",
    "telegram.me": "Telegram",
    "t.me": "Telegram",
    "discord.com": "Discord",

    # Platform konten creator
    "youtube.com": "YouTube",
    "vimeo.com": "Vimeo",
    "twitch.tv": "Twitch",
    "soundcloud.com": "SoundCloud",
    "bandcamp.com": "Bandcamp",
    "mixcloud.com": "Mixcloud",
    "patreon.com": "Patreon",
    "ko-fi.com": "Ko-fi",

    # Platform profesional & knowledge
    "stackoverflow.com": "StackOverflow",
    "medium.com": "Medium",
    "quora.com": "Quora",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "bitbucket.org": "Bitbucket",
    "researchgate.net": "ResearchGate",
    "academia.edu": "Academia",

    # Platform review & interest
    "goodreads.com": "Goodreads",
    "letterboxd.com": "Letterboxd",
    "behance.net": "Behance",
    "dribbble.com": "Dribbble",
    "deviantart.com": "DeviantArt",
    "flickr.com": "Flickr",

    # Marketplace / e-commerce social
    "etsy.com": "Etsy",
    "ebay.com": "eBay",
    "pinterest.com": "Pinterest",
    "tiktokshop.com": "TikTok Shop",

    # Misc / forums / communities
    "4chan.org": "4chan",
    "8kun.top": "8kun",
    "forums.whirlpool.net.au": "Whirlpool",
    "vbulletin.com": "vBulletin",
    "discourse.org": "Discourse",
}

UA_POOL = [
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
]

_partial_findings: List = []
_shutdown_requested = False

# ================= DATACLASS =================
@dataclass
class SocialProfile:
    platform: str
    url: str
    username: str
    full_name: str
    bio: str
    location: str
    emails: list
    phones: list
    followers: int
    following: int
    posts: int
    profile_pic_url: Optional[str]


# ================= HELPERS =================
def rand_ua():
    return random.choice(UA_POOL)

def log_info(msg: str):
    print(f"[i] {msg}")

def log_warn(msg: str):
    print(f"[!] {msg}")

class RequestBlocked(Exception): pass

def request_get(url: str) -> Optional[requests.Response]:
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = {"User-Agent": rand_ua(), "Accept-Language": "en-US,en;q=0.9"}
            log_info(f"Requesting {url} (attempt {attempt})")
            resp = requests.get(url, headers=headers, timeout=REQ_TIMEOUT)
            if resp.status_code in (401,403):
                raise RequestBlocked(f"HTTP {resp.status_code}")
            if resp.status_code == 429:
                raise Exception("HTTP 429 Too Many Requests")
            if any(x in resp.text.lower() for x in ["captcha", "unusual traffic"]):
                raise RequestBlocked("Captcha / unusual traffic detected")
            return resp
        except RequestBlocked as rb:
            log_warn(f"Request blocked: {rb}")
            last_exc = rb
            break
        except Exception as e:
            last_exc = e
            backoff = BACKOFF_BASE ** (attempt - 1) + random.uniform(0, 1.0)
            log_warn(f"Request error: {e} — retrying in {backoff:.1f}s")
            time.sleep(backoff)
    if isinstance(last_exc, RequestBlocked) and SEARCH_FALLBACK:
        log_info(f"Falling back search for {url}")
        return search_fallback(url)
    return None

def search_fallback(url: str) -> Optional[requests.Response]:
    """Fallback search via Google / DuckDuckGo"""
    username_or_email = url.rstrip("/").split("/")[-1]
    host = urllib.parse.urlparse(url).netloc
    query = f"site:{host} {username_or_email}"
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    try:
        headers = {"User-Agent": rand_ua()}
        resp = requests.get(search_url, headers=headers, timeout=REQ_TIMEOUT)
        return resp
    except Exception as e:
        log_warn(f"Fallback search failed: {e}")
        return None

def extract_contacts(text: str):
    EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+")
    PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s\(\)]{6,}\d)")
    emails = sorted(set(re.findall(EMAIL_RE, text)))
    phones = sorted(set([re.sub(r"\s+", " ", p.strip()) for p in re.findall(PHONE_RE, text)]))
    phones = [p for p in phones if len(re.sub(r"\D","",p))>=8]
    return emails, phones

def guess_platform(url: str):
    host = urllib.parse.urlparse(url).netloc.lower()
    for dom, name in SOCIAL_DOMAINS.items():
        if dom in host: return name
    return "Unknown"

def scrape_profile(url: str) -> Optional[SocialProfile]:
    try:
        resp = request_get(url)
        if not resp: return None
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        emails, phones = extract_contacts(text)
        username = url.rstrip("/").split("/")[-1]
        full_name = soup.title.get_text(strip=True) if soup.title else None
        p_tags = soup.find_all("p")
        bio = " ".join([p.get_text(" ",strip=True) for p in p_tags[:2]]) if p_tags else None
        loc_tags = soup.find_all(["span","div"], string=re.compile(r"\b(location|city|kota|alamat)\b", re.I))
        location = loc_tags[0].get_text(strip=True) if loc_tags else None
        profile = SocialProfile(
            platform=guess_platform(url),
            url=url,
            username=username,
            full_name=full_name,
            bio=bio,
            location=location,
            emails=emails or None,
            phones=phones or None
        )
        return profile
    except Exception as e:
        log_warn(f"Gagal scrape {url}: {e}")
        return None

# ================= SAVE =================
def ensure_dir(path: str):
    """Pastikan folder ada, jika tidak buat otomatis"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        
def save_json(findings: List[SocialProfile], filename: str, folder: str = "output"):
    ensure_dir(folder)
    filepath = os.path.join(folder, filename)
    data = [asdict(f) for f in findings]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log_info(f"JSON saved -> {filepath}")

def save_csv(findings: List[SocialProfile], filename: str, folder: str = "output"):
    ensure_dir(folder)
    filepath = os.path.join(folder, filename)
    rows = [asdict(f) for f in findings]
    keys = sorted({k for r in rows for k in r.keys()})
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            for k in ["emails","phones"]:
                if isinstance(r.get(k), list): r[k] = "; ".join(r[k])
            w.writerow(r)
    log_info(f"CSV saved -> {filepath}")

def sanitize(s: str) -> str: return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def save_html(findings: List[SocialProfile], filename: str, folder: str = "output"):
    ensure_dir(folder)
    filepath = os.path.join(folder, filename)
    html = [f"<html><head><meta charset='utf-8'><title>OSINT Report</title></head><body>"]
    html.append(f"<h1>OSINT Social Media Finder</h1><small>{APP_OWNER}</small>")
    for f in findings:
        html.append(f"<div><b>{sanitize(f.platform)}</b> | <a href='{sanitize(f.url)}'>{sanitize(f.url)}</a><br>")
        html.append(f"Username: {sanitize(f.username)} | Name: {sanitize(f.full_name)}<br>")
        html.append(f"Bio: {sanitize(f.bio)}<br>Location: {sanitize(f.location)}<br>")
        html.append(f"Emails: {sanitize(', '.join(f.emails) if f.emails else '')} | Phones: {sanitize(', '.join(f.phones) if f.phones else '')}")
        html.append("</div><hr>")
    html.append(f"<footer>Generated by {APP_TITLE} — {APP_OWNER}</footer></body></html>")
    with open(filepath, "w", encoding="utf-8") as f: f.write("\n".join(html))
    log_info(f"HTML report saved -> {filepath}")

def save_results(findings: List[SocialProfile], base: str, out_fmt: str, folder: str = "output"):
    if out_fmt.lower() == "csv":
        save_csv(findings, f"{base}.csv", folder)
    else:
        save_json(findings, f"{base}.json", folder)
    save_html(findings, f"{base}.html", folder)

# ================= SIGNAL =================
def _handle_shutdown(signum,frame):
    global _shutdown_requested
    print("\n[i] Shutdown requested... stopping after current ops.")
    _shutdown_requested = True

signal.signal(signal.SIGINT,_handle_shutdown)
signal.signal(signal.SIGTERM,_handle_shutdown)

# ================= INSTAGRAM MENU =================

def get_contact_hint_from_ig(username: str, instaloader_context):
    """
    Ambil email hint & phone hint dari Instagram forgot password menggunakan session Instaloader.
    """
    try:
        session = instaloader_context._session
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-CSRFToken": session.cookies.get_dict().get("csrftoken", ""),
            "Referer": "https://www.instagram.com/accounts/password/reset/",
        }
        data = {
            "email_or_username": username,
        }
        url = "https://www.instagram.com/accounts/account_recovery_send_ajax/"
        res = session.post(url, headers=headers, data=data)

        if res.status_code == 200:
            j = res.json()
            email_hint = j.get("contact_point")  # contoh: j***@gmail.com
            phone_hint = j.get("obfuscated_phone_number")  # contoh: +62 *** 1234
            return email_hint, phone_hint
        return None, None
    except Exception as e:
        print(f"[!] Gagal ambil contact hint untuk {username}: {e}")
        return None, None


def scrape_instagram_logged(target_username: str, session_file: str, session_user: str) -> Optional[SocialProfile]:
    """
    Scrape Instagram profile menggunakan session file (.session)
    + Ekstrak lokasi, email (bio + hint), dan phone
    """
    try:
        L = Instaloader()
        L.load_session_from_file(username=session_user, filename=session_file)
        profile = Profile.from_username(L.context, target_username)

        # Ambil bio
        bio_text = profile.biography or ""

        # Regex untuk email & phone dari bio
        EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+")
        PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s\(\)]{6,}\d)")

        emails = EMAIL_RE.findall(bio_text)
        phones = PHONE_RE.findall(bio_text)

        # Ambil email_hint & phone_hint via forgot password
        email_hint, phone_hint = get_contact_hint_from_ig(target_username, L.context)

        if email_hint and email_hint not in emails:
            emails.append(email_hint)

        if phone_hint and phone_hint not in phones:
            phones.append(phone_hint)
            
        # Jika keduanya kosong, baru fallback "Tidak tersedia"
        if not emails:
            emails = ["Tidak tersedia"]
        if not phones:
            phones = ["Tidak tersedia"]

        # Coba deteksi lokasi (manual dari bio)
        location = None
        possible_locations = ["Jakarta", "Bandung", "Surabaya", "Indonesia", "ID", "Bali"]
        for loc in possible_locations:
            if loc.lower() in bio_text.lower():
                location = loc
                break

        return SocialProfile(
            platform="Instagram",
            url=f"https://instagram.com/{target_username}",
            username=profile.username,
            full_name=profile.full_name or "Tidak tersedia",
            bio=bio_text or "Tidak tersedia",
            location=location or "Tidak tersedia",
            emails=emails,
            phones=phones,
            followers=profile.followers,
            following=profile.followees,
            posts=profile.mediacount,
            profile_pic_url=getattr(profile, "profile_pic_url", None)
        )

    except Exception as e:
        print(f"[!] Gagal scrape Instagram {target_username}: {e}")
        return None

        
# ================= CLI =================
def banner():
    print(f"\n=============================\n{APP_TITLE}\nBranding: {APP_OWNER}\n=============================\n")

def run_scan(items: list, mode: str = "username", threads: int = 6, realtime: bool = True):
    """
    items: list of emails or usernames
    mode: "email" atau "username"
    """
    global _partial_findings
    findings = []
    links = []

    for item in items:
        if mode == "email":
            links.extend([f"https://{dom}/search?q={urllib.parse.quote(item)}" for dom in SOCIAL_DOMAINS])
        else:  # username
            links.extend([f"https://{dom}/{urllib.parse.quote(item)}" for dom in SOCIAL_DOMAINS])

    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(scrape_profile, url): url for url in links}
        total = len(futures)
        count = 0
        skipped = 0

        for fut in as_completed(futures):
            if _shutdown_requested:
                log_info("Shutdown requested — stopping.")
                break
            try:
                res = fut.result()
                if res:
                    findings.append(res)
                    _partial_findings.append(res)
                    count += 1
                    if realtime:
                        print(f"[{count}/{total}] {res.platform} | {res.username} | {res.url}")
                else:
                    skipped += 1
                    if realtime:
                        print(f"[{count + skipped}/{total}] Skipped (no result)")
            except Exception as e:
                skipped += 1
                if realtime:
                    print(f"[{count + skipped}/{total}] Exception: {e}")
            time.sleep(random.uniform(*SCRAPE_DELAY))

    log_info(f"Scan selesai: {count} ditemukan, {skipped} dilewati/gagal.")
    return findings
    
# ================= MAIN =================
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

def banner():
    os.system('clear' if os.name=="posix" else 'cls')

    ascii_text = r"""
  /$$$$$$   /$$$$$$  /$$$$$$ /$$   /$$ /$$$$$$$$       /$$    /$$   /$$  
 /$$__  $$ /$$__  $$|_  $$_/| $$$ | $$|__  $$__/      | $$   | $$ /$$$$  
| $$  \ $$| $$  \__/  | $$  | $$$$| $$   | $$         | $$   | $$|_  $$  
| $$  | $$|  $$$$$$   | $$  | $$ $$ $$   | $$         |  $$ / $$/  | $$  
| $$  | $$ \____  $$  | $$  | $$  $$$$   | $$          \  $$ $$/   | $$  
| $$  | $$ /$$  \ $$  | $$  | $$\  $$$   | $$           \  $$$/    | $$  
|  $$$$$$/|  $$$$$$/ /$$$$$$| $$ \  $$   | $$            \  $/    /$$$$$$
 \______/  \______/ |______/|__/  \__/   |__/             \_/    |______/
"""

    print(f"{Colors.OKGREEN}{ascii_text}{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}  OSINT Social Media Finder v1 2025{Colors.END}")
    print(f"  Powered by Finyra Software Design Studio")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")



def main():
    out_fmt="json"
    banner()
    while True:
        print(f"{Colors.OKBLUE}[1]{Colors.END} 🔍 Scan Social Media by Email")
        print(f"{Colors.OKBLUE}[2]{Colors.END} 🔎 Scan Social Media by Username")
        print(f"{Colors.OKBLUE}[3]{Colors.END} ⚙️ Change Output Format (JSON/CSV)")
        print(f"{Colors.OKBLUE}[4]{Colors.END} 📸 OSINT Instagram (username only)")
        print(f"{Colors.OKBLUE}[5]{Colors.END} ❌ Exit")
        print("-"*50)
        
        choice=input(f"{Colors.BOLD}[?] Pilih opsi: {Colors.END}").strip()
        
        if choice=="1":
            email=input(f"{Colors.OKCYAN}[+] Masukkan Email: {Colors.END}").strip()
            if not email: continue
            threads=input(f"{Colors.OKCYAN}[+] Jumlah threads [6]: {Colors.END}").strip()
            threads=int(threads) if threads.isdigit() else 6
            findings=run_scan([email],mode="email",threads=threads)
            if findings: 
                save_results(findings,f"results_email_{int(time.time())}",out_fmt)
            else: print(f"{Colors.WARNING}[-] Tidak ada hasil ditemukan.{Colors.END}")
        
        elif choice=="2":
            username=input(f"{Colors.OKCYAN}[+] Masukkan Username: {Colors.END}").strip()
            if not username: continue
            threads=input(f"{Colors.OKCYAN}[+] Jumlah threads [6]: {Colors.END}").strip()
            threads=int(threads) if threads.isdigit() else 6
            findings=run_scan([username],mode="username",threads=threads)
            if findings: 
                save_results(findings,f"results_username_{int(time.time())}",out_fmt)
            else: print(f"{Colors.WARNING}[-] Tidak ada hasil ditemukan.{Colors.END}")
        
        elif choice=="3":
            fmt=input(f"{Colors.OKCYAN}[+] Format (json/csv): {Colors.END}").strip().lower()
            if fmt in ("json","csv"): 
                out_fmt=fmt
                print(f"{Colors.OKGREEN}[i] Output format diubah menjadi {out_fmt.upper()}{Colors.END}")
            else:
                print(f"{Colors.WARNING}[!] Format tidak valid{Colors.END}")
        
        elif choice=="4":
            session_user = input(f"{Colors.OKCYAN}[+] Masukkan username IG session: {Colors.END}").strip()
            session_file = input(f"{Colors.OKCYAN}[+] Masukkan path session file (/home/cby032/.config/instaloader/session-(akun_login)): {Colors.END}").strip()
            target_username = input(f"{Colors.OKCYAN}[+] Masukkan Instagram Username target: {Colors.END}").strip() 
            
            profile = scrape_instagram_logged(target_username, session_file, session_user)
            if profile:
                save_results([profile], f"instagram_{target_username}_{int(time.time())}", out_fmt)
                print(f"{Colors.OKGREEN}[i] Instagram profile {target_username} berhasil disimpan.{Colors.END}")
            else:
                print(f"{Colors.FAIL}[-] Gagal mendapatkan data Instagram.{Colors.END}")
                
        elif choice=="5":
            if _partial_findings: save_results(_partial_findings,f"partial_exit_{int(time.time())}",out_fmt)
            print(f"{Colors.OKGREEN}[i] Keluar...{Colors.END}"); break
        
        else:
            print(f"{Colors.WARNING}[!] Pilihan tidak valid!{Colors.END}")

if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt:
        if _partial_findings: save_results(_partial_findings,f"partial_kbint_{int(time.time())}","json")
        print(f"\n{Colors.WARNING}[i] Dihentikan user.{Colors.END}")
        sys.exit(0)
