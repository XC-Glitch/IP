import schedule
import time
import requests
import re
from bs4 import BeautifulSoup  # 导入 bs4 解析库

def is_valid_ip_port(ip_port):
    """辅助函数：验证IP:端口格式是否正确"""
    # 匹配IPv4+端口的正则表达式
    pattern = r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?):([1-9]\d{0,4}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$'
    return re.match(pattern, ip_port) is not None

def check(proxy):
    """增强版验证函数：验证代理IP是否可用，且返回的IP是代理IP"""
    # 先校验格式，格式错误直接返回False
    if not is_valid_ip_port(proxy):
        print(f"❌ 代理 {proxy} 格式错误，跳过验证")
        return False
    
    try:
        # 构造代理格式：{'http': 'http://IP:端口', 'https': 'http://IP:端口'}
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        # 访问httpbin.org/ip，获取当前请求的IP（即代理IP）
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=5)
        if response.status_code == 200:
            # 解析返回的IP（处理可能的多IP情况，取第一个）
            resp_ip = response.json()['origin'].split(',')[0].strip()
            # 提取代理中的IP部分（去掉端口）
            proxy_ip = proxy.split(':')[0]
            # 验证返回的IP是否与代理IP一致
            if resp_ip == proxy_ip:
                return True
            else:
                print(f"❌ 代理 {proxy} 转发失败，实际使用IP：{resp_ip}")
                return False
        print(f"❌ 代理 {proxy} 请求成功但状态码非200：{response.status_code}")
        return False
    except requests.exceptions.ConnectTimeout:
        print(f"❌ 代理 {proxy} 连接超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 代理 {proxy} 连接失败")
        return False
    except Exception as e:
        # 捕获其他异常，只显示前50个字符避免输出过长
        print(f"❌ 代理 {proxy} 不可用：{str(e)[:50]}")
        return False

def refresh():
    """抓取 89ip.cn 网站的 IP 地址，解析并验证有效性"""
    print(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} 开始抓取IP =====")
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # 发送请求获取页面内容
        r = requests.get('http://www.89ip.cn/', headers=headers, timeout=10)
        r.encoding = 'utf-8'  # 统一编码，避免中文乱码
        
        # 使用 bs4 解析页面
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 定位 IP 表格
        ip_table = soup.find('table', attrs={'class': 'layui-table'})
        if not ip_table:
            print('未找到 IP 表格，页面结构可能已变更')
            return
        
        # 提取表格中的 IP 和端口
        raw_ip_list = []
        # 跳过表头，遍历数据行
        for tr in ip_table.find_all('tr')[1:]:
            td_list = tr.find_all('td')
            if len(td_list) >= 2:
                ip = td_list[0].text.strip()  # IP 地址列
                port = td_list[1].text.strip()  # 端口列
                if ip and port:
                    ip_port = f"{ip}:{port}"
                    raw_ip_list.append(ip_port)
        
        # 去重（避免重复IP）
        raw_ip_list = list(set(raw_ip_list))
        print(f'共抓取到 {len(raw_ip_list)} 个原始IP（已去重）')
        
        # 验证抓取到的IP是否可用
        valid_ip_list = []
        for proxy in raw_ip_list:
            if check(proxy):
                valid_ip_list.append(proxy)
                print(f'✅ 代理 {proxy} 可用且转发正常')
        
        # 存储有效IP
        if valid_ip_list:
            print(f'\n本次共获取 {len(valid_ip_list)} 个可用IP：{valid_ip_list}')
            # 写入文件（追加模式）
            with open('valid_ip_list.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} - {",".join(valid_ip_list)}\n')
        else:
            print('\n本次未获取到可用IP')
            
    except requests.exceptions.RequestException as e:
        print(f'请求失败：{e}')
    except Exception as e:
        print(f'解析失败：{e}')
    print(f"===== {time.strftime('%Y-%m-%d %H:%M:%S')} 抓取验证结束 =====\n")

# 定时任务：每30分钟执行一次
schedule.every(30).minutes.do(refresh)

# 立即执行一次
refresh()

# 持续运行定时任务
print('定时任务已启动，每30分钟抓取并验证一次IP...')
while True:
    schedule.run_pending()
    time.sleep(1)