# 🎯 SF轻小说自动签到与订阅

> ⚠️ 该项目仅用于学习，出现的任何问题我不承担任何责任。

这是一个基于GitHub Actions的SF轻小说自动签到和订阅脚本，只需Fork即可使用。

## ✨ 功能特点

- 🎁 每日自动签到获取代券
- 📖 自动阅读任务
- 📺 自动广告任务
- 🔔 自动订阅章节
- ♻️ 每月自动保活
- 📚 自动下载已订阅书籍并上传至坚果云

## 📝 使用说明

### 1️⃣ Fork仓库
直接Fork本仓库到你的账户下

### 2️⃣ 配置账户信息（必需）

#### 🔑 配置Actions权限
1. 进入 `设置 > Actions > General > Workflow permissions`
2. 将权限更改为"读取和写入权限"
3. 这是为了授予"每月更新操作"更新仓库的权限，防止GitHub因长期不活动禁用Actions

#### 🔒 添加账户凭据 
1. 进入 `设置 > Secrets > Actions > New repository secret`
2. 添加以下信息:
   - `USERNAME`: 多账号用`,`隔开,每个账号用`|`隔开,格式为`手机号|密码`
   - `WEBDAV_HOST`: 坚果云WebDAV地址
   - `WEBDAV_USERNAME`: 坚果云WebDAV账号
   - `WEBDAV_PASSWORD`: 坚果云WebDAV密码

### 3️⃣ 自动订阅
订阅顺序从[书架]的第一部书开始

### 4️⃣ 配置执行时间（可选）
修改`.github/workflows/health-report.yml`中的计划任务时间:
