import asyncio
import aiohttp
from loguru import logger
import atexit
import json

session: aiohttp.ClientSession | None = None


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

        self.created_at = asyncio.get_event_loop().time()

    def __str__(self):
        return f"[{self.is_success}, {self.result}]"

    def __repr__(self):
        return str(self)


class ReqUser:
    def __init__(self, name):
        self.name = name

        self.requesting = False
        self.results: list[ReqResult] = []

    async def send_get_req(self) -> ReqResult:
        try:
            sess = await get_session()
            async with sess.get(f"http://k3s") as resp:
                text = await resp.text()
                try:
                    resp_d = json.loads(text)
                    return ReqResult(True, resp_d)
                except Exception as e:
                    return ReqResult(
                        False,
                        {
                            "msg": "json error",
                            "ex": str(e),
                            "text": text,
                            "status": resp.status,
                        },
                    )
        except Exception as e:
            return ReqResult(False, {"msg": "req error", "ex": str(e)})

    async def _send_get_req(self):
        result = await self.send_get_req()
        logger.debug(f"{self.name} result: {result}")

        self.results.append(result)

    async def _start_send_get_req(self, tps=1):
        logger.info(f"{self.name} started, tps={tps}")
        sleep_time = 1 / tps
        while self.requesting:
            start = asyncio.get_event_loop().time()
            asyncio.create_task(self._send_get_req())
            end = asyncio.get_event_loop().time()

            if end - start < sleep_time:
                await asyncio.sleep(sleep_time - (end - start))
            else:
                logger.warning(
                    f"{self.name} is too slow, start = {start}, end = {end}, start - end = {start - end} < sleep_time = {sleep_time}"
                )

        logger.info(f"{self.name} stopped")

    async def start_send_get_req(self, tps=1):
        self.requesting = True

        asyncio.create_task(self._start_send_get_req(tps))

    async def stop_and_get_results(self):
        self.requesting = False
        return self.results
