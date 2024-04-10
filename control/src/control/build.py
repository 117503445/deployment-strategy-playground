import subprocess
from pathlib import Path
import datetime

def build_image():
    for ver in ["1", "2"]:
        Path('/workspace/app/build.txt').write_text(f"Build version {ver} at {datetime.datetime.now().isoformat()}")
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

def main():
    build_image()


if __name__ == '__main__':
    main()