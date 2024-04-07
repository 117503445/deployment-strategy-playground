import subprocess

def build_image(ver: str):
    # docker build --build-arg VER=1 -t 117503445/demo-app:v1 /workspace/app
    subprocess.run(['docker', 'build', '--build-arg', f'VER={ver}', '-t', f'117503445/demo-app:v{ver}', '/workspace/app'], check=True)

def main():
    build_image('1')
    build_image('2')
    # docker run --rm -p 18080:8080 117503445/demo-app:v1
    print('main')


if __name__ == '__main__':
    main()