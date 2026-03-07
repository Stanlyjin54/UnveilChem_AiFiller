# 解析器运行指南

## 方法1: 运行Camelot表格解析器 (独立模块)

### 直接运行
```bash
cd d:\UnveilChem_AI_DocAnalyzer
python -c "
from parsers.camelot_parser import CamelotTableParser
import logging
logging.basicConfig(level=logging.INFO)

# 初始化解析器
parser = CamelotTableParser()

# 提取PDF表格
pdf_path = 'your_document.pdf'
tables = parser.extract_tables(pdf_path)

# 输出结果
for i, table in enumerate(tables):
    print(f'表格 {i+1}:')
    print(f'置信度: {table.confidence:.2f}')
    print(f'数据形状: {table.data.shape}')
    print(f'数据预览:')
    print(table.data.head())
    print('---')
```

### 批量提取
```bash
python -c "
from parsers.camelot_parser import CamelotTableParser
parser = CamelotTableParser()
pdf_files = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
results = parser.extract_tables_batch(pdf_files, max_workers=2)
for file_path, tables in results.items():
    print(f'{file_path}: 提取到 {len(tables)} 个表格')
"
```

## 方法2: 运行Backend PDF解析器 (API服务)

### 启动后端服务
```bash
cd d:\UnveilChem_AI_DocAnalyzer\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 通过API调用
```python
import requests
import json

# 上传PDF文件进行解析
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/v1/parse', files=files)
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 方法3: 使用统一解析器 (推荐)

### 集成所有解析引擎
```bash
python -c "
from parsers.unified_parser import UnifiedDocumentParser
parser = UnifiedDocumentParser()

# 自动选择最佳解析器
result = parser.parse_document('document.pdf')
print(f'使用的解析器: {result.parser_used}')
print(f'解析状态: {result.success}')
print(f'提取内容长度: {len(result.text_content)}')
print(f'表格数量: {len(result.tables)}')
print(f'参数数量: {len(result.parameters)}')
"
```

## 方法4: GUI应用程序

### 运行图形界面
```bash
# 方式1: 简单GUI
python simple_gui_app.py

# 方式2: 高级GUI
python advanced_gui_app.py
```

## 依赖安装

### 确保安装核心依赖
```bash
pip install -r requirements.txt
```

### 特殊依赖安装
```bash
# Camelot依赖
pip install camelot-py[cv]

# 或者使用conda (推荐)
conda install -c conda-forge ghostscript
pip install camelot-py

# OCR依赖
pip install pytesseract
# 还需要安装Tesseract OCR软件
```

## 性能对比

| 解析器类型 | 优势 | 适用场景 | 准确率 |
|-----------|------|----------|--------|
| Camelot表格解析器 | 表格提取精度高 | 专门处理PDF表格 | ≥99.02% |
| Backend PDF解析器 | 文本+OCR全面 | 综合文档解析 | 90-95% |
| 统一解析器 | 智能路由选择 | 复杂混合文档 | 自适应 |
| GUI应用 | 易于使用 | 手动操作 | 依赖选择 |

## 错误排查

### 常见问题
1. **Camelot导入失败**: 安装Ghostscript
2. **OCR不工作**: 安装Tesseract软件
3. **依赖冲突**: 使用虚拟环境
4. **内存不足**: 调整batch_size参数

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 运行解析器
parser = CamelotTableParser()
tables = parser.extract_tables('document.pdf')
```