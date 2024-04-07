import subprocess

def build_image():
    for ver in ['1', '2']:
        # docker build --build-arg VER=1 -t 117503445/demo-app:v1 /workspace/app
        subprocess.run(['docker', 'build', '--build-arg', f'VER={ver}', '-t', f'117503445/demo-app:v{ver}', '/workspace/app'], check=True)

        # docker push 117503445/demo-app:v1
        subprocess.run(['docker', 'push', f'117503445/demo-app:v{ver}'], check=True)

    
def main():
    build_image()
    
    # docker run --rm -p 18080:8080 117503445/demo-app:v1
    print('main')


if __name__ == '__main__':
    main()