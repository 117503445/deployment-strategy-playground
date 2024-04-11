from pathlib import Path
import subprocess
import json
import shutil
import asyncio
from loguru import logger
import aiohttp
from control.req import get_session
import datetime

dir_logs = Path(__file__).parent / "logs"
if dir_logs.exists():
    shutil.rmtree(dir_logs)
dir_logs.mkdir()


class kubeLogger:
    def __init__(self):
        self.pods_set = set()

        self.meta = {}

    async def start_app_logs(self):
        while True:
            output = subprocess.run(
                ["kubectl", "get", "pods", "-l", "app=demo-app", "-o", "json"],
                check=True,
                stdout=subprocess.PIPE,
            )
            output = json.loads(output.stdout.decode())
            for pod in output["items"]:
                pod_name = pod["metadata"]["name"]

                if pod_name not in self.pods_set:
                    self.pods_set.add(pod_name)
                    pod_image = pod["spec"]["containers"][0]["image"]
                    v = "v1_" if "v1" in pod_image else "v2_"
                    file_log = dir_logs / f"{v}{pod_name}.log"

                    asyncio.create_task(self._collect_pod_name(pod_name, file_log))

            await asyncio.sleep(5)

    async def start_traefik_logs(self):
        # delete traefik pod
        logger.debug("deleting traefik pod to clear previous logs")
        subprocess.run(
            [
                "kubectl",
                "delete",
                "pod",
                "-l",
                "app.kubernetes.io/name=traefik",
                "--namespace",
                "kube-system",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # wait for traefik pod to be ready

        while True:
            try:
                logger.debug("waiting for traefik pod to be ready")
                pod_name = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        "pod",
                        "-l",
                        "app.kubernetes.io/name=traefik",
                        "--namespace",
                        "kube-system",
                        "-o",
                        "jsonpath={.items[0].metadata.name}",
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                ).stdout.decode()
                break
            except Exception as e:
                await asyncio.sleep(3)
        logger.debug(f"traefik pod name = {pod_name}")

        file_log = dir_logs / f"traefik_stdout.log"
        asyncio.create_task(self._collect_pod_name(pod_name, file_log, "kube-system"))

    async def _wait_for_pod_ready(self, pod_name: str, namespace: str = "default"):
        while True:
            out = await asyncio.create_subprocess_exec(
                "kubectl",
                "get",
                "pod",
                pod_name,
                "-n",
                namespace,
                "-o",
                "json",
                stdout=subprocess.PIPE,
            )
            out = await out.communicate()
            try:
                out = json.loads(out[0].decode())
                if out["status"]["phase"] == "Running":
                    break
            except Exception as e:
                pass

            await asyncio.sleep(1)

    async def _collect_pod_name(
        self, pod_name: str, file_log: Path, namespace: str = "default"
    ):
        await self._wait_for_pod_ready(pod_name, namespace)

        logger.info(f"collecting logs for {pod_name} to {file_log}")

        args = ["kubectl", "logs", pod_name]
        if namespace:
            args.extend(["--namespace", namespace])
        args.extend(["-f"])

        subprocess.Popen(
            args,
            stdout=file_log.open("w"),
        )

    async def start_meta(self):
        while True:
            output = subprocess.run(
                ["kubectl", "get", "pods", "-l", "app=demo-app", "-o", "json"],
                check=True,
                stdout=subprocess.PIPE,
            )
            output = json.loads(output.stdout.decode())
            for pod in output["items"]:
                pod_name = pod["metadata"]["name"]
                if pod_name not in self.meta:
                    # pod may not have IP yet
                    if "podIP" in pod["status"]:
                        self.meta[pod_name] = {
                            "ip": pod["status"]["podIP"],
                            "image": pod["spec"]["containers"][0]["image"],
                        }

            Path(dir_logs / "meta.json").write_text(json.dumps(self.meta, indent=4))

            await asyncio.sleep(5)

    async def start_traefik_api(self):
        sess = await get_session()
        with open(dir_logs / "traefik_api.log", "w") as f:
            while True:
                try:
                    async with sess.get(
                        f"http://k3s:80/api/http/services",
                        headers={"Host": "a.example"},
                        ssl=False,
                    ) as resp:
                        js = await resp.json()
                        for service in js:
                            if service["name"] == "default-demo-app-8080@kubernetes":
                                text = f'{datetime.datetime.now().isoformat()} {json.dumps(service["loadBalancer"])}\n'
                                f.write(text)
                                f.flush()
                except Exception as e:
                    pass

                await asyncio.sleep(0.1)
