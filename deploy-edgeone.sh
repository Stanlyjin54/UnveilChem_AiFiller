#!/bin/bash

# UnveilChem_AiFiller EdgeOne前端部署脚本
# 使用方法: ./deploy-edgeone.sh

set -e

echo "🚀 开始部署UnveilChem前端到EdgeOne Pages..."

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm未安装，请先安装npm"
    exit 1
fi

# 进入前端目录
cd frontend

echo "📦 安装依赖..."
npm install

echo "🔨 构建前端应用..."
npm run build

# 检查构建是否成功
if [ ! -d "dist" ]; then
    echo "❌ 构建失败，dist目录不存在"
    exit 1
fi

echo "✅ 前端构建完成"

# 检查EdgeOne CLI是否安装
if ! command -v edgeone &> /dev/null; then
    echo "📥 安装EdgeOne CLI..."
    npm install -g @edgeone/cli
fi

# 检查环境变量
if [ -z "$EDGEONE_TOKEN" ]; then
    echo "⚠️  环境变量EDGEONE_TOKEN未设置"
    echo "请设置EdgeOne访问令牌:"
    echo "export EDGEONE_TOKEN=your-token-here"
    exit 1
fi

if [ -z "$EDGEONE_PROJECT" ]; then
    EDGEONE_PROJECT="unveilchem"
    echo "ℹ️  使用默认项目名: $EDGEONE_PROJECT"
fi

echo "🚀 部署到EdgeOne Pages..."
edgeone pages deploy \
    --project "$EDGEONE_PROJECT" \
    --token "$EDGEONE_TOKEN" \
    --dir ./dist

echo "✅ 部署完成!"

# 配置自定义域名（如果提供）
if [ -n "$CUSTOM_DOMAIN" ]; then
    echo "🌐 配置自定义域名: $CUSTOM_DOMAIN"
    edgeone pages domain add \
        --project "$EDGEONE_PROJECT" \
        --domain "$CUSTOM_DOMAIN" \
        --token "$EDGEONE_TOKEN"
    echo "✅ 域名配置完成"
fi

echo ""
echo "🎉 UnveilChem前端部署成功!"
echo "📊 访问地址: https://$EDGEONE_PROJECT.edgeone.app"
if [ -n "$CUSTOM_DOMAIN" ]; then
    echo "🌐 自定义域名: https://$CUSTOM_DOMAIN"
fi
echo ""
echo "💡 后续操作:"
echo "1. 检查DNS解析是否生效"
echo "2. 测试API接口连通性"
echo "3. 配置SSL证书"
echo ""

# 健康检查
echo "🔍 执行健康检查..."
if command -v curl &> /dev/null; then
    if [ -n "$CUSTOM_DOMAIN" ]; then
        HEALTH_URL="https://$CUSTOM_DOMAIN"
    else
        HEALTH_URL="https://$EDGEONE_PROJECT.edgeone.app"
    fi
    
    if curl -s -f "$HEALTH_URL" > /dev/null; then
        echo "✅ 健康检查通过"
    else
        echo "⚠️  健康检查失败，请手动验证"
    fi
fi