import asyncio
import aiohttp
from loguru import logger
import atexit

session = None


async def get_session():
    global session
    if session is None:
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1))
    return session


async def close_session():
    global session
    if session is not None:
        await session.close()
        session = None


def close():
    asyncio.run(close_session())


atexit.register(close)


class ReqResult:
    def __init__(self, is_success: bool, result: dict):
        self.is_success = is_success
        self.result = result


class ReqUser:
    def __init__(self, name):
        self.name = name

        self.requesting = False
        self.results: list[ReqResult] = []

    async def send_get_req(self) -> ReqResult:
        try:
            async with (await get_session()).get(f"http://k3s") as resp:
                return ReqResult(True, await resp.json())
        except Exception as e:
            return ReqResult(False, {"req error": str(e)})

    async def _start_send_get_req(self, tps=1):
        logger.info(f"{self.name} started, tps={tps}")
        sleep_time = 1 / tps
        while self.requesting:
            self.results.append(await self.send_get_req())
            await asyncio.sleep(sleep_time)
        logger.info(f"{self.name} stopped")

    async def start_send_get_req(self, tps=1):
        self.requesting = True

        asyncio.create_task(self._start_send_get_req(tps))

    async def stop_and_get_results(self):
        self.requesting = False
        return self.results
