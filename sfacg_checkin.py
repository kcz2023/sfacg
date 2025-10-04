import requests
import time
import uuid
import hashlib
import json
import os

def process_single_account(username, password):
    """处理单个账号 - 完全保持原有成功代码不变"""
    nonce = "C7DC5CAD-31CF-4431-8635-B415B75BF4F3"
    device_token = str(uuid.uuid4())
    SALT = "FN_Q29XHVmfV3mYX"
    headers = {
        'Host': 'api.sfacg.com',
        'accept-charset': 'UTF-8',
        'authorization': 'Basic YW5kcm9pZHVzZXI6MWEjJDUxLXl0Njk7KkFjdkBxeHE=',
        'accept': 'application/vnd.sfacg.api+json;version=1',
        'user-agent': f'boluobao/5.0.36(android;32)/H5/{device_token}/H5',
        'accept-encoding': 'gzip',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    device_token = device_token.upper()

    def md5_hex(input, case):
        m = hashlib.md5()
        m.update(input.encode())
        if case == 'Upper':
            return m.hexdigest().upper()
        else:
            return m.hexdigest()

    def check(cookie):
        headers['cookie'] = cookie
        resp = requests.get('https://api.sfacg.com/user?', headers=headers).json()
        if (resp["status"]["httpCode"] == 200):
            nick_Name = resp['data']['nickName']
            print(f"用户 {nick_Name} 登录成功")
            return True
        else:
            return False

    def login():
        timestamp = int(time.time() * 1000)
        sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
        headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
        data = json.dumps({"password": password, "shuMeiId": "", "username": username})
        url = "https://api.sfacg.com/sessions"
        
        resp = requests.post(url, headers=headers, data=data)
        if (resp.json()["status"]["httpCode"] == 200):
            cookie = requests.utils.dict_from_cookiejar(resp.cookies)
            return cookie[".SFCommunity"], cookie["session_APP"]
        else:
            return "", ""

    def checkin(cookie):
        headers["cookie"] = cookie
        Date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        signDate = json.dumps({"signDate": Date})
        total_coupons = 0
        
        print("开始执行签到和广告任务...")
        
        # 1. 每日签到
        timestamp = int(time.time() * 1000)
        sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
        headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
        resp = requests.put("https://api.sfacg.com/user/newSignInfo", headers=headers, data=signDate).json()
        
        if 'status' in resp and resp['status']['httpCode'] == 200:
            coupon_num = resp['data'][0]['num']
            total_coupons += coupon_num
            print(f"✅ 签到成功，获得代券: {coupon_num}")
        else:
            print("❌ 签到失败")
        
        # 2. 广告任务
        print("开始广告任务...")
        for i in range(5):
            # 获取广告
            timestamp = int(time.time() * 1000)
            sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
            headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
            url = f"https://api.sfacg.com/user/advertisements?deviceToken={device_token.lower()}&page=0&size=20"
            requests.get(url, headers=headers)
            
            # 上报广告观看
            timestamp = int(time.time() * 1000)
            sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
            headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
            url = f"https://api.sfacg.com/user/tasks/21/advertisement?aid=43&deviceToken={device_token.lower()}"
            requests.put(url, headers=headers, data=json.dumps({"num": 1}))
            
            # 完成任务
            timestamp = int(time.time() * 1000)
            sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
            headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
            resp = requests.put("https://api.sfacg.com/user/tasks/21", headers=headers, data='').json()
            
            if resp['status']['httpCode'] == 200:
                coupon_num = resp['data']['couponNum']
                total_coupons += coupon_num
                print(f"✅ 广告任务 {i+1}/5 完成，获得代券: {coupon_num}")
            else:
                print(f"❌ 广告任务 {i+1}/5 失败")
            
            time.sleep(2)  # 等待2秒
        
        print(f"🎉 任务完成，总计获得代券: {total_coupons}")
        return total_coupons

    # 执行单个账号流程
    print(f"正在处理账号: {username}")
    SFCommunity, session_APP = login()
    cookie = f".SFCommunity={SFCommunity}; session_APP={session_APP}"
    
    if check(cookie):
        coupons = checkin(cookie)
        print(f"账号 {username} 处理完成，获得代券: {coupons}\n")
        return coupons
    else:
        print(f"账号 {username} 登录失败\n")
        return 0

if __name__ == "__main__":
    # 获取所有账号
    users = os.environ.get('username').split(',')  
    total_coupons = 0
    
    for user in users:
        username, password = user.split('|')
        coupons = process_single_account(username, password)
        total_coupons += coupons
    
    print(f"所有账号处理完成，总计获得代券: {total_coupons}")
