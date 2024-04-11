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

file_traefik_api = dir_logs / "traefik_api.log"
file_meta = dir_logs / "meta.json"


class kubeLogger:
    def __init__(self):
        self.pods_set = set()

        self.meta = {}

        self._clear()

    # clear previous logs
    def _clear(self):
        if dir_logs.exists():
            shutil.rmtree(dir_logs)
        dir_logs.mkdir()

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
                if "podIP" in pod["status"]:
                    pod_name = pod["metadata"]["name"]
                    ip = pod["status"]["podIP"]
                    image = pod["spec"]["containers"][0]["image"]

                    if image not in self.meta:
                        self.meta[image] = {}
                    self.meta[image][pod_name] = ip

            Path(file_meta).write_text(json.dumps(self.meta, indent=4))

            await asyncio.sleep(5)

    async def start_traefik_api(self):
        sess = await get_session()
        with open(file_traefik_api, "w") as f:
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

                # refresh as fast as possible
                # await asyncio.sleep(0.1)


class Event:
    def __init__(self, time: datetime.datetime, message: str):
        self.time = time
        self.message = message


class Analyzer:

    def _parse_traefik_api(self) -> list[Event]:

        events = []

        lines = file_traefik_api.read_text().splitlines()
        if not lines:
            return []

        def _parse_line(line: str) -> Event:
            time_str, message = line.split(" ", 1)
            time = datetime.datetime.fromisoformat(time_str)
            return Event(time, f"Traefik LoadBalancer change to: {message}")

        events.append(_parse_line(lines[0]))
        lines = lines[1:]
        for line in lines:
            if _parse_line(line).message != events[-1].message:
                events.append(_parse_line(line))

        return events

    def _parse_pod_logs(self) -> list[Event]:

        events = []

        for pod_log in dir_logs.glob("v*_*.log"):
            pod_name = pod_log.stem[3:]  # 3: to remove "v1_" or "v2_"
            lines = pod_log.read_text().splitlines()
            if not lines:
                continue

            def _is_access_log(line: str):
                return "GET" in line and "debug" not in line

            def _is_user_access_log(line: str):
                return _is_access_log(line) and "user" in line

            def _parse_access_log(line: str):
                start_index = line.index("[GIN] ") + len("[GIN] ")

                end_index = start_index + len("2024-04-11 14:08:06.230143")
                time_str = line[start_index:end_index]
                time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                return time

            for line in lines:
                if _is_access_log(line):
                    time = _parse_access_log(line)
                    events.append(Event(time, f"{pod_name} First Request"))
                    break
            for line in lines:
                if _is_user_access_log(line):
                    time = _parse_access_log(line)
                    events.append(Event(time, f"{pod_name} First User Request"))
                    break

            for line in reversed(lines):
                if _is_access_log(line):
                    time = _parse_access_log(line)
                    events.append(Event(time, f"{pod_name} Last User Request"))
                    break

        return events

    def execute(self):

        logger.debug("=== log analyze start ===")

        meta = file_meta.read_text()
        print(meta)

        class PodsMeta:
            def __init__(self, pod_name: str, ip: str, image: str):
                self.pod_name = pod_name
                self.ip = ip
                self.image = image

            def __repr__(self):
                return self.__str__()

            def __str__(self):
                return f"PodsMeta({self.pod_name}, {self.ip}, {self.image})"

        pods_meta: list[PodsMeta] = []
        for image in json.loads(meta):
            for pod_name, ip in json.loads(meta)[image].items():
                pods_meta.append(PodsMeta(pod_name, ip, image))

        events: list[Event] = []

        events.extend(self._parse_traefik_api())
        events.extend(self._parse_pod_logs())

        events.sort(key=lambda x: x.time)

        for event in events:
            print(f"{event.time} {event.message}")

        logger.debug("=== log analyze end ===")


def main():
    analyzer = Analyzer()
    analyzer.execute()


if __name__ == "__main__":
    main()
