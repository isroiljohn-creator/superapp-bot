import asyncio
from arq.worker import create_worker
from taskqueue.worker import WorkerSettings

async def main():
    worker = create_worker(WorkerSettings)
    await worker.async_run()

if __name__ == '__main__':
    asyncio.run(main())
