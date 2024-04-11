import subprocess
from pathlib import Path
import datetime


def build_image():
    file_build = Path("/workspace/app/build.txt")
    for ver in ["1", "2"]:
        file_build.write_text(
            f"Build version {ver} at {datetime.datetime.now().isoformat()}"
        )
        # docker exec -it dind docker build --build-arg VER=1 -t registry:5000/117503445/demo-app:v1 /workspace/app
        subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                "dind",
                "docker",
                "build",
                "--build-arg",
                f"VER={ver}",
                "-t",
                f"registry:5000/117503445/demo-app:v{ver}",
                "/workspace/app",
            ]
        )

        # docker exec -it dind docker push registry:5000/117503445/demo-app:v1
        subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                "dind",
                "docker",
                "push",
                f"registry:5000/117503445/demo-app:v{ver}",
            ],
            check=True,
        )
    file_build.unlink()


def main():
    build_image()


if __name__ == "__main__":
    main()
