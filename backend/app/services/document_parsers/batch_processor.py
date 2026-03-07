#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量文档处理系统

支持多文件并行解析、进度跟踪和结果汇总
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json

from . import BaseDocumentParser, ParserError
from .parser_manager import DocumentParserManager

logger = logging.getLogger(__name__)

class BatchProcessor:
    """批量文档处理器"""
    
    def __init__(self, parser_manager: DocumentParserManager, max_workers: int = 4):
        self.parser_manager = parser_manager
        self.max_workers = max_workers
        self.progress_callbacks: List[Callable] = []
        self.batch_history: List[Dict[str, Any]] = []
    
    def add_progress_callback(self, callback: Callable):
        """添加进度回调函数"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, progress_data: Dict[str, Any]):
        """通知进度更新"""
        for callback in self.progress_callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")
    
    async def process_batch_async(self, file_paths: List[str], 
                                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """异步批量处理文档"""
        if progress_callback:
            self.add_progress_callback(progress_callback)
        
        batch_id = f"batch_{int(time.time())}"
        start_time = time.time()
        
        # 准备任务
        tasks = []
        for i, file_path in enumerate(file_paths):
            task = {
                "task_id": f"{batch_id}_task_{i+1}",
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "status": "pending",
                "progress": 0
            }
            tasks.append(task)
        
        # 通知开始
        self._notify_progress({
            "batch_id": batch_id,
            "status": "started",
            "total_files": len(tasks),
            "completed": 0,
            "failed": 0,
            "start_time": start_time
        })
        
        # 创建异步任务
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single_file(task: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self._process_single_file_async(task)
        
        # 执行所有任务
        results = await asyncio.gather(*[process_single_file(task) for task in tasks], 
                                     return_exceptions=True)
        
        # 处理结果
        completed_results = []
        failed_count = 0
        completed_count = 0
        
        for i, result in enumerate(results):
            task = tasks[i]
            if isinstance(result, Exception):
                task["status"] = "failed"
                task["error"] = str(result)
                failed_count += 1
            else:
                task["status"] = "completed"
                task["result"] = result
                completed_count += 1
                completed_results.append(result)
            
            # 通知进度
            self._notify_progress({
                "batch_id": batch_id,
                "current_task": i + 1,
                "total_tasks": len(tasks),
                "completed": completed_count,
                "failed": failed_count,
                "status": task["status"]
            })
        
        # 汇总结果
        batch_result = {
            "batch_id": batch_id,
            "status": "completed" if failed_count == 0 else "completed_with_errors",
            "total_files": len(file_paths),
            "completed_files": completed_count,
            "failed_files": failed_count,
            "processing_time": time.time() - start_time,
            "start_time": start_time,
            "end_time": time.time(),
            "results": completed_results,
            "failed_files": [task for task in tasks if task["status"] == "failed"],
            "statistics": self._generate_batch_statistics(completed_results)
        }
        
        # 保存到历史记录
        self.batch_history.append(batch_result)
        
        # 通知完成
        self._notify_progress({
            "batch_id": batch_id,
            "status": "completed",
            "result": batch_result
        })
        
        return batch_result
    
    async def _process_single_file_async(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """异步处理单个文件"""
        file_path = task["file_path"]
        task["status"] = "processing"
        task["progress"] = 10
        
        try:
            # 验证文件
            validation_result = self.parser_manager.validate_file_before_parse(file_path)
            if not validation_result[0]:
                raise ParserError(f"文件验证失败: {validation_result[1]}")
            
            task["progress"] = 30
            
            # 获取合适的解析器
            parser = self.parser_manager.find_suitable_parser(file_path)
            if not parser:
                raise ParserError("未找到合适的解析器")
            
            task["progress"] = 50
            
            # 解析文档
            result = parser.parse(file_path)
            task["progress"] = 80
            
            # 添加任务信息
            result["task_info"] = {
                "task_id": task["task_id"],
                "file_name": task["file_name"],
                "processing_time": time.time(),
                "parser_used": parser.parser_name
            }
            
            task["progress"] = 100
            task["status"] = "completed"
            
            return result
            
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            raise
    
    def process_batch_sync(self, file_paths: List[str], 
                          progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """同步批量处理文档"""
        if progress_callback:
            self.add_progress_callback(progress_callback)
        
        batch_id = f"sync_batch_{int(time.time())}"
        start_time = time.time()
        
        # 准备任务
        tasks = []
        for i, file_path in enumerate(file_paths):
            task = {
                "task_id": f"{batch_id}_task_{i+1}",
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "status": "pending",
                "progress": 0
            }
            tasks.append(task)
        
        # 通知开始
        self._notify_progress({
            "batch_id": batch_id,
            "status": "started",
            "total_files": len(tasks),
            "completed": 0,
            "failed": 0,
            "start_time": start_time
        })
        
        # 使用线程池进行并行处理
        results = []
        failed_count = 0
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self._process_single_file_sync, task): task 
                for task in tasks
            }
            
            # 收集结果
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    task["status"] = "completed"
                    task["result"] = result
                    results.append(result)
                    completed_count += 1
                except Exception as e:
                    task["status"] = "failed"
                    task["error"] = str(e)
                    failed_count += 1
                
                # 通知进度
                self._notify_progress({
                    "batch_id": batch_id,
                    "completed": completed_count,
                    "failed": failed_count,
                    "total": len(tasks),
                    "status": task["status"]
                })
        
        # 汇总结果
        batch_result = {
            "batch_id": batch_id,
            "status": "completed" if failed_count == 0 else "completed_with_errors",
            "total_files": len(file_paths),
            "completed_files": completed_count,
            "failed_files": failed_count,
            "processing_time": time.time() - start_time,
            "start_time": start_time,
            "end_time": time.time(),
            "results": results,
            "failed_files": [task for task in tasks if task["status"] == "failed"],
            "statistics": self._generate_batch_statistics(results)
        }
        
        # 保存到历史记录
        self.batch_history.append(batch_result)
        
        return batch_result
    
    def _process_single_file_sync(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """同步处理单个文件"""
        file_path = task["file_path"]
        task["status"] = "processing"
        task["progress"] = 10
        
        try:
            # 验证文件
            validation_result = self.parser_manager.validate_file_before_parse(file_path)
            if not validation_result[0]:
                raise ParserError(f"文件验证失败: {validation_result[1]}")
            
            task["progress"] = 30
            
            # 获取合适的解析器
            parser = self.parser_manager.find_suitable_parser(file_path)
            if not parser:
                raise ParserError("未找到合适的解析器")
            
            task["progress"] = 50
            
            # 解析文档
            result = parser.parse(file_path)
            task["progress"] = 80
            
            # 添加任务信息
            result["task_info"] = {
                "task_id": task["task_id"],
                "file_name": task["file_name"],
                "processing_time": time.time(),
                "parser_used": parser.parser_name
            }
            
            task["progress"] = 100
            task["status"] = "completed"
            
            return result
            
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            raise
    
    def _generate_batch_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成批量处理统计信息"""
        if not results:
            return {}
        
        statistics = {
            "total_files": len(results),
            "file_types": {},
            "parsers_used": {},
            "total_parameters_found": 0,
            "total_entities_found": 0,
            "average_parse_time": 0.0,
            "success_rate": 1.0
        }
        
        total_time = 0
        total_params = 0
        total_entities = 0
        
        for result in results:
            if "error" in result:
                continue
            
            # 文件类型统计
            file_ext = Path(result.get("file_path", "")).suffix.lower()
            statistics["file_types"][file_ext] = statistics["file_types"].get(file_ext, 0) + 1
            
            # 解析器使用统计
            parser_name = result.get("parser_used", "Unknown")
            statistics["parsers_used"][parser_name] = statistics["parsers_used"].get(parser_name, 0) + 1
            
            # 解析时间统计
            parse_time = result.get("parse_time", 0)
            total_time += parse_time
            
            # 参数统计
            parameters = result.get("parameters", {})
            total_params += len(parameters) if isinstance(parameters, dict) else 0
            
            # 实体统计
            entities = result.get("chemical_entities", [])
            total_entities += len(entities) if isinstance(entities, list) else 0
        
        # 计算平均值
        if results:
            statistics["average_parse_time"] = total_time / len(results)
            statistics["total_parameters_found"] = total_params
            statistics["total_entities_found"] = total_entities
        
        return statistics
    
    def get_batch_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取批量处理历史记录"""
        return self.batch_history[-limit:] if self.batch_history else []
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.batch_history:
            return {"message": "暂无批量处理记录"}
        
        total_batches = len(self.batch_history)
        total_files = sum(batch["total_files"] for batch in self.batch_history)
        total_time = sum(batch["processing_time"] for batch in self.batch_history)
        
        return {
            "total_batches": total_batches,
            "total_files_processed": total_files,
            "total_processing_time": total_time,
            "average_batch_size": total_files / total_batches if total_batches > 0 else 0,
            "average_batch_time": total_time / total_batches if total_batches > 0 else 0,
            "average_files_per_second": total_files / total_time if total_time > 0 else 0,
            "success_rate": sum(1 for batch in self.batch_history if batch["status"] == "completed") / total_batches if total_batches > 0 else 0
        }

class ResultPreview:
    """结果预览生成器"""
    
    def __init__(self):
        self.preview_cache = {}
    
    def generate_preview(self, parse_result: Dict[str, Any], max_length: int = 500) -> Dict[str, Any]:
        """生成解析结果预览"""
        if "error" in parse_result:
            return {
                "type": "error",
                "message": parse_result["error"],
                "file_path": parse_result.get("file_path", ""),
                "preview_time": time.time()
            }
        
        preview = {
            "type": "success",
            "file_path": parse_result.get("file_path", ""),
            "file_name": Path(parse_result.get("file_path", "")).name,
            "parser_used": parse_result.get("parser_used", ""),
            "preview_time": time.time()
        }
        
        # 文本内容预览
        text_content = parse_result.get("text_content", "")
        if text_content:
            preview["text_preview"] = text_content[:max_length] + ("..." if len(text_content) > max_length else "")
            preview["has_full_text"] = len(text_content) > max_length
            preview["word_count"] = len(text_content.split())
        
        # 参数预览
        parameters = parse_result.get("parameters", {})
        if isinstance(parameters, dict) and parameters:
            preview["parameters_summary"] = {
                "total_count": len(parameters),
                "types": list(parameters.keys()),
                "sample": {}
            }
            
            # 添加示例参数
            for param_type, param_data in list(parameters.items())[:3]:
                if isinstance(param_data, list) and param_data:
                    preview["parameters_summary"]["sample"][param_type] = param_data[0]
                elif isinstance(param_data, dict) and "values" in param_data:
                    preview["parameters_summary"]["sample"][param_type] = {
                        "values": param_data["values"][:2] if param_data.get("values") else [],
                        "unit": param_data.get("unit", "")
                    }
        
        # 表格预览
        tables = parse_result.get("tables", [])
        if tables:
            preview["tables_summary"] = {
                "total_count": len(tables),
                "sample_table": tables[0] if tables else None
            }
        
        # 图像预览
        images = parse_result.get("images", [])
        if images:
            preview["images_summary"] = {
                "total_count": len(images),
                "sample_image": images[0] if images else None
            }
        
        # 实体预览
        entities = parse_result.get("chemical_entities", [])
        if entities:
            preview["entities_summary"] = {
                "total_count": len(entities),
                "types": list(set(entity.get("type", "") for entity in entities)),
                "sample": entities[:3]
            }
        
        # 解析时间信息
        parse_time = parse_result.get("parse_time", 0)
        if parse_time:
            preview["performance"] = {
                "parse_time": parse_time,
                "parsing_speed": "fast" if parse_time < 1 else "medium" if parse_time < 5 else "slow"
            }
        
        return preview
    
    def save_preview_cache(self, result: Dict[str, Any], cache_key: str):
        """保存预览到缓存"""
        self.preview_cache[cache_key] = self.generate_preview(result)
    
    def get_cached_preview(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的预览"""
        return self.preview_cache.get(cache_key)
    
    def clear_cache(self):
        """清理预览缓存"""
        self.preview_cache.clear()