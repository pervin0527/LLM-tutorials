import psutil
import asyncio
import logging


from datetime import datetime
from typing import Dict, Any, Callable, Tuple

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue = asyncio.Queue()
        self.is_processing = False
        self.memory_threshold = 0.8  # 80%
        self.max_concurrent_tasks = 2
        self.current_tasks = 0
        logger.info("TaskManager initialized with queue system")

    async def create_task(self, company_name: str) -> str:
        import uuid
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            "company_name": company_name,
            "eda_status": "pending",
            "created_at": datetime.utcnow(),
            "queue_position": self.task_queue.qsize() + 1
        }
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return self.tasks.get(task_id)

    def adjust_resource_thresholds(self):
        memory = psutil.virtual_memory()
        memory_usage = memory.percent / 100
        if memory_usage > self.memory_threshold:
            self.max_concurrent_tasks = max(1, self.max_concurrent_tasks - 1)
        else:
            self.max_concurrent_tasks = min(5, self.max_concurrent_tasks + 1)
        logger.info(f"리소스 임계값 조정: memory_threshold={self.memory_threshold}, max_concurrent_tasks={self.max_concurrent_tasks}")

    async def add_task_to_queue(self, task_id: str, crawling_function: Callable, **kwargs):
        if not callable(crawling_function):
            raise ValueError(f"crawling_function must be callable, got {type(crawling_function)}")
        while True:
            try:
                self.tasks[task_id].update({
                    "function": crawling_function,
                    "kwargs": kwargs
                })
                await self.task_queue.put((task_id, crawling_function, kwargs))
                break
            except Exception as e:
                logger.error(f"Task {task_id} 큐 등록 실패: {str(e)}, 재시도 중...")
                await asyncio.sleep(1)
        if not self.is_processing:
            asyncio.create_task(self.process_queue())

    async def execute_task(self, task_id: str, crawling_function: Callable, kwargs: Dict[str, Any]) -> None:
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                self.tasks[task_id]["started_at"] = datetime.utcnow()
                self.tasks[task_id]["eda_status"] = "processing"
                result = await crawling_function(task_id=task_id, **kwargs)
                self.tasks[task_id]["completed_at"] = datetime.utcnow()
                self.tasks[task_id]["eda_status"] = "completed"
                self.tasks[task_id]["result"] = result
                return
            except Exception as e:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"Task execution failed: {str(e)}, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
        logger.error(f"Task failed after {max_retries} attempts: {str(e)}")
        self.tasks[task_id]["eda_status"] = "failed"
        self.tasks[task_id]["error"] = str(e)
        logger.error(f"Task {task_id} failed: {str(e)}")

    async def process_queue(self):
        self.is_processing = True
        while True:
            try:
                self.adjust_resource_thresholds()
                if self.current_tasks >= self.max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue
                task_id, crawling_function, kwargs = await self.task_queue.get()
                self.current_tasks += 1
                try:
                    await self.execute_task(task_id, crawling_function, kwargs)
                finally:
                    self.current_tasks -= 1
                    self.task_queue.task_done()
                if self.task_queue.empty() and self.current_tasks == 0:
                    self.is_processing = False
                    break
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(1)