import requests
import time
import uuid
import hashlib
import json
import os
import random

nonce = "C7DC5CAD-31CF-4431-8635-B415B75BF4F3"
SALT = "FN_Q29XHVmfV3mYX"

# 模拟真实设备的User-Agent列表
USER_AGENTS = [
    "boluobao/5.0.36(android;32)/H5/{device_token}/H5",
    "boluobao/5.0.35(android;31)/H5/{device_token}/H5", 
    "boluobao/5.0.34(android;30)/H5/{device_token}/H5",
    "boluobao/5.0.33(android;29)/H5/{device_token}/H5"
]

def random_delay(min_seconds=1, max_seconds=3):
    """随机延迟，模拟人类操作"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def md5_hex(input, case):
    m = hashlib.md5()
    m.update(input.encode())
    if case == 'Upper':
        return m.hexdigest().upper()
    else:
        return m.hexdigest()

def generate_headers(device_token):
    # 随机选择User-Agent
    user_agent_template = random.choice(USER_AGENTS)
    user_agent = user_agent_template.format(device_token=device_token)
    
    headers = {
        'Host': 'api.sfacg.com',
        'accept-charset': 'UTF-8',
        'authorization': 'Basic YW5kcm9pZHVzZXI6MWEjJDUxLXl0Njk7KkFjdkBxeHE=',
        'accept': 'application/vnd.sfacg.api+json;version=1',
        'user-agent': user_agent,
        'accept-encoding': 'gzip',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return headers

def check(cookie, headers):
    headers['cookie'] = cookie
    random_delay(1, 2)
    
    try:
        resp = requests.get('https://api.sfacg.com/user?', headers=headers, timeout=15)
        result = resp.json()
        if (result["status"]["httpCode"] == 200):
            nick_Name = result['data']['nickName']
            print(f"用户 {nick_Name} 登录成功")
            return True, nick_Name
        else:
            return False, ""
    except Exception as e:
        print(f"检查登录状态时出错: {str(e)}")
        return False, ""

def login(username, password, device_token, headers):
    timestamp = int(time.time() * 1000)
    sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
    headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
    data = json.dumps({"password": password, "shuMeiId": "", "username": username})
    url = "https://api.sfacg.com/sessions"
    
    # 登录前随机延迟
    random_delay(2, 4)
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=15)
        result = resp.json()
        if (result["status"]["httpCode"] == 200):
            cookie = requests.utils.dict_from_cookiejar(resp.cookies)
            return cookie[".SFCommunity"], cookie["session_APP"]
        else:
            print(f"登录失败: {result.get('status', {}).get('msg', '未知错误')}")
            return "", ""
    except Exception as e:
        print(f"登录时发生错误: {str(e)}")
        return "", ""

def logout(cookie, device_token, headers):
    """退出登录"""
    try:
        timestamp = int(time.time() * 1000)
        sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper")
        headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
        headers['cookie'] = cookie
        
        logout_url = "https://api.sfacg.com/sessions"
        resp = requests.delete(logout_url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            print("✅ 已安全退出账号")
            return True
        else:
            print("⚠️ 退出账号失败，但会话已失效")
            return False
    except Exception as e:
        print(f"⚠️ 退出账号时发生错误: {str(e)}")
        return False

def checkin(cookie, device_token, headers):
    headers["cookie"] = cookie
    Date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    signDate = json.dumps({"signDate": Date})
    total_coupons = 0
    
    print("开始执行签到和广告任务...")
    
    # 1. 每日签到
    random_delay(1, 2)
    timestamp = int(time.time() * 1000)
    sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
    headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
    
    try:
        resp = requests.put("https://api.sfacg.com/user/newSignInfo", headers=headers, data=signDate, timeout=15)
        result = resp.json()
        
        if 'status' in result and result['status']['httpCode'] == 200:
            coupon_num = result['data'][0]['num']
            total_coupons += coupon_num
            print(f"✅ 签到成功，获得代券: {coupon_num}")
        else:
            print("❌ 签到失败")
    except Exception as e:
        print(f"❌ 签到时发生错误: {str(e)}")
    
    # 2. 广告任务 - 增加更多随机性和延迟
    print("开始广告任务...")
    successful_ads = 0
    
    for i in range(8):  # 增加最大尝试次数
        if successful_ads >= 5:
            break
            
        try:
            # 随机延迟
            random_delay(2, 5)
            
            # 获取广告
            timestamp = int(time.time() * 1000)
            sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
            headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
            url = f"https://api.sfacg.com/user/advertisements?deviceToken={device_token.lower()}&page=0&size=20"
            requests.get(url, headers=headers, timeout=15)
            
            # 随机延迟
            random_delay(1, 3)
            
            # 上报广告观看
            timestamp = int(time.time() * 1000)
            sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
            headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
            url = f"https://api.sfacg.com/user/tasks/21/advertisement?aid=43&deviceToken={device_token.lower()}"
            requests.put(url, headers=headers, data=json.dumps({"num": 1}), timeout=15)
            
            # 随机延迟
            random_delay(1, 2)
            
            # 完成任务
            timestamp = int(time.time() * 1000)
            sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
            headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
            resp = requests.put("https://api.sfacg.com/user/tasks/21", headers=headers, data='', timeout=15)
            result = resp.json()
            
            if result['status']['httpCode'] == 200:
                coupon_num = result['data']['couponNum']
                total_coupons += coupon_num
                successful_ads += 1
                print(f"✅ 广告任务 {successful_ads}/5 完成，获得代券: {coupon_num}")
            else:
                print(f"⚠️ 广告任务 {i+1} 响应异常")
                
        except Exception as e:
            print(f"⚠️ 广告任务 {i+1} 出现异常: {str(e)}")
    
    print(f"广告任务完成: {successful_ads}/5 次")
    print(f"🎉 所有任务完成，总计获得代券: {total_coupons}")
    
    return total_coupons

def process_single_account(username, password, account_index, total_accounts):
    """处理单个账号"""
    print(f"\n🔍 正在处理账号 {account_index}/{total_accounts}: {username}")
    
    # 为每个账号生成独立的设备ID和headers
    device_token = str(uuid.uuid4()).upper()
    headers = generate_headers(device_token)
    
    # 登录前延迟，模拟人类操作
    random_delay(3, 6)
    
    SFCommunity, session_APP = login(username, password, device_token, headers)
    if not SFCommunity or not session_APP:
        print(f"❌ 账号 {username} 登录失败")
        return 0, False
        
    cookie = f".SFCommunity={SFCommunity}; session_APP={session_APP}"
    
    login_success, nick_name = check(cookie, headers)
    if not login_success:
        print(f"❌ 账号 {username} 登录状态检查失败")
        return 0, False
        
    print(f"✅ 用户 {nick_name} 登录成功")
    
    # 执行签到和广告任务
    coupons = checkin(cookie, device_token, headers)
    
    # 任务完成后退出账号
    random_delay(2, 4)  # 退出前延迟
    logout_success = logout(cookie, device_token, headers)
    
    if logout_success:
        print(f"✅ 账号 {username} 处理完成并已安全退出，获得代券: {coupons}")
    else:
        print(f"✅ 账号 {username} 处理完成，获得代券: {coupons}")
    
    return coupons, True

if __name__ == "__main__":
    print("🚀 SF轻小说多账号自动签到开始执行...")
    print("=" * 50)
    
    # 获取所有账号
    users_env = os.environ.get('username', '')
    if not users_env:
        print("❌ 错误: 未找到username环境变量")
        exit(1)
    
    # 解析多账号
    users = users_env.split(',')
    print(f"📋 检测到 {len(users)} 个账号")
    
    total_coupons = 0
    successful_accounts = 0
    
    # 处理每个账号
    for i, user in enumerate(users, 1):
        try:
            if '|' not in user:
                print(f"❌ 账号 {i} 格式错误: {user}")
                continue
                
            username, password = user.split('|')
            coupons, success = process_single_account(
                username.strip(), 
                password.strip(), 
                i, 
                len(users)
            )
            
            if success:
                total_coupons += coupons
                successful_accounts += 1
            
            # 账号间延迟，避免频繁切换
            if i < len(users):
                delay = random.uniform(10, 20)  # 10-20秒延迟
                print(f"⏳ 等待 {delay:.1f} 秒后处理下一个账号...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"❌ 处理账号 {i} 时发生错误: {str(e)}")
    
    # 输出总结
    print("\n" + "=" * 50)
    print(f"📊 任务执行完成:")
    print(f"   成功处理: {successful_accounts}/{len(users)} 个账号")
    print(f"   总计获得: {total_coupons} 代券")
    
    if successful_accounts > 0:
        print("🎉 多账号自动签到完成！")
    else:
        print("❌ 所有账号处理失败")
        exit(1)
