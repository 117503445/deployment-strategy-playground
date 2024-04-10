```sh
docker compose up -d

# wait until healthy

# control-dev 
/workspace/k3s-setup/main.py
rye sync
rye run python ./src/control/build.py
rye run python ./src/control/main.py


./scripts/clean.sh
```