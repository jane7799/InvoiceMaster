from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import json
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# 配置日志
LOG_FILE = "/data/downloads.log"
STATS_FILE = "/data/stats.json"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_stats():
    """加载统计数据"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"total": 0, "files": {}, "regions": {}}

def save_stats(stats):
    """保存统计数据"""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def get_region(ip):
    """简单的IP地区判断（可扩展为调用IP库）"""
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
        return "内网"
    # 简化处理，实际可以接入IP地区库
    return "未知"

@app.route('/api/download/<path:filename>')
def track_download(filename):
    """记录下载并重定向到实际文件"""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    
    region = get_region(ip)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # 记录日志
    log_entry = f"下载: {filename} | IP: {ip} | 地区: {region} | UA: {user_agent[:50]}"
    logging.info(log_entry)
    
    # 更新统计
    stats = load_stats()
    stats["total"] += 1
    stats["files"][filename] = stats["files"].get(filename, 0) + 1
    stats["regions"][region] = stats["regions"].get(region, 0) + 1
    save_stats(stats)
    
    # 重定向到实际文件
    return redirect(f"/downloads/{filename}")

@app.route('/api/stats')
def get_stats():
    """获取统计数据"""
    stats = load_stats()
    return jsonify(stats)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # 确保数据目录存在
    os.makedirs("/data", exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
