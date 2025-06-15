# OKX API代理服务
import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# 支持的免费代理服务
PROXY_SERVICES = [
    # 可以使用的免费HTTP代理
    "http://proxy-server:port",
    # 或者付费代理服务如：
    # ProxyMesh, Bright Data, Oxylabs等
]

class OKXProxyClient:
    def __init__(self):
        self.base_url = "https://www.okx.com/api/v5"
        self.proxies = None
        self.setup_proxy()
    
    def setup_proxy(self):
        """设置代理配置"""
        proxy_url = os.environ.get('PROXY_URL')
        if proxy_url:
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            print(f"🔗 已配置代理: {proxy_url}")
    
    def make_request(self, endpoint, params=None):
        """通过代理发送请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            # 添加User-Agent和其他头部
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(
                url, 
                params=params,
                proxies=self.proxies,
                headers=headers,
                timeout=15
            )
            return response
        except Exception as e:
            print(f"❌ 代理请求失败: {e}")
            return None

# 示例端点
@app.route('/proxy/okx/time')
def get_okx_time():
    client = OKXProxyClient()
    resp = client.make_request('/public/time')
    if resp and resp.status_code == 200:
        return resp.json()
    return {"error": "代理请求失败"}, 500

if __name__ == '__main__':
    app.run(debug=True)
