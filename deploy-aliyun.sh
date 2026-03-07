#!/bin/bash

# UnveilChem_AiFiller 阿里云后端部署脚本
# 使用方法: ./deploy-aliyun.sh [环境: dev|prod]

set -e

ENVIRONMENT=${1:-prod}
SERVER_IP=""
SSH_USER="root"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查参数
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    log_error "无效的环境参数: $ENVIRONMENT"
    echo "用法: $0 [dev|prod]"
    exit 1
fi

log_info "🚀 开始部署UnveilChem后端到阿里云 ($ENVIRONMENT环境)..."

# 检查必需的环境变量
if [ -z "$ALIYUN_SERVER_IP" ]; then
    read -p "🌐 请输入阿里云服务器IP地址: " SERVER_IP
else
    SERVER_IP="$ALIYUN_SERVER_IP"
fi

if [ -z "$ALIYUN_SSH_USER" ]; then
    read -p "👤 请输入SSH用户名 (默认: root): " SSH_USER
    SSH_USER=${SSH_USER:-root}
else
    SSH_USER="$ALIYUN_SSH_USER"
fi

# 检查SSH连接
log_info "🔗 检查SSH连接..."
if ! ssh -o ConnectTimeout=10 "$SSH_USER@$SERVER_IP" "echo 'SSH连接成功'"; then
    log_error "SSH连接失败，请检查服务器状态和凭据"
    exit 1
fi

# 创建部署目录结构
log_info "📁 创建服务器目录结构..."
ssh "$SSH_USER@$SERVER_IP" "
set -e
sudo mkdir -p /opt/unveilchem/{backend,logs,uploads,static}
sudo chown -R www:www /opt/unveilchem
sudo chmod -R 755 /opt/unveilchem
"

# 上传后端代码
log_info "📤 上传后端代码..."
rsync -avz --delete \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='uploads/*' \
    backend/ "$SSH_USER@$SERVER_IP:/opt/unveilchem/backend/"

# 上传配置文件
log_info "⚙️  上传配置文件..."
scp deploy/unveilchem.service "$SSH_USER@$SERVER_IP:/tmp/"
scp deploy/nginx.conf "$SSH_USER@$SERVER_IP:/tmp/"

# 在服务器上执行部署操作
log_info "🔧 在服务器上执行部署操作..."
ssh "$SSH_USER@$SERVER_IP" "
set -e

# 安装系统依赖
log_info '📦 安装系统依赖...'
sudo yum update -y || sudo apt update -y
sudo yum install -y python3 python3-pip nginx postgresql-client || \
    sudo apt install -y python3 python3-pip nginx postgresql-client

# 创建Python虚拟环境
log_info '🐍 创建Python虚拟环境...'
sudo python3 -m venv /opt/unveilchem/venv
sudo /opt/unveilchem/venv/bin/pip install --upgrade pip

# 安装Python依赖
log_info '📚 安装Python依赖...'
cd /opt/unveilchem/backend
sudo /opt/unveilchem/venv/bin/pip install -r requirements.txt

# 配置Nginx
log_info '🌐 配置Nginx...'
sudo cp /tmp/nginx.conf /etc/nginx/conf.d/unveilchem.conf
sudo nginx -t && sudo systemctl reload nginx

# 配置系统服务
log_info '🔧 配置系统服务...'
sudo cp /tmp/unveilchem.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable unveilchem.service

# 创建日志目录
sudo mkdir -p /var/log/unveilchem
sudo chown www:www /var/log/unveilchem

# 设置文件权限
sudo chown -R www:www /opt/unveilchem
sudo chmod -R 755 /opt/unveilchem

log_info '✅ 服务器配置完成'
"

# 启动服务
log_info "🚀 启动后端服务..."
ssh "$SSH_USER@$SERVER_IP" "
sudo systemctl start unveilchem.service
sudo systemctl status unveilchem.service
"

# 健康检查
log_info "🔍 执行健康检查..."
if curl -s -f "http://$SERVER_IP/health" > /dev/null; then
    log_info "✅ 健康检查通过"
else
    log_warn "⚠️  健康检查失败，请检查服务状态"
fi

log_info ""
log_info "🎉 UnveilChem后端部署成功!"
log_info "🌐 服务器地址: $SERVER_IP"
log_info "🔧 服务状态: sudo systemctl status unveilchem"
log_info "📊 日志查看: sudo journalctl -u unveilchem -f"
log_info ""
log_info "💡 后续操作:"
log_info "1. 配置域名解析"
log_info "2. 申请SSL证书"
log_info "3. 配置数据库连接"
log_info "4. 配置阿里云OSS和OCR服务"
log_info ""

# 生成环境配置示例
log_info "📋 环境变量配置示例:"
cat << EOF
# 数据库配置
export DATABASE_URL=postgresql://unveilchem_user:password@rds-host:5432/unveilchem_db

# 阿里云OSS配置
export OSS_ACCESS_KEY=your-access-key
export OSS_SECRET_KEY=your-secret-key
export OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
export OSS_BUCKET=unveilchem

# 阿里云OCR配置
export ALIYUN_OCR_ACCESS_KEY=your-ocr-key
export ALIYUN_OCR_SECRET_KEY=your-ocr-secret

# JWT密钥
export SECRET_KEY=your-jwt-secret-key
EOF