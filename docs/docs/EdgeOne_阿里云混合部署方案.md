# UnveilChem_AiFiller 混合部署方案
## 前端EdgeOne + 后端阿里云

## 1. 部署架构概述

### 1.1 架构设计
```
用户访问 → EdgeOne CDN (前端) → 阿里云ECS/函数计算 (后端API)
                    ↓
                阿里云RDS (数据库)
                    ↓
                阿里云OSS (文件存储)
                    ↓
                阿里云OCR服务 (AI能力)
```

### 1.2 技术栈适配
- **前端**: React + Vite → EdgeOne Pages
- **后端**: FastAPI → 阿里云ECS/函数计算
- **数据库**: SQLite → 阿里云RDS PostgreSQL
- **文件存储**: 本地存储 → 阿里云OSS
- **OCR服务**: 本地Tesseract → 阿里云OCR

## 2. 前端EdgeOne部署方案

### 2.1 部署配置

#### EdgeOne Pages配置文件 (`edgeone.json`)
```json
{
  "name": "unveilchem-frontend",
  "build": {
    "command": "npm run build",
    "output": "dist"
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://api.unveilchem.com/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "VITE_API_BASE_URL": "https://api.unveilchem.com"
  }
}
```

#### Vite配置适配 (`vite.config.ts`)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/', // EdgeOne Pages根路径
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

### 2.2 环境变量配置

#### 生产环境变量 (`.env.production`)
```env
VITE_API_BASE_URL=https://api.unveilchem.com
VITE_APP_NAME=UnveilChem
VITE_APP_VERSION=1.0.0
```

### 2.3 部署脚本

#### EdgeOne CLI部署脚本 (`deploy-edgeone.sh`)
```bash
#!/bin/bash

# 构建前端
cd frontend
npm install
npm run build

# 安装EdgeOne CLI
npm install -g @edgeone/cli

# 部署到EdgeOne Pages
edgeone pages deploy --project unveilchem --token $EDGEONE_TOKEN

# 配置自定义域名
edgeone pages domain add --project unveilchem --domain www.unveilchem.com
```

## 3. 后端阿里云部署方案

### 3.1 服务器配置

#### ECS实例规格建议
- **实例类型**: ecs.g7.large (2核8G)
- **系统盘**: 100GB ESSD云盘
- **带宽**: 5Mbps
- **操作系统**: Ubuntu 22.04 LTS

#### 安全组配置
```bash
# 允许的端口
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (FastAPI)
```

### 3.2 应用部署配置

#### 系统服务配置 (`/etc/systemd/system/unveilchem.service`)
```ini
[Unit]
Description=UnveilChem Backend Service
After=network.target

[Service]
Type=simple
User=www
WorkingDirectory=/opt/unveilchem/backend
Environment=PATH=/opt/unveilchem/venv/bin
ExecStart=/opt/unveilchem/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Nginx反向代理配置 (`/etc/nginx/sites-available/unveilchem`)
```nginx
server {
    listen 80;
    server_name api.unveilchem.com;
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静态文件服务
    location /static/ {
        alias /opt/unveilchem/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3.3 数据库迁移

#### PostgreSQL配置 (`backend/app/config.py`)
```python
import os
from typing import List

class Settings:
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@rds-host:5432/unveilchem"
    )
    
    # 文件存储配置
    OSS_ACCESS_KEY: str = os.getenv("OSS_ACCESS_KEY")
    OSS_SECRET_KEY: str = os.getenv("OSS_SECRET_KEY")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    OSS_BUCKET: str = os.getenv("OSS_BUCKET", "unveilchem")
    
    # OCR服务配置
    ALIYUN_OCR_ACCESS_KEY: str = os.getenv("ALIYUN_OCR_ACCESS_KEY")
    ALIYUN_OCR_SECRET_KEY: str = os.getenv("ALIYUN_OCR_SECRET_KEY")
    ALIYUN_OCR_REGION: str = os.getenv("ALIYUN_OCR_REGION", "cn-hangzhou")
```

### 3.4 部署脚本

#### 阿里云ECS部署脚本 (`deploy-aliyun.sh`)
```bash
#!/bin/bash

# 服务器初始化脚本
set -e

# 创建应用目录
sudo mkdir -p /opt/unveilchem
sudo chown -R www:www /opt/unveilchem

# 安装系统依赖
sudo apt update
sudo apt install -y python3.10 python3.10-venv nginx

# 创建虚拟用户
sudo useradd -r -s /bin/false www

# 部署应用
cd /opt/unveilchem
git clone https://github.com/your-repo/unveilchem.git .

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量
cat > backend/.env << EOF
DATABASE_URL=postgresql://user:password@rds-host:5432/unveilchem
OSS_ACCESS_KEY=your-access-key
OSS_SECRET_KEY=your-secret-key
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET=unveilchem
ALIYUN_OCR_ACCESS_KEY=your-ocr-key
ALIYUN_OCR_SECRET_KEY=your-ocr-secret
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable unveilchem
sudo systemctl start unveilchem

# 配置Nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/unveilchem
sudo ln -sf /etc/nginx/sites-available/unveilchem /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 4. 数据库与存储方案

### 4.1 阿里云RDS配置
- **实例规格**: rds.pg.s2.large (2核4G)
- **存储**: 100GB SSD
- **备份**: 自动备份，保留7天
- **高可用**: 主备架构

### 4.2 阿里云OSS配置
- **存储类型**: 标准存储
- **地域**: 华东1（杭州）
- **权限**: 私有读写 + CDN加速
- **生命周期**: 自动归档30天前的文件

### 4.3 数据迁移脚本
```python
# backend/scripts/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

def migrate_database():
    # 连接SQLite
    sqlite_conn = sqlite3.connect('unveilchem.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    pg_cursor = pg_conn.cursor()
    
    # 迁移用户表
    sqlite_cursor.execute('SELECT * FROM users')
    users = sqlite_cursor.fetchall()
    
    if users:
        execute_values(
            pg_cursor,
            'INSERT INTO users (id, username, email, password_hash, role, created_at) VALUES %s',
            users
        )
    
    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()
```

## 5. 域名与SSL配置

### 5.1 域名规划
- **前端域名**: www.unveilchem.com (EdgeOne Pages)
- **API域名**: api.unveilchem.com (阿里云ECS)
- **文件域名**: files.unveilchem.com (阿里云OSS + CDN)

### 5.2 SSL证书配置
- **EdgeOne Pages**: 自动SSL证书
- **阿里云ECS**: 使用阿里云免费SSL证书
- **OSS CDN**: 配置HTTPS加速

## 6. 监控与运维

### 6.1 监控配置
- **阿里云云监控**: CPU、内存、磁盘、网络监控
- **应用监控**: 自定义业务指标
- **日志服务**: 应用日志收集分析

### 6.2 备份策略
- **数据库**: 自动备份 + 手动快照
- **代码**: Git仓库 + 定期打包备份
- **配置文件**: 版本控制 + 备份到OSS

## 7. 成本估算

### 7.1 月度成本估算
| 服务 | 规格 | 月费用 |
|------|------|--------|
| EdgeOne Pages | 基础版 | ¥100 |
| 阿里云ECS | ecs.g7.large | ¥400 |
| 阿里云RDS | rds.pg.s2.large | ¥300 |
| 阿里云OSS | 100GB存储 | ¥50 |
| 阿里云OCR | 按量计费 | ¥200 |
| **总计** | | **¥1050** |

### 7.2 与传统方案对比
| 方案 | 月成本 | 性能 | 运维复杂度 |
|------|--------|------|------------|
| 传统VPS | ¥800 | 中等 | 高 |
| 混合部署 | ¥1050 | 优秀 | 中等 |
| 全云原生 | ¥1500+ | 极佳 | 低 |

## 8. 部署时间计划

### 8.1 第一阶段（1-2天）
- [ ] 前端EdgeOne部署配置
- [ ] 域名解析配置
- [ ] SSL证书申请

### 8.2 第二阶段（2-3天）
- [ ] 阿里云资源创建
- [ ] 数据库迁移
- [ ] 后端应用部署

### 8.3 第三阶段（1天）
- [ ] 集成测试
- [ ] 性能优化
- [ ] 监控配置

## 9. 风险与应对

### 9.1 技术风险
- **跨域问题**: 配置CORS和代理
- **网络延迟**: 使用CDN和边缘计算
- **数据一致性**: 实施数据迁移验证

### 9.2 运维风险
- **服务中断**: 配置健康检查和自动恢复
- **数据丢失**: 实施多级备份策略
- **安全风险**: 配置WAF和访问控制

## 10. 总结

UnveilChem_AiFiller采用前端EdgeOne + 后端阿里云的混合部署方案，结合了两者的优势：

**优势**:
- ✅ 前端全球加速，用户体验优秀
- ✅ 后端稳定可靠，成本可控
- ✅ 架构灵活，易于扩展
- ✅ 运维复杂度适中

**建议**: 此方案适合中小型项目，既能享受边缘计算的优势，又能控制后端成本，是性价比较高的选择。