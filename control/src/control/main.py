import control.req
from loguru import logger
import subprocess
import sys
from pathlib import Path


def stderr_filter_function(record):
    if record["name"] == "control.req" and record["level"].name == "DEBUG":
        return False
    return True


logger.remove(handler_id=None)
logger.add(
    sys.stderr,
    format="{time} {level: <5} {message}",
    level="DEBUG",
    filter=stderr_filter_function,
)


file_log = Path(__file__).parent / "control.log"
if file_log.exists():
    file_log.unlink()
logger.add(
    file_log,
    format="{time} {level: <5} {message}",
    level="DEBUG",
)


def format_results(results: list[control.req.ReqResult]):
    # errors_d = {}
    # for r in results:
    #     if not r.is_success:
    #         errors_d[r.result["msg"]] = errors_d.get(r.result["msg"], 0) + 1
    return {
        "total": len(results),
        "success": len([r for r in results if r.is_success]),
        "fail": len([r for r in results if not r.is_success]),
        "v1": len([r for r in results if r.result.get("version") == "1"]),
        "v2": len([r for r in results if r.result.get("version") == "2"]),
        "errors": [r.result for r in results if not r.is_success],
    }


async def case_fail():
    def deploy_app(version: str):
        # kubectl apply -f /workspace/control/assets/fail/v1.yaml
        subprocess.run(
            [
                "kubectl",
                "apply",
                "-f",
                f"/workspace/control/assets/fail/v{version}.yaml",
            ],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )

    u1 = control.req.ReqUser("user1")

    deploy_app("1")
    while True:
        result = await u1.send_get_req()
        if result.is_success and result.result.get("version") == "1":
            break
        logger.debug("waiting for v1 to be ready")
        await asyncio.sleep(5)

    await u1.start_send_get_req(tps=50)
    await asyncio.sleep(10)
    deploy_app("2")
    await asyncio.sleep(10)
    results = await u1.stop_and_get_results()
    print(format_results(results))


async def case_health():
    def deploy_app(version: str):
        logger.info(f"deploying v{version}")
        subprocess.run(
            [
                "kubectl",
                "apply",
                "-f",
                f"/workspace/control/assets/health/v{version}.yaml",
            ],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )

    def delete_app(version: str):
        logger.info(f"deleting v{version}")
        subprocess.run(
            [
                "kubectl",
                "delete",
                "-f",
                f"/workspace/control/assets/health/v{version}.yaml",
            ],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )

    u1 = control.req.ReqUser("user1")

    deploy_app("1")
    while True:
        result = await u1.send_get_req()
        if result.is_success and result.result.get("version") == "1":
            break
        logger.debug("waiting for v1 to be ready")
        await asyncio.sleep(5)

    await u1.start_send_get_req(tps=50)
    await asyncio.sleep(10)
    deploy_app("2")
    await asyncio.sleep(20)
    results = await u1.stop_and_get_results()
    logger.info(f'results = {format_results(results)}')
    delete_app("2")


async def main():
    # await case_fail()
    await case_health()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
