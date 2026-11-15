"""Independent agent worker; bounded calls never block the virtual clock."""
import asyncio
import logging
from uuid import uuid4
from .agents import claim_job, process_job


async def main():
    logging.basicConfig(level=logging.INFO)
    owner = 'agent-'+uuid4().hex
    while True:
        try:
            job_id = claim_job(owner)
            if job_id:
                await process_job(job_id, owner)
            else:
                await asyncio.sleep(1)
        except Exception:
            # The lease/checkpoint is durable. Do not log provider responses or credentials.
            logging.error('Agent step interrupted; lease recovery will inspect its saved call state.')
            await asyncio.sleep(2)


if __name__ == '__main__':
    asyncio.run(main())
