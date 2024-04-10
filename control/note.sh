rye run python ./src/control/k.py
rye run python ./src/control/main.py
rye run python ./src/control/build.py

curl -L https://github.com/fortio/fortio/releases/download/v1.63.7/fortio-linux_amd64-1.63.7.tgz | sudo tar -C / -xvzpf -

fortio load -a -c 50 -qps 500 -t 60s k3s

curl k3s