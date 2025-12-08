import os
import sys
import logging
from dockerspawner import SwarmSpawner

c = get_config()

class CustomSwarmSpawner(SwarmSpawner):
    def _options_form_default(self):
        cpu_options = [2, 4, 8]  # Possible values for CPUs
        memory_options = [2, 4, 8]  # Possible values for memory in GB
        form_template = """
        <div class="form-group">
            <label for="stack">Choose an image</label>
            <select id="stacks" class="form-control" name="stack">
                <option value="quay.io/jupyter/base-notebook:latest">base-notebook</option>
                <option value="quay.io/jupyter/scipy-notebook:latest">scipy-notebook</option>
            </select>
        </div>
        <label for="cpu_limit">CPUs:</label>
        <select class="form-control" name="cpu_limit" id="cpu_limit">
            {cpu_options}
        </select>
        <label for="memory_limit">Memory (GiB):</label>
        <select class="form-control" name="memory_limit" id="memory_limit">
            {memory_options}
        </select>
        """
        # Populate the CPU options
        cpu_select = "\n".join([f"<option>{cpu}</option>" for cpu in cpu_options])
        # Populate the memory options
        memory_select = "\n".join([f"<option>{memory}</option>" for memory in memory_options])

        # Render the final form
        options_form = form_template.format(
            cpu_options=cpu_select,
            memory_options=memory_select
        )
        return options_form

    def options_from_form(self, formdata):
        options = {}
        options['stack'] = formdata.get('stack', [''])[0].strip()
        options['mem_limit'] = formdata.get('memory_limit', [''])[0].strip() + "G"
        options['cpu_limit'] = int(formdata.get('cpu_limit', [''])[0].strip())
        
        self.image = options['stack']
        self.mem_limit = options['mem_limit']
        self.cpu_limit = options['cpu_limit']
        
        return options

def create_dir_hook(SwarmSpawner):
    username = SwarmSpawner.user.name  # get the username
    volume_path = os.path.join('/mnt/nfs/jupyterhub/volumes', username)
    if not os.path.exists(volume_path):
        os.makedirs(volume_path, 0o755)
        os.chown(volume_path, 1000, 100)
    mounts_user = [
        {'type': 'bind',
         'source': volume_path,
         'target': '/home/jovyan/work'        
        }
    ]
        
    SwarmSpawner.environment = {
        'GRANT_SUDO': 'yes',
        'NB_USER': 'jovyan',
        'NB_UID': 1000,
        'NB_GID': 100,
    }
    
    SwarmSpawner.extra_container_spec = {
        'mounts': mounts_user,
        'user': '0'
    }
    
    SwarmSpawner.notebook_dir = f'/home/jovyan/work'

# Use the built-in dummy authenticator
#c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.authenticator_class = "shared-password"
c.SharedPasswordAuthenticator.user_password = "my-workshop-2042"

c.Authenticator.allowed_users = {"bayu", "danger", "eggs"}

# Grant admin users access
c.Authenticator.admin_users = {"danger", "eggs"}
c.SharedPasswordAuthenticator.admin_password = "extra-super-secret-secure-password"

# use SwarmSpawner
c.JupyterHub.spawner_class = CustomSwarmSpawner
c.Spawner.pre_spawn_hook = create_dir_hook

c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'
network_name = os.environ['DOCKER_NETWORK_NAME']
c.SwarmSpawner.network_name = network_name
c.SwarmSpawner.extra_host_config = {'network_mode': network_name}

# increase launch timeout because initial image pulls can take a while
c.SwarmSpawner.http_timeout = 300
c.SwarmSpawner.start_timeout = 300
c.SwarmSpawner.remove_containers = True

# start jupyterlab
c.Spawner.cmd = ["jupyter", "labhub"]
c.SwarmSpawner.debug = False
c.JupyterHub.log_level = logging.DEBUG
c.JupyterHub.last_activity_interval = 600  # Poll activity every 10 minutes
c.JupyterHub.shutdown_on_logout = True
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': [sys.executable, '-m', 'jupyterhub_idle_culler', '--timeout=3600'],
        'api_token': 'super-secret-token',
    }
]

c.JupyterHub.load_roles = [
    {
        "name": "list-and-cull", # name the role
        "services": [
            "idle-culler", # assign the service to this role
        ],
        'api_token': 'super-secret-token',
        "scopes": [
            # declare what permissions the service should have
            "list:users", # list users
            "read:users:activity", # read user last-activity
            "admin:servers", # start/stop servers
        ],
    }
]
