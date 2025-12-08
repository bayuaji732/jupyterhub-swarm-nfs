# JupyterHub with Docker Swarm and NFS

A production-ready JupyterHub deployment using Docker Swarm for container orchestration and NFS for persistent storage. This setup allows multiple users to spawn their own Jupyter notebook servers with customizable resources.

## Versions

- JupyterHub: 5.4.2 (tested)
- DockerSpawner: 14.0.0 (tested)
- Docker Engine: 29.1.2 (tested)
- OS: Rocky Linux 9 (tested)

## Features

- 🐳 Docker Swarm orchestration for high availability
- 📦 Multiple notebook images (base-notebook, scipy-notebook)
- 💾 NFS-backed persistent storage for user notebooks
- 🔐 Shared password authentication with admin controls
- ⚙️ User-configurable CPU and memory limits
- 🔄 Automatic idle server culling after 1 hour
- 🌐 Overlay networking for service discovery

## Prerequisites

- Docker Engine 29.1.2 or later
- Docker Swarm initialized
- NFS server configured (tested on Rocky Linux 9)
- Root or sudo access on all nodes

## Setup Instructions

### 1. Initialize Docker Swarm

If you haven't already initialized Docker Swarm on your manager node:

```bash
docker swarm init --advertise-addr <MANAGER_IP>
```

To add worker nodes (optional):

```bash
# On worker nodes, run the command provided
docker swarm join --token <TOKEN> <MANAGER_IP>:2377
```

Verify your swarm cluster:

```bash
docker node ls
```

### 2. Configure NFS Server

**On NFS Server (Rocky Linux 9):**

```bash
# Install NFS utilities
sudo dnf install -y nfs-utils

# Create the shared directory
sudo mkdir -p /mnt/nfs/jupyterhub/volumes
sudo chown nobody:nobody /mnt/nfs
sudo chmod 777 /mnt/nfs

# Configure NFS exports
sudo nano /etc/exports

# Add the following line (adjust network range as needed):
/mnt/nfs   *(rw,sync,no_root_squash,no_subtree_check)

# Start and enable NFS service
sudo exportfs -arv
sudo systemctl enable --now nfs-server

# Configure firewall:
sudo firewall-cmd --permanent --add-service=nfs
sudo firewall-cmd --permanent --add-service=mountd
sudo firewall-cmd --permanent --add-service=rpc-bind
sudo firewall-cmd --reload
```

**On NFS Client (Rocky Linux 9):**

```bash
# Install NFS client
sudo dnf install -y nfs-utils  # Rocky Linux

# Create mount point
sudo mkdir -p /mnt/nfs

# Mount NFS share
sudo mount -t nfs <NFS_SERVER_IP>:/mnt/nfs /mnt/nfs

# Make mount persistent (add to /etc/fstab)
sudo nano /etc/fstab

# Add the line (adjust server IP):
<NFS_SERVER_IP>:/mnt/nfs   /mnt/nfs   nfs   defaults,_netdev   0 0
```

### 3. Create Docker Network

Create an overlay network for JupyterHub services to communicate:

```bash
docker network create --driver overlay --attachable jupyterhub_network
```

Verify the network:

```bash
docker network ls | grep jupyterhub_network
```

### 4. Configure Authentication

Edit `jupyterhub_config.py` to set your passwords and allowed users:

```python
# User password for login
c.SharedPasswordAuthenticator.user_password = "my-workshop-2042"

# Allowed users
c.Authenticator.allowed_users = {"bayu", "danger", "eggs"}

# Admin users and password
c.Authenticator.admin_users = {"danger", "eggs"}
c.SharedPasswordAuthenticator.admin_password = "extra-super-secret-secure-password"
```

**⚠️ Security Note:** Change these default passwords before deploying to production!

## Using SwarmSpawner

In general, when configuring a Spawner, there is one primary concern to get it working: **Make sure the servers can connect to the Hub**.
This generally takes the form of network configuration of the Hub,
and possibly also the Spawner.

This directory contains an example `docker-compose.yml` that does the following:

- configures jupyterhub to use `SharedPasswordAuthenticator` (for testing) and `SwarmSpawner`. (Added in version 5.3: `SharedPasswordAuthenticator` is added and `DummyAuthenticator.password` is deprecated.)
- runs the hub and proxy in separate containers.
- creates an `overlay` network `jupyterhub_network` so that everybody can communicate across the swarm.

The key parts of jupyterhub configuration make the Hub accessible on the docker network. First, make sure that the Hub is connectable from outside its own container:

```python
c.JupyterHub.hub_ip = '0.0.0.0'
```

Then, tell everyone (singleuser servers and proxy)
to connect to it using it's hostname on the docker network
(this is the name of the service running the jupyterhub image):

```python
c.JupyterHub.hub_connect_ip = 'jupyterhub'
```

Finally, we need to put user servers onto the same network as the Hub.
In `docker-compose.yml`, we created a network called `jupyterhub_network`,
and put the hub and proxy on it:

```yaml
networks:
  jupyterhub_network:
    external: True
```

### 5. Build Docker Image

Build the JupyterHub Docker image:

```bash
docker-compose build
```

### 6. Deploy JupyterHub

Start the JupyterHub service:

```bash
docker-compose up -d
```

Check the service status:

```bash
docker-compose ps
docker service ls
```

View logs:

```bash
docker-compose logs -f jupyterhub
```

## Accessing JupyterHub

Once deployed, access JupyterHub at:

```
http://<MANAGER_IP>:8333
```

Login with:

- **Username:** Any user from `allowed_users` (bayu, danger, eggs)
- **Password:** `my-workshop-2042`
- **Admin Password:** `extra-super-secret-secure-password` (for admin users)

## User Experience

When users log in, they can:

1. Select a notebook image (base-notebook or scipy-notebook)
2. Choose CPU allocation (2, 4, or 8 cores)
3. Choose memory allocation (2, 4, or 8 GiB)
4. Launch their personal Jupyter Lab environment

All user work is saved to `/mnt/nfs/jupyterhub/volumes/<username>` and persists across sessions.

## Configuration Details

### Resource Limits

Users can select from predefined resource options:

- **CPU:** 2, 4, or 8 cores
- **Memory:** 2, 4, or 8 GiB

### Idle Culling

Servers are automatically shut down after 1 hour of inactivity to save resources.

### Available Notebook Images

- `quay.io/jupyter/base-notebook:latest` - Minimal Jupyter installation
- `quay.io/jupyter/scipy-notebook:latest` - Includes scientific Python stack

## Stopping JupyterHub

```bash
# Stop the service
docker-compose down

# Stop and remove all
docker-compose down --rmi all
```

## Security Recommendations

- [ ] Change all default passwords
- [ ] Use HTTPS with SSL certificates
- [ ] Implement proper authentication (LDAP, OAuth, etc.)
- [ ] Configure firewall rules
- [ ] Regularly update Docker images
- [ ] Monitor resource usage and set quotas
- [ ] Enable Docker secrets for sensitive data

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License - feel free to use and modify for your needs.

## References

- [JupyterHub Documentation](https://jupyterhub.readthedocs.io/)
- [SwarmSpawner Documentation](https://jupyterhub-dockerspawner.readthedocs.io/en/latest/spawner-types.html#swarmspawner)
- [Docker Swarm Documentation](https://docs.docker.com/engine/swarm/)
