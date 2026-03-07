# UnveilChem 智能参数录入助手 - 部署指南

## 系统概述

UnveilChem_AiFiller 是一个基于前后端分离架构的智能化工文档参数提取系统，支持文档和图片的自动解析，提取化学实体和工艺参数,同时可以根据用户配置将提取到的参数自动填充到相关软件中，现支持化工类常用设计软件（如aspen、autocad等）。

## 技术栈

### 后端技术栈
- **框架**: FastAPI + Uvicorn
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **文档解析**: 
  - 基础解析: PyMuPDF, pytesseract
  - 高级解析: Pix2Text (复杂PDF), PaddleOCR (高精度OCR)
  - 统一解析器: UnifiedDocumentParser
- **化学解析**: chemdataextractor
- **自动化**: AutomationEngine, TaskScheduler
- **认证**: JWT + bcrypt

### 前端技术栈
- **框架**: React 18 + TypeScript
- **UI组件**: Ant Design 5.x
- **构建工具**: Vite
- **路由**: React Router 6
- **HTTP客户端**: Axios
- **状态管理**: Context API

## 环境要求

### 系统要求
- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.10+
- **Node.js**: 18+
- **内存**: 至少 8GB RAM (推荐16GB用于高级解析)
- **磁盘空间**: 至少 5GB 可用空间

### 软件依赖
- **Python包管理**: pip
- **Node.js包管理**: npm 或 yarn
- **数据库**: SQLite3 (内置) 或 PostgreSQL
- **OCR依赖**: Tesseract OCR, Ghostscript (可选，用于Camelot表格解析)

## 快速开始

### 1. 环境准备

#### 安装 Python (如果未安装)
```bash
# Windows: 从官网下载安装包
# 或使用 chocolatey
choco install python --version=3.13.0

# macOS: 使用 Homebrew
brew install python@3.13

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.13 python3.13-pip
```

#### 安装 Node.js (如果未安装)
```bash
# Windows: 从官网下载安装包
# 或使用 chocolatey
choco install nodejs --version=20.15.0

# macOS: 使用 Homebrew
brew install node@20

# Linux (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 安装系统依赖
```bash
# Windows: 使用 chocolatey 安装 Tesseract
choco install tesseract

# macOS: 使用 Homebrew 安装 Tesseract 和 Ghostscript
brew install tesseract ghostscript

# Linux (Ubuntu/Debian)
sudo apt install tesseract-ocr ghostscript
```

### 2. 手动启动

**后端服务**:
```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装基础依赖
pip install -r requirements.txt

# 安装高级解析依赖
pip install pix2text paddleocr

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端服务**:
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动服务
npm run dev
```

### 3. 访问应用

- **前端地址**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/api/docs
- **ReDoc文档**: http://localhost:8000/api/redoc

## 首次使用

### 1. 注册管理员账户
1. 打开前端应用 (http://localhost:5173)
2. 点击"注册"创建第一个账户
3. 第一个注册的用户自动获得管理员权限
4. 默认管理员账户为企业版，拥有全部功能

### 2. 功能测试
1. **文档解析**: 上传PDF/Word文档测试参数提取
2. **图片解析**: 上传化工图片测试结构识别
3. **高级解析**: 测试Pix2Text复杂PDF解析和PaddleOCR高精度识别
4. **自动化功能**: 测试自动化任务提交和执行
5. **管理后台**: 管理员可访问用户管理和系统设置

### 3. 版本功能说明

| 功能 | 基础版 | 专业版 | 企业版 |
|------|--------|--------|--------|
| 基础PDF解析 | ✅ | ✅ | ✅ |
| 基础OCR识别 | ✅ | ✅ | ✅ |
| Pix2Text复杂PDF解析 | ❌ | ✅ | ✅ |
| PaddleOCR高精度识别 | ❌ | ✅ | ✅ |
| 高级统一解析器 | ❌ | ❌ | ✅ |
| 月使用配额 | 100 | 500 | 无限 |
| 优先处理 | ❌ | ❌ | ✅ |
| 自动化功能 | ❌ | ✅ | ✅ |

## 配置文件

### 后端配置 (backend/app/config.py)
```python
from typing import List

class Settings:
    # 应用配置
    APP_NAME: str = "UnveilChem"
    VERSION: str = "1.0.0"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./unveilchem.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/jpg", "image/png", "image/tiff", "image/bmp"]
    ALLOWED_DOCUMENT_TYPES: List[str] = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    # 解析器配置
    ENABLE_OCR: bool = True
    ENABLE_CHEM_PARSING: bool = True
    ENABLE_ADVANCED_PARSING: bool = True  # 启用高级解析器
    
    # 自动化配置
    ENABLE_AUTOMATION: bool = True
    MAX_TASK_QUEUE_SIZE: int = 100
    TASK_TIMEOUT: int = 300  # 任务超时时间（秒）
    MAX_RETRIES: int = 3  # 任务最大重试次数
    
    # 版本默认配置
    DEFAULT_USER_VERSION: str = "basic"
    DEFAULT_MONTHLY_QUOTA: int = 100
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
```

### 前端配置 (frontend/vite.config.ts)
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
  },
})
```

## 生产环境部署

### Docker 部署 (推荐)

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/unveilchem
      - SECRET_KEY=your-production-secret-key-change-this
      - LOG_LEVEL=INFO
      - ENABLE_ADVANCED_PARSING=True
      - ENABLE_AUTOMATION=True
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/logs:/app/logs
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    volumes:
      - ./frontend/dist:/usr/share/nginx/html

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=unveilchem
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

创建 `backend/Dockerfile`:
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pix2text paddleocr

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p uploads logs

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

创建 `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine as build

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制应用代码
COPY . .

# 构建生产版本
RUN npm run build

# 使用Nginx作为生产服务器
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
```

创建 `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}
```

启动服务:
```bash
docker-compose up -d
```

### 传统部署

#### 后端部署
```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
pip install pix2text paddleocr

# 5. 设置环境变量
# Windows
set DATABASE_URL=postgresql://user:password@localhost:5432/unveilchem
set SECRET_KEY=your-production-secret-key
set LOG_LEVEL=INFO

# Linux/Mac
export DATABASE_URL=postgresql://user:password@localhost:5432/unveilchem
export SECRET_KEY=your-production-secret-key
export LOG_LEVEL=INFO

# 6. 创建必要目录
mkdir -p uploads logs

# 7. 使用生产服务器
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 300
```

#### 前端部署
```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 构建生产版本
npm run build

# 4. 配置Nginx
# 创建或修改nginx配置文件
# /etc/nginx/sites-available/unveilchem
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}

# 5. 启用站点并重启Nginx
sudo ln -s /etc/nginx/sites-available/unveilchem /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 故障排除

### 常见问题

1. **端口占用错误**
   - 后端: 修改 `uvicorn` 命令中的端口号，如 `--port 8001`
   - 前端: 修改 `vite.config.ts` 中的 `port` 配置

2. **依赖安装失败**
   - Python: 使用国内镜像 `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
   - Node.js: 使用淘宝镜像 `npm install --registry=https://registry.npmmirror.com`
   - 高级解析依赖: 确保网络连接正常，Pix2Text 和 PaddleOCR 依赖较大

3. **数据库连接错误**
   - 检查 SQLite 文件权限和路径
   - 生产环境确保 PostgreSQL 服务运行，检查连接字符串格式
   - 首次运行时确保数据库文件不存在，系统会自动创建

4. **文件上传失败**
   - 检查文件大小是否超过 `MAX_FILE_SIZE` 配置
   - 确认文件格式在 `ALLOWED_IMAGE_TYPES` 或 `ALLOWED_DOCUMENT_TYPES` 中
   - 检查上传目录权限

5. **解析器初始化失败**
   - 检查系统依赖是否安装: Tesseract OCR, Ghostscript
   - 查看日志获取具体错误信息
   - 确保 `ENABLE_ADVANCED_PARSING` 配置正确

6. **自动化任务执行失败**
   - 检查 `ENABLE_AUTOMATION` 配置是否为 `True`
   - 查看任务日志获取具体错误
   - 检查目标软件是否安装并可访问
   - 确认参数映射器配置正确

7. **OCR识别准确率低**
   - 确保图片清晰，分辨率足够
   - 尝试使用 PaddleOCR 高精度模式
   - 检查 Tesseract 语言包是否安装

8. **CORS 错误**
   - 检查后端 `ALLOWED_ORIGINS` 配置，确保包含前端域名
   - 生产环境中添加实际域名到允许列表

### 日志查看

**后端日志**:
```bash
# 查看实时日志
tail -f backend/logs/app.log

# 查看特定类型日志
grep -i "error" backend/logs/app.log

# 查看解析器相关日志
grep -i "parser" backend/logs/app.log

# 查看自动化相关日志
grep -i "automation" backend/logs/app.log
```

**前端日志**:
- 浏览器开发者工具 Console 标签
- 网络请求日志: 检查 API 请求状态和响应
- React DevTools: 调试组件状态

### 调试命令

**检查依赖版本**:
```bash
# 检查 Python 版本
python --version

# 检查 Node.js 版本
node --version

# 检查已安装的 Python 包
pip list

# 检查已安装的 Node.js 包
npm list --depth=0
```

**检查服务状态**:
```bash
# 检查后端服务是否运行
curl http://localhost:8000/api/health

# 检查前端服务是否运行
curl http://localhost:5173
```

**测试 API 端点**:
```bash
# 测试文档上传
curl -X POST -F "file=@test.pdf" http://localhost:8000/api/documents/upload

# 测试解析器状态
curl http://localhost:8000/api/documents/parser-status
```

## 安全建议

1. **生产环境配置**
   - 修改默认的 `SECRET_KEY`，使用强随机字符串
   - 使用 HTTPS，配置 SSL 证书
   - 配置防火墙规则，限制访问端口
   - 禁用调试模式
   - 配置适当的日志级别，避免敏感信息泄露

2. **数据库安全**
   - 使用强密码，定期更换
   - 定期备份数据，测试恢复流程
   - 限制数据库访问IP
   - 生产环境使用 PostgreSQL 而非 SQLite
   - 配置数据库连接池，限制最大连接数

3. **文件安全**
   - 设置合理的文件上传大小限制
   - 扫描上传文件，防止恶意文件
   - 使用安全的文件存储路径，避免路径遍历攻击
   - 定期清理临时文件
   - 配置适当的文件权限

4. **高级解析器安全**
   - 限制高级解析器的资源使用，防止DoS攻击
   - 对输入文档进行验证和清理
   - 监控解析器性能，设置超时机制
   - 定期更新解析器依赖，修复安全漏洞

5. **自动化功能安全**
   - 限制自动化任务的执行权限
   - 对自动化参数进行严格验证
   - 监控自动化任务执行，防止恶意操作
   - 设置任务队列大小限制，防止队列溢出
   - 定期清理过期任务

6. **用户权限安全**
   - 实施最小权限原则
   - 定期审核用户权限
   - 对敏感操作进行日志记录
   - 实施双因素认证（可选）
   - 限制管理员账号数量

7. **API安全**
   - 实施 API 速率限制
   - 对敏感 API 端点进行权限控制
   - 验证所有 API 请求参数
   - 实施 API 密钥或 JWT 认证
   - 定期审计 API 访问日志

## 技术支持

- **文档**: 
  - 部署指南: `部署指南.md`
  - 用户使用说明: `AIFILLER_USER_GUIDE.md`
  - 开发者文档: `AIFILLER_DEVELOPER_GUIDE.md`
  - 解析器模块说明: `PARSERS模块说明.md`
  - 升级执行方案: `AIFILLER_UPGRADE_PLAN.md`

- **问题反馈**: 
  - 创建 GitHub Issue
  - 发送邮件至: dev@unveilchem.com

- **社区支持**: 
  - 加入技术讨论群
  - 参与项目贡献

## 版本更新

### 更新步骤
1. **备份数据**
   - 备份数据库文件或使用数据库备份工具
   - 备份上传的文件和配置文件
   - 记录当前版本号

2. **停止服务**
   - 停止后端服务: `Ctrl+C` 或 `kill` 命令
   - 停止前端服务: `Ctrl+C`
   - 生产环境使用 `systemctl stop` 命令

3. **更新代码**
   - 使用 Git 更新代码: `git pull`
   - 或下载最新版本代码包

4. **安装新依赖**
   - 后端: `pip install -r requirements.txt`
   - 前端: `npm install`
   - 高级解析依赖: `pip install pix2text paddleocr`（如果有更新）

5. **数据库迁移**
   - 检查是否有数据库模型变更
   - 使用 Alembic 进行数据库迁移（如果配置了）
   - 或删除旧数据库文件，系统会自动创建新数据库（开发环境）

6. **配置更新**
   - 检查配置文件是否有新增或变更的配置项
   - 更新 `config.py` 中的配置

7. **重启服务**
   - 启动后端服务: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
   - 启动前端服务: `npm run dev`
   - 生产环境使用 `systemctl start` 命令

8. **验证更新**
   - 访问前端应用，检查功能是否正常
   - 测试文档解析和自动化功能
   - 查看日志，确保没有错误

### 更新注意事项
- 首次更新时建议在测试环境验证
- 复杂更新建议分步骤进行
- 记录更新过程，便于回滚
- 对于重大版本更新，建议先阅读更新说明
- 确保备份数据可恢复，防止更新失败

---

*最后更新: 2025年11月*