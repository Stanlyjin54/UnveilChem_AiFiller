#!/bin/bash

# UnveilChem_AiFiller 数据库迁移脚本
# 从SQLite迁移到PostgreSQL

set -e

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

# 检查环境变量
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ]; then
    log_error "请设置PostgreSQL连接信息:"
    echo "export POSTGRES_HOST=your-rds-host"
    echo "export POSTGRES_DB=unveilchem"
    echo "export POSTGRES_USER=unveilchem_user"
    echo "export POSTGRES_PASSWORD=your-password"
    exit 1
fi

log_info "🚀 开始数据库迁移 (SQLite → PostgreSQL)..."

# 检查SQLite数据库文件
SQLITE_DB="backend/database.db"
if [ ! -f "$SQLITE_DB" ]; then
    log_error "SQLite数据库文件不存在: $SQLITE_DB"
    exit 1
fi

# 检查PostgreSQL连接
log_info "🔗 检查PostgreSQL连接..."
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; then
    log_error "PostgreSQL连接失败"
    exit 1
fi

# 创建数据库表结构
log_info "📊 创建PostgreSQL表结构..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS '用户信息表';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.password_hash IS '密码哈希值';
COMMENT ON COLUMN users.role IS '用户角色: admin/user';

-- 文档解析记录表
CREATE TABLE IF NOT EXISTS document_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    file_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    ocr_text TEXT,
    chemical_data JSONB,
    analysis_result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

COMMENT ON TABLE document_records IS '文档解析记录表';
COMMENT ON COLUMN document_records.filename IS '文件名';
COMMENT ON COLUMN document_records.file_path IS '文件存储路径';
COMMENT ON COLUMN document_records.status IS '处理状态: pending/processing/completed/failed';
COMMENT ON COLUMN document_records.chemical_data IS '化学数据提取结果';

-- 化学参数配置表
CREATE TABLE IF NOT EXISTS chemical_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    config_name VARCHAR(100) NOT NULL,
    config_data JSONB NOT NULL,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chemical_configs IS '化学参数配置表';
COMMENT ON COLUMN chemical_configs.config_name IS '配置名称';
COMMENT ON COLUMN chemical_configs.config_data IS '配置数据(JSON格式)';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_document_records_user_id ON document_records(user_id);
CREATE INDEX IF NOT EXISTS idx_document_records_status ON document_records(status);
CREATE INDEX IF NOT EXISTS idx_chemical_configs_user_id ON chemical_configs(user_id);

EOF

log_info "✅ 表结构创建完成"

# 检查是否需要数据迁移
read -p "是否迁移现有数据? (y/N): " MIGRATE_DATA
if [[ "$MIGRATE_DATA" =~ ^[Yy]$ ]]; then
    log_info "📥 开始数据迁移..."
    
    # 安装迁移工具
    if ! command -v sqlite3 &> /dev/null; then
        log_info "📦 安装sqlite3工具..."
        sudo apt install -y sqlite3 || sudo yum install -y sqlite
    fi
    
    # 创建临时迁移脚本
    cat > /tmp/migrate_data.py << 'EOF'
import sqlite3
import psycopg2
import json
import sys
from datetime import datetime

# 连接SQLite数据库
sqlite_conn = sqlite3.connect('backend/database.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接PostgreSQL
try:
    pg_conn = psycopg2.connect(
        host=sys.argv[1],
        database=sys.argv[2],
        user=sys.argv[3],
        password=sys.argv[4]
    )
    pg_cursor = pg_conn.cursor()
    
    # 迁移用户数据
    sqlite_cursor.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    for user in users:
        pg_cursor.execute("""
            INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, user)
    
    # 迁移文档记录
    sqlite_cursor.execute("SELECT * FROM document_records")
    records = sqlite_cursor.fetchall()
    
    for record in records:
        pg_cursor.execute("""
            INSERT INTO document_records 
            (id, user_id, filename, file_path, file_size, file_type, status, 
             ocr_text, chemical_data, analysis_result, error_message, created_at, processed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, record)
    
    # 迁移配置数据
    sqlite_cursor.execute("SELECT * FROM chemical_configs")
    configs = sqlite_cursor.fetchall()
    
    for config in configs:
        pg_cursor.execute("""
            INSERT INTO chemical_configs 
            (id, user_id, config_name, config_data, is_default, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, config)
    
    pg_conn.commit()
    print("数据迁移完成")
    
except Exception as e:
    print(f"迁移失败: {e}")
    sys.exit(1)
    
finally:
    sqlite_conn.close()
    if 'pg_conn' in locals():
        pg_conn.close()
EOF
    
    # 执行数据迁移
    python3 /tmp/migrate_data.py "$POSTGRES_HOST" "$POSTGRES_DB" "$POSTGRES_USER" "$POSTGRES_PASSWORD"
    
    log_info "✅ 数据迁移完成"
else
    log_info "ℹ️  跳过数据迁移"
fi

# 更新应用配置
log_info "⚙️  更新应用数据库配置..."

# 创建生产环境配置文件
cat > backend/.env.production << EOF
# 数据库配置
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:5432/$POSTGRES_DB

# 应用配置
DEBUG=false
SECRET_KEY=your-production-secret-key-change-this

# 阿里云服务配置
OSS_ACCESS_KEY=your-oss-access-key
OSS_SECRET_KEY=your-oss-secret-key
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET=unveilchem

ALIYUN_OCR_ACCESS_KEY=your-ocr-access-key
ALIYUN_OCR_SECRET_KEY=your-ocr-secret-key
ALIYUN_OCR_REGION=cn-hangzhou

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS配置
CORS_ORIGINS=https://unveilchem.edgeone.app,https://www.unveilchem.com
EOF

log_info ""
log_info "🎉 数据库迁移完成!"
log_info "📊 PostgreSQL连接信息:"
log_info "   主机: $POSTGRES_HOST"
log_info "   数据库: $POSTGRES_DB"
log_info "   用户: $POSTGRES_USER"
log_info ""
log_info "💡 后续操作:"
log_info "1. 验证数据库连接"
log_info "2. 测试应用功能"
log_info "3. 配置数据库备份"
log_info "4. 监控数据库性能"
log_info ""

# 验证迁移结果
log_info "🔍 验证迁移结果..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    (SELECT COUNT(*) FROM users) as users_count,
    (SELECT COUNT(*) FROM document_records) as records_count,
    (SELECT COUNT(*) FROM chemical_configs) as configs_count;
"