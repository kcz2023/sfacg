import requests
import time
import uuid
import hashlib
import json
import os
import random

class SfacgAutoCheckin:
    def __init__(self):
        self.nonce = "C7DC5CAD-31CF-4431-8635-B415B75BF4F3"
        self.SALT = "FN_Q29XHVmfV3mYX"
        self.session = requests.Session()
        
    def generate_headers(self, device_token=None):
        if not device_token:
            device_token = str(uuid.uuid4()).upper()
        
        headers = {
            'Host': 'api.sfacg.com',
            'accept-charset': 'UTF-8',
            'authorization': 'Basic YW5kcm9pZHVzZXI6MWEjJDUxLXl0Njk7KkFjdkBxeHE=',
            'accept': 'application/vnd.sfacg.api+json;version=1',
            'user-agent': f'boluobao/5.0.36(android;32)/H5/{device_token}/H5',
            'accept-encoding': 'gzip',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        return headers, device_token

    def md5_hex(self, input_str, case='Upper'):
        m = hashlib.md5()
        m.update(input_str.encode())
        if case == 'Upper':
            return m.hexdigest().upper()
        else:
            return m.hexdigest()

    def update_security_headers(self, headers, device_token):
        timestamp = int(time.time() * 1000)
        sign = self.md5_hex(f"{self.nonce}{timestamp}{device_token}{self.SALT}", 'Upper')
        headers['sfsecurity'] = f'nonce={self.nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
        return headers

    def login(self, username, password):
        """登录SF轻小说账号"""
        headers, device_token = self.generate_headers()
        headers = self.update_security_headers(headers, device_token)
        
        data = json.dumps({"password": password, "shuMeiId": "", "username": username})
        url = "https://api.sfacg.com/sessions"
        
        try:
            resp = self.session.post(url, headers=headers, data=data, timeout=10)
            if resp.status_code == 200 and resp.json()["status"]["httpCode"] == 200:
                cookie = requests.utils.dict_from_cookiejar(resp.cookies)
                return cookie.get(".SFCommunity", ""), cookie.get("session_APP", ""), device_token
        except Exception as e:
            print(f"登录异常: {str(e)}")
        
        return "", "", ""

    def check_login(self, cookie, device_token):
        """检查登录状态"""
        headers, _ = self.generate_headers(device_token)
        headers['cookie'] = cookie
        headers = self.update_security_headers(headers, device_token)
        
        try:
            resp = self.session.get('https://api.sfacg.com/user?', headers=headers, timeout=10)
            if resp.status_code == 200:
                user_data = resp.json()
                if user_data["status"]["httpCode"] == 200:
                    nick_name = user_data['data']['nickName']
                    return True, nick_name
        except Exception as e:
            print(f"检查登录状态异常: {str(e)}")
        
        return False, ""

    def daily_checkin(self, cookie, device_token):
        """每日签到"""
        headers, _ = self.generate_headers(device_token)
        headers['cookie'] = cookie
        headers = self.update_security_headers(headers, device_token)
        
        date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        sign_data = json.dumps({"signDate": date})
        
        try:
            resp = self.session.put(
                "https://api.sfacg.com/user/newSignInfo", 
                headers=headers, 
                data=sign_data,
                timeout=10
            )
            result = resp.json()
            
            if 'status' in result and result['status']['httpCode'] == 200:
                coupon_num = result['data'][0]['num']
                print(f"  ✅ 签到成功，获得代券: {coupon_num}")
                return coupon_num
            else:
                print(f"  ❌ 签到失败: {result.get('status', {}).get('msg', '未知错误')}")
        except Exception as e:
            print(f"  ❌ 签到异常: {str(e)}")
        
        return 0

    def ad_task(self, cookie, device_token):
        """广告任务"""
        headers, _ = self.generate_headers(device_token)
        headers['cookie'] = cookie
        
        total_ad_coupons = 0
        successful_ads = 0
        max_attempts = 8  # 最大尝试次数
        target_success = 5  # 目标成功次数
        
        print("  开始广告任务...")
        
        for attempt in range(max_attempts):
            if successful_ads >= target_success:
                break
                
            try:
                # 更新安全头
                headers = self.update_security_headers(headers, device_token)
                
                # 1. 获取广告列表
                ad_url = f"https://api.sfacg.com/user/advertisements?deviceToken={device_token.lower()}&page=0&size=20"
                self.session.get(ad_url, headers=headers, timeout=10)
                
                # 2. 上报广告观看
                headers = self.update_security_headers(headers, device_token)
                report_url = f"https://api.sfacg.com/user/tasks/21/advertisement?aid=43&deviceToken={device_token.lower()}"
                self.session.put(report_url, headers=headers, data=json.dumps({"num": 1}), timeout=10)
                
                # 3. 完成任务领取代券
                headers = self.update_security_headers(headers, device_token)
                task_url = "https://api.sfacg.com/user/tasks/21"
                resp = self.session.put(task_url, headers=headers, data='', timeout=10)
                result = resp.json()
                
                if result.get('status', {}).get('httpCode') == 200:
                    coupon_num = result['data']['couponNum']
                    total_ad_coupons += coupon_num
                    successful_ads += 1
                    print(f"    ✅ 广告任务 {successful_ads}/{target_success} 完成，获得代券: {coupon_num}")
                else:
                    print(f"    ⚠️ 广告任务 {attempt+1} 响应异常")
                
            except Exception as e:
                print(f"    ⚠️ 广告任务 {attempt+1} 出现异常: {str(e)}")
            
            # 随机等待1-3秒，避免请求过于频繁
            time.sleep(random.uniform(1, 3))
        
        print(f"  广告任务完成: {successful_ads}/{target_success} 次")
        return total_ad_coupons

    def process_account(self, username, password):
        """处理单个账号的所有任务"""
        print(f"🔍 处理账号: {username}")
        
        # 登录
        sfcommunity, session_app, device_token = self.login(username, password)
        if not sfcommunity or not session_app:
            print(f"  ❌ 登录失败")
            return 0, 0
        
        cookie = f".SFCommunity={sfcommunity}; session_APP={session_app}"
        
        # 检查登录状态
        is_logged_in, nick_name = self.check_login(cookie, device_token)
        if not is_logged_in:
            print(f"  ❌ 登录状态检查失败")
            return 0, 0
        
        print(f"  👤 用户 {nick_name} 登录成功")
        
        # 执行签到
        checkin_coupons = self.daily_checkin(cookie, device_token)
        
        # 执行广告任务
        ad_coupons = self.ad_task(cookie, device_token)
        
        total_coupons = checkin_coupons + ad_coupons
        print(f"  🎉 账号 {username} 任务完成，总计获得代券: {total_coupons}\n")
        
        return total_coupons, 1

    def run(self):
        """主运行函数"""
        print("🚀 SF轻小说自动签到开始执行...")
        print("=" * 50)
        
        # 获取账号信息
        users_env = os.environ.get('username', '')
        if not users_env:
            print("❌ 未找到账号信息，请检查USERNAME环境变量")
            return
        
        users = users_env.split(',')
        total_accounts = len(users)
        successful_accounts = 0
        total_coupons_all = 0
        
        print(f"📋 共发现 {total_accounts} 个账号")
        
        # 处理每个账号
        for user in users:
            try:
                username, password = user.split('|')
                coupons, success = self.process_account(username.strip(), password.strip())
                total_coupons_all += coupons
                successful_accounts += success
            except ValueError:
                print(f"❌ 账号格式错误: {user}")
            except Exception as e:
                print(f"❌ 处理账号异常: {str(e)}")
        
        # 输出总结
        print("=" * 50)
        print(f"📊 任务执行完成:")
        print(f"   成功处理: {successful_accounts}/{total_accounts} 个账号")
        print(f"   总计获得: {total_coupons_all} 代券")
        print("🎉 所有任务已完成！")

if __name__ == "__main__":
    checker = SfacgAutoCheckin()
    checker.run()
