# UnveilChem_AiFiller 部署指南

## 概述

本文档详细说明如何将UnveilChem_AiFiller项目部署到生产环境，采用**前端EdgeOne Pages + 后端阿里云ECS**的混合部署架构。

## 部署架构

```
用户访问 → EdgeOne CDN (前端) → 阿里云ECS (后端API) → PostgreSQL数据库
                                  ↓
                          阿里云OSS (文件存储)
                                  ↓
                          阿里云OCR (文档识别)
```

## 前置要求

### 1. 基础设施准备
- **EdgeOne Pages账户**: 用于前端部署
- **阿里云账户**: 用于后端服务器和云服务
- **域名**: 用于生产环境访问

### 2. 服务器要求
- **ECS实例**: 2核4G或更高配置
- **操作系统**: CentOS 7+/Ubuntu 18.04+
- **网络**: 公网IP，安全组开放80/443端口

### 3. 云服务配置
- **阿里云RDS PostgreSQL**: 数据库服务
- **阿里云OSS**: 文件存储服务
- **阿里云OCR**: 文档识别服务

## 部署步骤

### 第一步：环境准备

1. **克隆代码库**
   ```bash
   git clone <repository-url>
   cd UnveilChem_AiFiller
   ```

2. **配置环境变量**
   ```bash
   cp deploy/.env.example .env
   # 编辑 .env 文件，配置生产环境参数
   ```

### 第二步：数据库迁移

1. **创建PostgreSQL数据库**
   ```bash
   # 在阿里云RDS控制台创建数据库
   # 数据库名: unveilchem
   # 用户名: unveilchem_user
   # 密码: 强密码
   ```

2. **执行数据库迁移**
   ```bash
   # 设置环境变量
   export POSTGRES_HOST=your-rds-host
   export POSTGRES_DB=unveilchem
   export POSTGRES_USER=unveilchem_user
   export POSTGRES_PASSWORD=your-password
   
   # 执行迁移脚本
   chmod +x deploy/migrate-database.sh
   ./deploy/migrate-database.sh
   ```

### 第三步：后端部署到阿里云

1. **配置服务器环境变量**
   ```bash
   # 在服务器上设置环境变量
   export ALIYUN_SERVER_IP=your-server-ip
   export ALIYUN_SSH_USER=root
   ```

2. **执行后端部署**
   ```bash
   chmod +x deploy-aliyun.sh
   ./deploy-aliyun.sh prod
   ```

3. **验证后端服务**
   ```bash
   # 检查服务状态
   curl http://your-server-ip/health
   
   # 查看服务日志
   ssh root@your-server-ip "sudo journalctl -u unveilchem -f"
   ```

### 第四步：前端部署到EdgeOne

1. **安装EdgeOne CLI**
   ```bash
   npm install -g @edgeone/cli
   ```

2. **配置环境变量**
   ```bash
   export EDGEONE_TOKEN=your-edgeone-token
   export EDGEONE_PROJECT=unveilchem
   export CUSTOM_DOMAIN=www.unveilchem.com
   ```

3. **执行前端部署**
   ```bash
   chmod +x deploy-edgeone.sh
   ./deploy-edgeone.sh
   ```

### 第五步：域名和SSL配置

1. **域名解析**
   - API域名: `api.unveilchem.com` → 阿里云ECS公网IP
   - 前端域名: `www.unveilchem.com` → EdgeOne提供的CNAME

2. **SSL证书申请**
   - 在阿里云SSL证书服务申请免费证书
   - 配置Nginx SSL证书
   - EdgeOne Pages自动提供SSL

## 配置文件说明

### 1. 后端配置文件 (`backend/app/config.py`)

主要配置项：
- 数据库连接
- 阿里云服务配置
- 服务器设置
- CORS跨域配置

### 2. 前端配置文件 (`frontend/vite.config.ts`)

主要配置项：
- API代理设置
- 构建输出配置
- 环境变量配置

### 3. 系统服务配置 (`deploy/unveilchem.service`)

服务管理配置：
- 服务描述
- 运行用户和目录
- 环境变量
- 重启策略

### 4. Nginx配置 (`deploy/nginx.conf`)

反向代理配置：
- 静态文件服务
- API代理
- 安全头设置
- SSL配置

## 监控和维护

### 1. 服务监控

```bash
# 查看服务状态
sudo systemctl status unveilchem

# 查看服务日志
sudo journalctl -u unveilchem -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/unveilchem_access.log
```

### 2. 性能监控

- **阿里云监控**: 监控ECS、RDS、OSS性能
- **EdgeOne监控**: 查看CDN性能和访问统计
- **应用监控**: 实现健康检查接口

### 3. 备份策略

```bash
# 数据库备份
pg_dump -h your-rds-host -U unveilchem_user unveilchem > backup.sql

# 文件备份
rsync -av /opt/unveilchem/uploads/ backup-server:/backup/unveilchem/
```

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查环境变量配置
   - 查看系统日志: `journalctl -u unveilchem`
   - 验证数据库连接

2. **前端无法访问API**
   - 检查CORS配置
   - 验证域名解析
   - 检查防火墙规则

3. **文件上传失败**
   - 检查OSS配置
   - 验证文件权限
   - 检查磁盘空间

### 日志分析

```bash
# 应用日志
sudo tail -f /var/log/unveilchem/app.log

# Nginx访问日志
sudo tail -f /var/log/nginx/unveilchem_access.log

# 错误日志
sudo tail -f /var/log/nginx/unveilchem_error.log
```

## 安全配置

### 1. 服务器安全
- 定期更新系统补丁
- 配置防火墙规则
- 使用密钥对登录
- 禁用root远程登录

### 2. 应用安全
- 使用强密码和密钥
- 配置HTTPS加密
- 实现输入验证和SQL注入防护
- 定期更新依赖包

### 3. 数据安全
- 数据库定期备份
- 敏感数据加密存储
- 访问权限控制
- 审计日志记录

## 成本估算

### 月度成本预估

| 服务 | 规格 | 月费用 |
|------|------|--------|
| 阿里云ECS | 2核4G | ~200元 |
| 阿里云RDS | 1核2G | ~150元 |
| 阿里云OSS | 100GB存储 | ~20元 |
| 阿里云OCR | 1000次调用 | ~50元 |
| EdgeOne Pages | 基础套餐 | 免费 |
| **总计** | | **~420元/月** |

## 性能优化建议

### 1. 前端优化
- 启用Gzip压缩
- 配置CDN缓存
- 优化图片资源
- 实现懒加载

### 2. 后端优化
- 数据库索引优化
- API响应缓存
- 连接池配置
- 异步任务处理

### 3. 基础设施优化
- 负载均衡配置
- 自动扩缩容
- 监控告警设置
- 日志分析优化

## 版本更新流程

1. **测试环境验证**
2. **数据库备份**
3. **后端服务更新**
4. **前端构建部署**
5. **功能验证测试**
6. **监控检查**

## 联系方式

如遇部署问题，请联系：
- 技术支持: tech-support@unveilchem.com
- 文档更新: docs@unveilchem.com
- 紧急问题: emergency@unveilchem.com

---

*最后更新: 2024年12月*
*版本: 1.0.0*