import control.req
from loguru import logger
import subprocess
import sys

logger.remove(handler_id=None)
logger.add(
    sys.stderr,
    format="{time} {level: <5} {message}",
    level="DEBUG",
)


def build_image():
    for ver in ["1", "2"]:
        # docker build --build-arg VER=1 -t 117503445/demo-app:v1 /workspace/app
        subprocess.run(
            [
                "docker",
                "build",
                "--build-arg",
                f"VER={ver}",
                "-t",
                f"117503445/demo-app:v{ver}",
                "/workspace/app",
            ],
            check=True,
        )

        # docker push 117503445/demo-app:v1
        subprocess.run(["docker", "push", f"117503445/demo-app:v{ver}"], check=True)


def format_results(results: list[control.req.ReqResult]):
    errors_d = {}
    for r in results:
        if not r.is_success:
            errors_d[r.result["req error"]] = errors_d.get(r.result["req error"], 0) + 1
    return {
        "total": len(results),
        "success": len([r for r in results if r.is_success]),
        "fail": len([r for r in results if not r.is_success]),
        "v1": len([r for r in results if r.result.get("version") == "1"]),
        "v2": len([r for r in results if r.result.get("version") == "2"]),
        "errors": errors_d,
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


async def main():
    await case_fail()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
