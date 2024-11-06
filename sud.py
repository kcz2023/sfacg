import requests
import time
import uuid
import sys
import hashlib
import json
import os
from functools import lru_cache
from webdav4-client import Client
import os

class NovelDownloader:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.nonce = "C7DC5CAD-31CF-4431-8635-B415B75BF4F3"
        self.device_token = str(uuid.uuid4()).upper()
        self.salt = "FN_Q29XHVmfV3mYX"
        self.headers = {
            'Host': 'api.sfacg.com',
            'accept-charset': 'UTF-8',
            'authorization': 'Basic YW5kcm9pZHVzZXI6MWEjJDUxLXl0Njk7KkFjdkBxeHE=',
            'accept': 'application/vnd.sfacg.api+json;version=1',
            'user-agent': f'boluobao/5.0.36(android;32)/H5/{self.device_token}/H5',
            'accept-encoding': 'gzip',
            'Content-Type': 'application/json; charset=UTF-8',
            'cookie': cookie
        }
        # 从环境变量获取WebDAV配置
        self.dav_host = os.environ.get('WEBDAV_HOST')
        self.dav_username = os.environ.get('WEBDAV_USERNAME') 
        self.dav_password = os.environ.get('WEBDAV_PASSWORD')
        
    def dav_upload(self, local_path, remote_path):
        """WebDAV文件上传"""
        try:
            if not all([self.dav_host, self.dav_username, self.dav_password]):
                print("WebDAV配置不完整,请检查环境变量")
                return False
                
            client = Client(self.dav_host, auth=(self.dav_username, self.dav_password))
            local = os.path.abspath(local_path)
            remote = f"/{remote_path.lstrip('/')}"
            
            client.upload_file(local, remote)
            print(f"上传成功: {local} -> {remote}")
            return True
        except Exception as e:
            print(f"上传失败: {str(e)}")
            return False
        
    def update_security_headers(self):
        """更新安全头"""
        timestamp = int(time.time() * 1000)
        sign = hashlib.md5(f"{self.nonce}{timestamp}{self.device_token}{self.salt}".encode()).hexdigest().upper()
        return f'nonce={self.nonce}&timestamp={timestamp}&devicetoken={self.device_token}&sign={sign}'
        
    def get_balance(self) -> dict:
        """获取账户余额"""
        self.headers['sfsecurity'] = self.update_security_headers()
        
        resp = requests.get("https://api.sfacg.com/user/money", headers=self.headers).json()
        balance = {}
        print(resp)
        if resp["status"]["httpCode"] == 200:
            balance = {
                "fireMoney": resp["data"]["fireMoneyRemain"],
                "coupons": resp["data"]["couponsRemain"]
            }
            print(f"\n=== 账户余额 ===")
            print(f"火卷余额: {balance['fireMoney']}")
            print(f"代券余额: {balance['coupons']}")
            print("-" * 30)
        else:
            print("获取余额失败!")        
        return balance

    def get_subscriptions(self) -> list:
        """获取订阅记录"""
        self.headers['sfsecurity'] = self.update_security_headers()
        
        resp = requests.get("https://api.sfacg.com/user/consumeitems?type=novel&page=0&size=12", headers=self.headers).json()
        
        if resp["status"]["httpCode"] == 200:
            print("\n=== 获取订阅记录 ===")
            return [{
                "consumeChapterNum": sub["consumeChapterNum"],
                "novelId": sub["novel"]["novelId"],
                "novelName": sub["novel"]["novelName"],
                "authorName": sub["novel"]["authorName"], 
                "lastUpdateTime": sub["novel"]["lastUpdateTime"]
            } for sub in resp["data"]]
        
        print("获取订阅记录失败!")
        return []

    def get_chapters(self, novel_id: int) -> list:
        """获取小说章节列表"""
        self.headers['sfsecurity'] = self.update_security_headers()
        
        resp = requests.get(f"https://api.sfacg.com/novels/{novel_id}/dirs?expand=originNeedFireMoney", headers=self.headers).json()
        
        if resp["status"]["httpCode"] == 200:
            print(f"\n=== 章节列表 ===")
            chapters = []
            for volume in resp["data"]["volumeList"]:
                chapters.extend([{
                    "chapterId": chapter["chapId"],
                    "title": chapter["title"],
                    "isVip": chapter["isVip"],
                    "needFireMoney": chapter["originNeedFireMoney"]
                } for chapter in volume["chapterList"]])
            return chapters
            
        print("获取章节列表失败!")
        return []

    def buy_chapter(self, chapter_id: int) -> bool:
        """购买小说章节"""
        self.headers['sfsecurity'] = self.update_security_headers()
        
        url = f"https://api.sfacg.com/Chaps/{chapter_id}?expand=content,needFireMoney,originNeedFireMoney,tsukkomi,chatlines,isbranch,isContentEncrypted,authorTalk&autoOrder=true"
        resp = requests.get(url, headers=self.headers).json()
        
        if resp["status"]["httpCode"] == 200:
            print(f"章节《{resp['data']['title']}》购买成功!")
            return True
        elif resp["status"]["httpCode"] == 403:
            print(f"章节购买失败: {resp['status']['msg']}")
            return False

    def buy_novel_chapters(self) -> dict:
        """获取所有订阅小说的章节信息"""
        print("\n=== 获取所有订阅小说章节 ===")
        
        subscriptions = self.get_subscriptions()
        if not subscriptions:
            return {}
            
        novel_chapters = []
        flag = True
        i = 0
        while i < len(subscriptions) and flag:
            sub = subscriptions[i]
            chapters = self.get_chapters(sub["novelId"])
            j = 0
            while j < len(chapters) and flag:
                chapter = chapters[j]
                if chapter["isVip"] and chapter["needFireMoney"] > 0:
                    if not self.buy_chapter(chapter["chapterId"]):
                        print(f"小说《{sub['novelName']}》章节《{chapter['title']}》购买失败,终止获取章节")
                        flag = False
                        return sub["novelName"], novel_chapters
                    else:
                        print(f"小说《{sub['novelName']}》章节《{chapter['title']}》购买成功,消耗火币{chapter['needFireMoney']}")
                
                novel_chapters.append({
                    "title": chapter["title"],
                    "chapterId": chapter["chapterId"]
                })
                j += 1
            i += 1
        return sub["novelName"], novel_chapters

    def download_chapter(self, chapters: str):
        content = ""
        self.headers['sfsecurity'] = self.update_security_headers()
        url = f"https://api.sfacg.com/Chaps/{chapters}?expand=content%2CneedFireMoney%2CoriginNeedFireMoney%2Ctsukkomi%2Cchatlines%2Cisbranch%2CisContentEncrypted%2CauthorTalk&autoOrder=false"
        resp = requests.get(url, headers=self.headers).json() 
        
        # 加载字典文件
        with open('dict.json', 'r', encoding='utf-8') as f:
            dictionary = json.load(f)
            
        if (resp['status']['httpCode'] == 200):
            content += resp['data']['title'] + '\n'
            tmp = ""
            warn = ""
            if 'content' in resp['data']:
                tmp += resp['data']['content']
                if 'expand' in resp['data'] and 'content' in resp['data']['expand']:
                    tmp += resp['data']['expand']['content']
            else:
                tmp += resp['data']['expand']['content']
            for char in tmp:
                if char in dictionary:
                    content += dictionary[char]
                else:
                    content += char
            content += '\n' + warn
            print(f"{resp['data']['title']} 已下载")
        else:
            print(f"{chapters} 下载失败，请检查是否未订阅该章节")
        return content

    def save_content(self, novel_name: str, chapters: list) -> None:
        """保存内容到本地文件并上传到WebDAV"""
        # 创建小说目录和配置目录
        os.makedirs("novels", exist_ok=True)
        os.makedirs("config", exist_ok=True)
        
        # 生成文件名
        file_path = os.path.join(os.getcwd(), "novels", f"{novel_name}.txt")
        config_path = os.path.join(os.getcwd(), "config", f"{novel_name}.json")
        # 检查配置文件是否存在
        downloaded_chapters = []
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    downloaded_chapters = json.load(f)
            except Exception as e:
                print(f"× 读取配置失败: {str(e)}")
        
        # 获取新增章节
        new_chapters = []
        for chapter in chapters:
            if chapter not in downloaded_chapters:
                new_chapters.append(chapter)
        
        if not new_chapters:
            print(f"没有新增章节需要下载")
            return
            
        try:
            # 保存新增章节内容
            content = ""
            for chapter in new_chapters:
                content += self.download_chapter(chapter["chapterId"])
                
            # 追加写入文件
            mode = "a" if os.path.exists(file_path) else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
                
            # 更新配置文件
            downloaded_chapters.extend(new_chapters)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(downloaded_chapters, f, ensure_ascii=False, indent=2)
                
            print(f"\n✓ 新增{len(new_chapters)}个章节已保存到: {file_path}")
            
            # 上传到WebDAV
            try:
                if self.dav_upload(file_path, f"{novel_name}.txt"):
                    print(f"✓ 文件已上传到WebDAV")
                else:
                    print(f"× WebDAV上传失败")
            except Exception as e:
                print(f"× WebDAV上传出错: {str(e)}")
                
        except Exception as e:
            print(f"\n× 保存失败: {str(e)}")
