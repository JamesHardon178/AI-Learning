"""多线程分段下载 ModelScope GGUF 模型文件（国内直连，4 线程，支持断点续传）"""
import os
import sys
import time
import threading
import urllib.request

BASE = "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/master/"
FILES = [
    ("qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf", 3993201344),
    ("qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf", 689872288),
]
OUT_DIR = r"D:\Desktop\AI-Learning\04_RAG_KnowledgeBase\backend\.tmp_models"
THREADS = 4
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

os.makedirs(OUT_DIR, exist_ok=True)

def probe_size(url):
    req = urllib.request.Request(url, method="HEAD", headers=UA)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return int(resp.headers.get("Content-Length", 0))

def get_range(url, start, end, dst, part_idx, progress, lock):
    """下载 [start, end] 区间到 dst.part{part_idx}"""
    part_file = f"{dst}.part{part_idx}"
    done = os.path.getsize(part_file) if os.path.exists(part_file) else 0
    if done >= (end - start + 1):
        with lock:
            progress[part_idx] = done
        return
    start += done
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(part_file, "ab") as f:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                with lock:
                    progress[part_idx] = progress.get(part_idx, 0) + len(chunk)
    except Exception as e:
        with lock:
            print(f"  [part{part_idx}] 下载中断，将自动重试: {e}", flush=True)

def download_file(name, size):
    url = BASE + name
    dst = os.path.join(OUT_DIR, name)
    final = os.path.join(OUT_DIR, name.replace(".part", ""))
    if os.path.exists(final) and os.path.getsize(final) >= size:
        print(f"[跳过] {name} 已存在", flush=True)
        return
    print(f"[开始] {name} ({size/1024/1024/1024:.2f}GB)", flush=True)
    chunk = (size + THREADS - 1) // THREADS
    progress, lock = {}, threading.Lock()
    threads = []
    for i in range(THREADS):
        s = i * chunk
        e = min(s + chunk - 1, size - 1)
        t = threading.Thread(target=get_range, args=(url, s, e, dst, i, progress, lock))
        t.start()
        threads.append(t)
    start_t = time.time()
    while any(t.is_alive() for t in threads):
        time.sleep(2)
        with lock:
            done = sum(progress.values())
        spd = done / max(time.time() - start_t, 0.1) / 1024 / 1024
        print(f"  {name}: {done/1024/1024/1024:.2f}/{size/1024/1024/1024:.2f}GB "
              f"({done/size*100:.0f}%) {spd:.1f}MB/s", flush=True)
    for t in threads:
        t.join()
    # 合并分片
    with open(final, "wb") as out:
        for i in range(THREADS):
            pf = f"{dst}.part{i}"
            with open(pf, "rb") as p:
                while True:
                    b = p.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
            try:
                os.remove(pf)
            except Exception as e:
                print(f"  [警告] 清理临时文件失败（可稍后手动删除）: {e}", flush=True)
    print(f"[完成] {name}", flush=True)

def main():
    for name, size in FILES:
        download_file(name, size)

if __name__ == "__main__":
    main()
