from pathlib import Path
import subprocess
import time

def main():
    file_kubeconfig = Path('/workspace/k3s/data/output/kubeconfig.yaml')
    while not file_kubeconfig.exists():
        print(f"Waiting for {file_kubeconfig}")
        time.sleep(5)
    
    kubeconfig = file_kubeconfig.read_text()
    kubeconfig = kubeconfig.replace('127.0.0.1', 'k3s')

    Path('/root/.kube').mkdir(parents=True, exist_ok=True)
    Path('/root/.kube/config').write_text(kubeconfig)

    # kubectl get nodes
    # check if k3s works
    subprocess.run(['kubectl', 'get', 'nodes'], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    main()

