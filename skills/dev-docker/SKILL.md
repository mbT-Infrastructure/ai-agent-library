---
name: dev-docker
description:
    Use ONLY when writing Dockerfiles, docker-compose, buildx builders, container volumes, or
    wake-on-LAN config in mbT projects.
---

# dev-docker — volumes, buildx, WOL, compose loop

## Container volumes

| Path                                  | Purpose                     |
| ------------------------------------- | --------------------------- |
| `/dev/dri`                            | GPU / hardware acceleration |
| `/media/###APP_NAME###/`              | App data                    |
| `/media/proxychains/proxychains.conf` | Proxychains config          |
| `/media/user/pulse-native-socket`     | Audio socket                |
| `/media/user/.Xauthority`             | X auth                      |
| `/tmp/.X11-unix`                      | X socket                    |
| `/media/workdir`                      | Working directory           |

## Docker buildx builders

    docker buildx ls
    docker buildx use multi-arch

Local:

    docker buildx create --driver docker-container --name multi-arch --node local

Remote:

    docker buildx create --name multi-arch-remote --node amd64-remote ssh://development
    docker buildx create --name multi-arch-remote --append --node arm-remote ssh://development-arm

## Wake-on-LAN (WOL)

    docker inspect "${DOCKER_NETWORK:?}"
    ip route | grep ###SUBNET###

Take the `br-????????????` interface, then:

    sysctl "net.ipv4.conf.${DOCKER_NETWORK_INTERFACE:?}.bc_forwarding=1"

Persist to `/etc/sysctl.d/docker-network-${DOCKER_NETWORK:?}.conf`.

## Compose-subfolder loop

Bash loop over subfolders; start compose where a compose file exists, else warn:

    for FOLDER in */; do
        if [ -f "${FOLDER}/docker-compose.yaml" ]; then
            docker compose -f "${FOLDER}/docker-compose.yaml" up --detach
        else
            echo "No compose file in ${FOLDER}, skipping"
        fi
    done
