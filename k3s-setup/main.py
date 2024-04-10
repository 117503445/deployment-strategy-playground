#!/usr/bin/env python3

import time
from pathlib import Path
import subprocess

def main():
    file_kubeconfig = Path('/workspace/k3s/data/output/kubeconfig.yaml')
    while not file_kubeconfig.exists():
        print(f"Waiting for {file_kubeconfig}")
        time.sleep(5)
    
    kubeconfig = file_kubeconfig.read_text()
    kubeconfig = kubeconfig.replace('127.0.0.1', 'k3s')

    Path('/workspace/k3s/data/output/kubeconfig.public.yaml').write_text(kubeconfig)

    Path('/root/.kube').mkdir(parents=True, exist_ok=True)
    Path('/root/.kube/config').write_text(kubeconfig)

    # kubectl get nodes
    # check if k3s works
    subprocess.run(['kubectl', 'get', 'nodes'], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # kubectl apply -f /workspace/k3s-setup/.k8s/traefik
    subprocess.run(['kubectl', 'apply', '-f', '/workspace/k3s-setup/.k8s/traefik'], check=True)

    # kubectl apply -f /workspace/k3s-setup/.k8s/traefik-dashboard
    subprocess.run(['kubectl', 'apply', '-f', '/workspace/k3s-setup/.k8s/traefik-dashboard'], check=True)

    time.sleep(1)

    # GET http://k3s/dashboard
    resp = subprocess.run(['curl', 'http://k3s/dashboard'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if resp is not None and '<html>' in resp.stdout.decode():
        print('Traefik Dashboard is ready at http://k3s/dashboard')
    else:
        print('Traefik Dashboard is not ready yet')
        
    


if __name__ == '__main__':
    main()