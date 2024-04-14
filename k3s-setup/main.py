#!/usr/bin/env python3

import time
from pathlib import Path
import subprocess

def is_traefik_dashboard_ready():
    # GET http://k3s/dashboard
    resp = subprocess.run(['curl', 'http://k3s/dashboard'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return resp is not None and '<html>' in resp.stdout.decode()
    # if resp is not None and '<html>' in resp.stdout.decode():
    #     print('Traefik Dashboard is ready at http://k3s/dashboard')
    # else:
    #     print('Traefik Dashboard is not ready yet')
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

    if not is_traefik_dashboard_ready():
        # kubectl get nodes
        # check if k3s works
        subprocess.run(['kubectl', 'get', 'nodes'], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        while True:
            # kubectl apply -f /workspace/k3s-setup/.k8s/traefik
            out = subprocess.run(['kubectl', 'apply', '-f', '/workspace/k3s-setup/.k8s/traefik'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if out.returncode == 0:
                break
            else:
                if 'The Service "traefik" is invalid: spec.ports: Required value' in out.stderr.decode():
                    print('Waiting for traefik service to be created')
                    time.sleep(1)
                else:
                    print('Failed to apply traefik service')
                    break

        # kubectl apply -f /workspace/k3s-setup/.k8s/traefik-dashboard
        subprocess.run(['kubectl', 'apply', '-f', '/workspace/k3s-setup/.k8s/traefik-dashboard'], check=True)

        try_times = 0
        while True:
            if is_traefik_dashboard_ready():
                print('Traefik Dashboard is ready at http://k3s/dashboard')
                break
            print('Waiting for Traefik Dashboard to be ready')
            time.sleep(1)
            try_times += 1
            if try_times > 5 * 60:
                print('Traefik Dashboard is not ready yet')
                break
    else:
        print('Traefik Dashboard is ready at http://k3s/dashboard')


if __name__ == '__main__':
    main()