# -- coding: utf-8 --

import requests
import os
import re
import base64
import threading
import concurrent.futures
import socket
import time
import random
import statistics
import sys
import urllib.parse
from typing import List, Dict, Tuple, Optional, Set, Union

# --- Global Constants & Variables ---

PRINT_LOCK = threading.Lock()

# مسیر دایرکتوری خروجی
OUTPUT_DIR = "data"

# لیست URLهای سابسکریپشن
CONFIG_URLS: List[str] = [
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/subscriptions/xray/base64/mix",
    "https://raw.githubusercontent.com/Argh73/VpnConfigCollector/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt",
    "https://raw.githubusercontent.com/jagger235711/V2rayCollector/refs/heads/main/results/vless.txt",
    "https://raw.githubusercontent.com/3yed-61/configs-collector/refs/heads/main/classified_output/vless.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/vless",
    "https://raw.githubusercontent.com/ircfspace/XraySubRefiner/refs/heads/main/export/soliSpirit/normal",
    "https://raw.githubusercontent.com/ircfspace/XraySubRefiner/refs/heads/main/export/psgV6/normal",
    "https://raw.githubusercontent.com/ircfspace/XraySubRefiner/refs/heads/main/export/psgMix/normal",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/refs/heads/main/sub/Mix/mix.txt",
    "https://raw.githubusercontent.com/T3stAcc/V2Ray/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/refs/heads/main/splitted-by-protocol/vless.txt",
    "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/refs/heads/master/result/nodes",
    "https://raw.githubusercontent.com/Flikify/Free-Node/refs/heads/main/v2ray.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/refs/heads/main/sub/vless.txt",
    "https://raw.githubusercontent.com/iboxz/free-v2ray-collector/refs/heads/main/main/vless",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt",
    "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt",
    "https://raw.githubusercontent.com/Pasimand/v2ray-config-agg/refs/heads/main/config.txt",
    "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/vless.html",
    "https://raw.githubusercontent.com/xyfqzy/free-nodes/refs/heads/main/nodes/vless.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/14.txt",
    "https://raw.githubusercontent.com/Awmiroosen/awmirx-v2ray/refs/heads/main/blob/main/v2-sub.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt",
    "https://raw.githubusercontent.com/RaitonRed/ConfigsHub/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://media.githubusercontent.com/media/gfpcom/free-proxy-list/refs/heads/main/list/vless.txt",
    "https://raw.githubusercontent.com/Matin-RK0/ConfigCollector/refs/heads/main/subscription.txt"
]

OUTPUT_FILENAME: str = os.getenv("REALITY_OUTPUT_FILENAME", "khanevadeh") + "_base64.txt"

# تنظیمات زمان‌بندی و تست
REQUEST_TIMEOUT: int = 15
TCP_CONNECT_TIMEOUT: int = 4  # کمی کاهش دادیم برای سرعت بیشتر
NUM_TCP_TESTS: int = 5        # کاهش تعداد تست‌ها برای جلوگیری از طولانی شدن بیش از حد
MIN_SUCCESSFUL_TESTS_RATIO: float = 0.6

QUICK_CHECK_TIMEOUT: int = 2

MAX_CONFIGS_TO_TEST: int = 90000 # محدودیت معقول‌تر
FINAL_MAX_OUTPUT_CONFIGS: int = 2000

# شناسه برای جلوگیری از تکرار
SEEN_IDENTIFIERS: Set[Tuple[str, int, str]] = set()

# لیست User-Agent ها برای جلوگیری از بلاک شدن
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

# --- توابع کمکی (Helper Functions) ---

def safe_print(message: str) -> None:
    with threading.Lock():
        print(message)

def print_progress(iteration: int, total: int, prefix: str = '', suffix: str = '', bar_length: int = 40) -> None:
    """نمایش نوار پیشرفت"""
    with PRINT_LOCK:
        if total == 0: total = 1
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(bar_length * iteration // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
        sys.stdout.flush()
        if iteration >= total:
            sys.stdout.write('\n')

def get_random_header() -> Dict[str, str]:
    return {'User-Agent': random.choice(USER_AGENTS)}

def parse_vless_config(config_str: str) -> Optional[Dict[str, Union[str, int]]]:
    """
    پارس کردن لینک VLESS با استفاده از کتابخانه استاندارد urllib
    جایگزین Regex پیچیده برای پایداری بیشتر.
    """
    if not config_str.startswith("vless://"):
        return None

    try:
        # حذف vless:// برای پارس راحت‌تر (اگر از urlparse استاندارد استفاده کنیم ممکن است نیاز به اصلاح باشد)
        # اما urlparse پروتکل‌های ناشناخته را هم هندل می‌کند
        parsed = urllib.parse.urlparse(config_str)
        
        if not parsed.netloc:
            return None

        # ساختار معمول: uuid@server:port
        user_info_server = parsed.netloc
        if '@' not in user_info_server:
            return None
            
        uuid, server_port = user_info_server.split('@', 1)
        
        if ':' in server_port:
            # هندل کردن IPv6 (داخل براکت) یا IPv4
            server_host = parsed.hostname
            server_port_num = parsed.port
        else:
            return None # پورت موجود نیست

        if not server_host or not server_port_num:
            return None

        # پارس کردن پارامترها
        query_params = urllib.parse.parse_qs(parsed.query)
        
        # چک کردن اینکه Reality است
        security = query_params.get('security', [''])[0]
        if security != 'reality':
            return None
        
        pbk = query_params.get('pbk', [''])[0]
        if not pbk:
            return None

        fp = query_params.get('fp', [''])[0]
        sni = query_params.get('sni', [''])[0]
        sid = query_params.get('sid', [''])[0]
        spx = query_params.get('spx', [''])[0]
        
        # نام کانفیگ (fragment)
        name = urllib.parse.unquote(parsed.fragment) if parsed.fragment else ""

        return {
            "uuid": uuid,
            "server": server_host,
            "port": int(server_port_num),
            "pbk": pbk,
            "fp": fp,
            "sni": sni,
            "sid": sid,
            "spx": spx,
            "name": name,
            "original_config": config_str
        }
    except Exception:
        return None

def is_base64_content(s: str) -> bool:
    """تشخیص اینکه آیا محتوا Base64 است یا خیر"""
    if not isinstance(s, str) or not s:
        return False
    # چک کردن کاراکترهای مجاز
    if not re.match(r'^[A-Za-z0-9+/=\s]+$', s):
        return False
    if len(s.strip()) % 4 != 0: # طول باید مضرب 4 باشد
        return False
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False

# --- توابع اصلی (Fetch & Process) ---

def fetch_subscription_content(url: str) -> Optional[str]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=get_random_header())
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException:
        # خطاها را بی‌صدا رد می‌کنیم تا لاگ شلوغ نشود
        return None

def process_subscription_content(content: str, source_url: str) -> List[Dict[str, Union[str, int]]]:
    if not content:
        return []
    
    # تلاش برای دیکد کردن Base64
    decoded_content = content
    if is_base64_content(content):
        try:
            decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
        except Exception as e:
            safe_print(f"⚠️ خطای دیکد Base64 برای {source_url}: {e}")
            return []
            
    valid_configs = []
    for line in decoded_content.splitlines():
        line = line.strip()
        if not line or not line.startswith("vless://"):
            continue
            
        if "security=reality" in line:
            parsed_data = parse_vless_config(line)
            if parsed_data:
                identifier = (parsed_data["server"], parsed_data["port"], parsed_data["uuid"])
                if identifier not in SEEN_IDENTIFIERS:
                    SEEN_IDENTIFIERS.add(identifier)
                    valid_configs.append(parsed_data)
                    
    return valid_configs

def gather_configurations(links: List[str]) -> List[Dict]:
    safe_print("🚀 مرحله ۱/۳: در حال دریافت و پردازش کانفیگ‌ها...")
    all_configs = []
    total_links = len(links)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_subscription_content, url): url for url in links}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            url = futures[future]
            content = future.result()
            if content:
                configs = process_subscription_content(content, url)
                all_configs.extend(configs)
            print_progress(i + 1, total_links, prefix='دریافت:', suffix='تکمیل')
            
    safe_print(f"\n✨ مجموع کانفیگ‌های یکتا: {len(all_configs)}")
    return all_configs

# --- توابع تست (Testing) ---

def test_tcp_latency(host: str, port: int, timeout: int) -> Optional[float]:
    try:
        start_time = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout):
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000
    except (socket.timeout, ConnectionRefusedError, OSError):
        return None

def quick_tcp_check(config: Dict) -> Optional[Dict]:
    """یک تست سریع برای فیلتر اولیه"""
    if test_tcp_latency(config['server'], config['port'], QUICK_CHECK_TIMEOUT):
        return config
    return None

def measure_quality_metrics(config: Dict) -> Optional[Dict]:
    host = config['server']
    port = config['port']
    latencies = []
    
    for _ in range(NUM_TCP_TESTS):
        lat = test_tcp_latency(host, port, TCP_CONNECT_TIMEOUT)
        if lat:
            latencies.append(lat)
        # وقفه کوتاه تصادفی بین پینگ‌ها
        time.sleep(0.1) 
        
    if not latencies or len(latencies) < (NUM_TCP_TESTS * MIN_SUCCESSFUL_TESTS_RATIO):
        return None
        
    avg_latency = statistics.mean(latencies)
    jitter = 0.0
    if len(latencies) > 1:
        jitter = statistics.mean([abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))])
        
    config['latency_ms'] = avg_latency
    config['jitter_ms'] = jitter
    return config

def evaluate_configs(configs: List[Dict]) -> List[Dict]:
    # فیلتر اولیه (تعداد زیاد)
    target_configs = configs[:MAX_CONFIGS_TO_TEST]
    safe_print(f"\n🔍 مرحله ۲/۳: تست سریع (Fast Fail) روی {len(target_configs)} کانفیگ...")
    
    alive_configs = []
    total = len(target_configs)
    workers = min(50, os.cpu_count() * 5) # تعداد تردها را بهینه کردیم
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(quick_tcp_check, cfg): cfg for cfg in target_configs}
        count = 0
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                alive_configs.append(res)
            count += 1
            if count % 10 == 0 or count == total:
                print_progress(count, total, prefix='تست سریع:', suffix='')
                
    safe_print(f"\n✅ {len(alive_configs)} کانفیگ فعال شناسایی شد.")
    if not alive_configs: return []
    
    # تست دقیق (کیفیت)
    safe_print("\n🔍 مرحله ۳/۳: تست دقیق (Ping & Jitter)...")
    final_configs = []
    total_alive = len(alive_configs)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(measure_quality_metrics, cfg): cfg for cfg in alive_configs}
        count = 0
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                final_configs.append(res)
            count += 1
            if count % 5 == 0 or count == total_alive:
                print_progress(count, total_alive, prefix='تست دقیق:', suffix='')

    # مرتب‌سازی: اولویت با Jitter کمتر، سپس Latency کمتر
    final_configs.sort(key=lambda x: (x['jitter_ms'], x['latency_ms']))
    return final_configs

def save_results(configs: List[Dict]) -> None:
    if not configs:
        return

    top_configs = configs[:FINAL_MAX_OUTPUT_CONFIGS]
    output_lines = []
    
    for i, cfg in enumerate(top_configs, 1):
        # بازسازی لینک تمیز
        # ما لینک اصلی را داریم، اما می‌توانیم نامش را عوض کنیم
        original = cfg['original_config']
        # جایگزینی نام انتهای لینک با شماره و مشخصات
        # فرمت: #Config_1_Lat-50_Jit-2
        new_name = f"Config_{i}_Ping-{int(cfg['latency_ms'])}"
        
        # حذف Fragment قدیمی (#...) و اضافه کردن جدید
        clean_link = original.split('#')[0] + f"#{new_name}"
        output_lines.append(clean_link)
        
    output_str = "\n".join(output_lines)
    base64_str = base64.b64encode(output_str.encode('utf-8')).decode('utf-8')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(base64_str)
        
    safe_print(f"\n💾 فایل نهایی ذخیره شد: {path}")
    safe_print(f"🎉 تعداد {len(top_configs)} کانفیگ برتر انتخاب شدند.")

# --- اجرا ---

def main():
    start = time.time()
    all_configs = gather_configurations(CONFIG_URLS)
    ranked_configs = evaluate_configs(all_configs)
    save_results(ranked_configs)
    safe_print(f"\n⏱️ زمان کل اجرا: {time.time() - start:.2f} ثانیه")

if __name__ == "__main__":
    main()
