import asyncio
from collections import defaultdict
from typing import Callable, Optional
from checkers.kz_checker import check_arrest_file
import logging
from checkers.arrest_batch_runner import run_arrest_check_in_chunks
check_queue = asyncio.Queue()
currently_checking = defaultdict(lambda: False)
progress_tracker = defaultdict(lambda: {"total": 0, "done": 0})

async def arrest_worker():
    while True:
        user_id, input_path, output_path, callback = await check_queue.get()
        currently_checking[user_id] = True
        try:
            success, path_arrest, path_clean, skipped_count = await asyncio.to_thread(
                run_arrest_check_in_chunks, user_id, input_path, output_path, progress_tracker
            )

            if success and callable(callback):
                await callback(user_id, path_arrest, path_clean, skipped_count=skipped_count)

        except Exception as e:
            logging.exception(f"Ошибка при обработке для пользователя {user_id}")
            if callable(callback):
                await callback(user_id, None, None, error=str(e))
        finally:
            currently_checking[user_id] = False
            check_queue.task_done()
async def enqueue_check(
    user_id: int,
    input_path: str,
    output_path: str,
    callback: Callable[[int, Optional[str], Optional[str], Optional[int]], None]
):    
    if currently_checking[user_id]:
        return False, "processing"
    await check_queue.put((user_id, input_path, output_path, callback))
    queue_size = check_queue.qsize()
    return True, "queued" if queue_size > 0 else "immediate"

async def start_arrest_checker_worker():
    asyncio.create_task(arrest_worker())
