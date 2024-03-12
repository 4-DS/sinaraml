import os
from docker import types
import socket
import re
import urllib
import time
import argparse
from .docker_utils import ensure_docker_volume, \
                          docker_volume_remove, \
                          docker_container_create, \
                          docker_container_exists, \
                          docker_container_start, \
                          docker_container_stop, \
                          docker_container_remove, \
                          docker_container_exec, \
                          docker_pull_image, \
                          docker_get_port_on_host, \
                          docker_get_container_labels, \
                          docker_get_latest_image_version
from .common_utils import get_public_ip, get_expanded_path, get_system_cpu_count, get_system_memory_size
from .platform import SinaraPlatform
from .infra import SinaraInfra
from .plugin_loader import SinaraPluginLoader

class SinaraServer():

    subject = 'server'
    container_name = 'jovyan-single-use'
    sinara_images = [['buslovaev/sinara-notebook', 'buslovaev/sinara-cv'], ['buslovaev/sinara-notebook-exp', 'buslovaev/sinara-cv-exp']]
    root_parser = None
    subject_parser = None
    create_parser = None
    start_parser = None
    remove_parser = None

    @staticmethod
    def add_command_handlers(root_parser, subject_parser):
        SinaraServer.root_parser = root_parser
        SinaraServer.subject_parser = subject_parser
        parser_server = subject_parser.add_parser(SinaraServer.subject, help='sinara server subject')
        server_subparsers = parser_server.add_subparsers(title='action', dest='action', help='Action to do with subject')

        SinaraServer.add_create_handler(server_subparsers)
        SinaraServer.add_start_handler(server_subparsers)
        SinaraServer.add_stop_handler(server_subparsers)
        SinaraServer.add_remove_handler(server_subparsers)
        SinaraServer.add_update_handler(server_subparsers)

    @staticmethod
    def add_create_handler(server_cmd_parser):
        SinaraServer.create_parser = server_cmd_parser.add_parser('create', help='create sinara server')
        SinaraServer.create_parser.add_argument('--instanceName', default=SinaraServer.container_name, type=str, help='sinara server container name (default: %(default)s)')
        SinaraServer.create_parser.add_argument('--runMode', default='q', choices=["q", "b"], help='Runmode, quick (q) - work, data, tmp will be mounted inside docker volumes, basic (b) - work, data, tmp will be mounted from host folders (default: %(default)s)')
        SinaraServer.create_parser.add_argument('--createFolders', default='y', choices=["y", "n"], help='y - create work, data, tmp folders in basic mode automatically, n - folders must be created manually (default: %(default)s)')
        SinaraServer.create_parser.add_argument('--gpuEnabled', choices=["y", "n"], help='y - Enables docker container to use Nvidia GPU, n - disable GPU')
        SinaraServer.create_parser.add_argument('--memLimit', default=str(SinaraServer.get_memory_size_limit()), type=str, help='Maximum amount of memory for server container (default: %(default)s)')
        SinaraServer.create_parser.add_argument('--cpuLimit', default=SinaraServer.get_cpu_cores_limit(), type=int, help='Number of CPU cores to use for server container (default: %(default)s)')
        SinaraServer.create_parser.add_argument('--jovyanRootPath', type=str, help='Path to parent folder for data, work and tmp (only used in basic mode with createFolders=y)')
        SinaraServer.create_parser.add_argument('--jovyanDataPath', type=str, help='Path to data fodler on host (only used in basic mode)')
        SinaraServer.create_parser.add_argument('--jovyanWorkPath', type=str, help='Path to work folder on host (only used in basic mode)')
        SinaraServer.create_parser.add_argument('--jovyanTmpPath', type=str, help='Path to tmp folder on host (only used in basic mode)')
        SinaraServer.create_parser.add_argument('--infraName', default=SinaraInfra.LocalFileSystem, choices=SinaraServer.get_available_infra_names(), type=str, help='Infrastructure name to use (default: %(default)s)')
        SinaraServer.create_parser.add_argument('--insecure', action='store_true', help='Run server without password protection')
        SinaraServer.create_parser.add_argument('--platform', default=SinaraPlatform.Desktop, choices=list(SinaraPlatform), type=SinaraPlatform, help='Server platform - host where the server is run')
        SinaraServer.create_parser.add_argument('--experimental', action='store_true', help='Use expermiental server images')
        SinaraServer.create_parser.add_argument('--image', type=str, help='Custom server image name')
        SinaraServer.create_parser.add_argument('--shm_size', type=str, default="512m", help='Docker shared memory size option (default: %(default)s)')
        SinaraServer.create_parser.set_defaults(func=SinaraServer.create)

    @staticmethod
    def add_start_handler(root_parser):
        server_start_parser = root_parser.add_parser('start', help='start sinara server')
        server_start_parser.add_argument('--instanceName', default=SinaraServer.container_name, help='sinara server container name (default: %(default)s)')
        server_start_parser.set_defaults(func=SinaraServer.start)

    @staticmethod
    def add_stop_handler(root_parser):
        server_stop_parser = root_parser.add_parser('stop', help='stop sinara server')
        server_stop_parser.add_argument('--instanceName', default=SinaraServer.container_name, help='sinara server container name (default: %(default)s)')
        server_stop_parser.set_defaults(func=SinaraServer.stop)

    @staticmethod
    def add_remove_handler(root_parser):
        server_remove_parser = root_parser.add_parser('remove', help='remove sinara server')
        server_remove_parser.add_argument('--instanceName', default=SinaraServer.container_name, help='sinara server container name (default: %(default)s)')
        server_remove_parser.add_argument('--withVolumes', default='n', choices=["y", "n"], help='y - remove existing data, work, tmp docker volumes, n - keep volumes  (default: %(default)s)')
        server_remove_parser.set_defaults(func=SinaraServer.remove)

    @staticmethod
    def add_update_handler(root_parser):
        server_remove_parser = root_parser.add_parser('update', help='update docker image of a sinara server')
        server_remove_parser.add_argument('--image', choices=["ml", "cv"], help='ml - update ml image, cv - update CV image')
        server_remove_parser.add_argument('--experimental', action='store_true', help='Update expermiental server images')
        server_remove_parser.set_defaults(func=SinaraServer.update)

    @staticmethod
    def _is_port_free(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result == 0:
            return False
        return True
    
    @staticmethod
    def get_free_port(port):
        while not SinaraServer._is_port_free(port):
            port += 1
        return port
    
    @staticmethod
    def get_spark_ui_ports_mapping():
        spark_ui_start_port = 4040
        port_count = 20
        sparkui_end_port = spark_ui_start_port + port_count
        result = {}
        free_host_port = spark_ui_start_port-1
        for container_port in range(spark_ui_start_port, sparkui_end_port+1):
            free_host_port = SinaraServer.get_free_port(port=free_host_port+1)
            result[str(container_port)] = str(free_host_port)
        return result
    
    @staticmethod
    def get_jupyter_ui_ports_mapping():
        result = {}
        jupyter_ui_start_port = 8888
        free_host_port = SinaraServer.get_free_port(port=jupyter_ui_start_port)
        result['8888'] = str(free_host_port)
        return result

    @staticmethod
    def get_ports_mapping():
        result = {}
        spark_ui_ports = SinaraServer.get_spark_ui_ports_mapping()
        jupyter_ui_ports = SinaraServer.get_jupyter_ui_ports_mapping()
        result = {**spark_ui_ports, **jupyter_ui_ports}
        return result
    
    @staticmethod
    def get_available_infra_names():
        infras = SinaraServer.get_available_infras()
        return infras.keys()

    @staticmethod
    def get_available_infras():
        infras = {}
        for _infra in SinaraInfra:
            infras[_infra.value] = ["self"]
        infra_plugins = SinaraPluginLoader.get_infra_plugins()
        for plugin in infra_plugins:
            plugin_infras = SinaraPluginLoader.get_infras(plugin)
            for infra in plugin_infras:
                if infra in infras and isinstance(infras[infra], list):
                    infras[infra].append(plugin)
                else:
                    infras[infra] = [plugin]
        return infras

    @staticmethod
    def get_cpu_cores_limit():
        cpu_cores = get_system_cpu_count()
        cores_reserve_for_host = 1
        if not cpu_cores or cpu_cores <= cores_reserve_for_host:
            result = 1
        else:
            result = cpu_cores - cores_reserve_for_host
        return result

    @staticmethod
    def get_memory_size_limit():
        total_mem_bytes = get_system_memory_size()
        bytes_reserve_for_host = int(2 * 1024.**3) # Reserve 2 Gb by default
        if total_mem_bytes <= bytes_reserve_for_host:
            result = int(total_mem_bytes * 0.7)
        else:
            result = int(total_mem_bytes - bytes_reserve_for_host)
        return result      

    

    @staticmethod
    def create(args):
        infras = SinaraServer.get_available_infras()
        current_infra = str(args.infraName)
        
        if current_infra not in infras.keys():
            raise Exception(f'Infra "{current_infra}" is not supported, available: {", ".join(infras.keys())}')

        current_plugin = infras[current_infra][-1]
        if current_plugin == "self":
            SinaraServer._create(args)
        else:
            infra_plugin = SinaraPluginLoader.get_infra_plugin(current_plugin)
            infra_plugin.add_create_arguments(SinaraServer.create_parser)
            extended_args = SinaraServer.root_parser.parse_args()
            infra_plugin.create_server(extended_args)
        
    @staticmethod
    def _create(args):
        args_dict = vars(args)

        gpu_requests = []
        sinara_image_num = 1

        if docker_container_exists(args.instanceName):
            print(f"Sinara server {args.instanceName} aleady exists, remove it and run create again")
            return

        if not args.gpuEnabled:
            sinara_image_num = -1
            while sinara_image_num not in [1, 2]:
                try:
                    sinara_image_num = int(input('Please, choose a Sinara for 1) ML or 2) CV projects: '))
                except ValueError:
                    pass
            if sinara_image_num == 2:
                args_dict['gpuEnabled'] = "y"  
        
        if args.gpuEnabled == "y":
            sinara_image_num = 2
            gpu_requests = [ types.DeviceRequest(count=-1, capabilities=[['gpu']]) ]

        if not args.image:
            sinara_image = SinaraServer.sinara_images[ int(args.experimental) ][ int(sinara_image_num - 1) ]
            versioned_image_tag = docker_get_latest_image_version(sinara_image.split('/')[-1])
            sinara_image_versioned = f"{sinara_image.replace('latest', '')}:{versioned_image_tag}"
        else:
            sinara_image = args.image
            sinara_image_versioned = sinara_image

        if args.runMode == "q":
            docker_volumes = SinaraServer._prepare_quick_mode(args)
        elif args.runMode == "b":
            docker_volumes = SinaraServer._prepare_basic_mode(args)

        server_cmd = "start-notebook.sh --ip=0.0.0.0 --port=8888 --NotebookApp.default_url=/lab --ServerApp.allow_password_change=False"
        if args.insecure:
            server_cmd = f"{server_cmd} --NotebookApp.token='' --NotebookApp.password=''"

        docker_container_create(
            image = sinara_image,
            command = server_cmd,
            working_dir = "/home/jovyan/work",
            name = args.instanceName,
            mem_limit = args.memLimit,
            nano_cpus = 1000000000 * int(args.cpuLimit), # '--cpus' parameter equivalent in python docker client
            shm_size = args.shm_size,
            ports = SinaraServer.get_ports_mapping(),
            volumes = docker_volumes,
            environment = {
                "DSML_USER": "jovyan",
                "JUPYTER_ALLOW_INSECURE_WRITES": "true",
                "JUPYTER_RUNTIME_DIR": "/tmp",
                "INFRA_NAME": args.infraName,
                "JUPYTER_IMAGE_SPEC": sinara_image_versioned,
                "SINARA_SERVER_MEMORY_LIMIT": args.memLimit,
                "SINARA_SERVER_CORES": int(args.cpuLimit)
            },
            labels = {
                "sinaraml.platform": str(args.platform),
                "sinaraml.infra": str(args.infraName)
            },
            device_requests = gpu_requests # '--gpus all' flag equivalent in python docker client
        )
        print(f"Sinara server {args.instanceName} is created")

    @staticmethod
    def _prepare_quick_mode(args):
        data_volume = f"jovyan-data-{args.instanceName}"
        work_volume = f"jovyan-work-{args.instanceName}"
        tmp_volume =  f"jovyan-tmp-{args.instanceName}"

        ensure_docker_volume(data_volume, already_exists_msg="Docker volume with jovyan data is found")
        ensure_docker_volume(work_volume, already_exists_msg="Docker volume with jovyan work is found")
        ensure_docker_volume(tmp_volume, already_exists_msg="Docker volume with jovyan tmp data is found")

        return  [f"{data_volume}:/data",
                 f"{work_volume}:/home/jovyan/work",
                 f"{tmp_volume}:/tmp"]

    @staticmethod
    def _prepare_basic_mode(args):
        folders_exist = ''
        
        if args.createFolders == "y":
             
            jovyan_root_path = get_expanded_path(args.jovyanRootPath) if args.jovyanRootPath else \
                get_expanded_path( input('Please, choose jovyan Root folder path (data, work and tmp will be created there): ') )

            jovyan_data_path = os.path.join(jovyan_root_path, "data")
            jovyan_work_path = os.path.join(jovyan_root_path, "work")
            jovyan_tmp_path = os.path.join(jovyan_root_path, "tmp")

            print("Creating work folders")
            os.makedirs(jovyan_data_path, exist_ok=True)
            os.makedirs(jovyan_work_path, exist_ok=True)
            os.makedirs(jovyan_tmp_path, exist_ok=True)
        else:
            jovyan_data_path = get_expanded_path(args.jovyanDataPath) if args.jovyanDataPath else \
                get_expanded_path( input("Please, choose jovyan Data path: ") )
            
            jovyan_work_path = get_expanded_path(args.jovyanWorkPath) if args.jovyanWorkPath else \
                get_expanded_path( input("Please, choose jovyan Work path: ") )

            jovyan_tmp_path = get_expanded_path(args.jovyanTmpPath) if args.jovyanTmpPath else \
                get_expanded_path( input("Please, choose jovyan Tmp path: ") )

            while folders_exist not in ["y", "n"]:
                folders_exist = input("Please, ensure that the folders exist (y/n): ")

            if folders_exist != "y":
                raise Exception("Sorry, you should prepare the folders beforehand")
        
        print("Trying to run your environment...")
        
        return  [f"{jovyan_data_path}:/data",
                 f"{jovyan_work_path}:/home/jovyan/work",
                 f"{jovyan_tmp_path}:/tmp"]

    @staticmethod
    def prepare_mounted_folders(instance):
        docker_container_exec(instance, "chown -R jovyan:users /tmp")
        docker_container_exec(instance, "chown -R jovyan:users /data")
        docker_container_exec(instance, "chown -R jovyan:users /home/jovyan/work")
        docker_container_exec(instance, "rm -rf /tmp/*")

    @staticmethod
    def get_server_logs(instance, server_command):
        exit_code, output = docker_container_exec(instance, server_command)
        return output

    @staticmethod
    def get_server_url(instance):
        url = None
        commands = ["jupyter lab list", "jupyter server list", "jupyter notebook list"]
        for cmd in commands:
            output = SinaraServer.get_server_logs(instance, cmd)
            stdout, stderr = output
            log_lines_stderr = [] if not stderr else stderr.decode('utf-8').split('\n')
            log_lines_stdout = [] if not stdout else stdout.decode('utf-8').split('\n')
            log_lines = [] if not stderr and not stdout else [*log_lines_stderr, *log_lines_stdout]
            for line in log_lines:
                if any(x in line for x in ['http://', 'https://']):
                    m = re.search(r"(http[^\s]+)", line)
                    url = m.group(1) if m else None
                    if url: 
                        break
            if url:
                break
        return url
    
    @staticmethod
    def get_server_protocol(server_url):
        m = re.search(r"^(http:|https:)", server_url)
        return str(m.group(1))[:-1] if m else None

    @staticmethod
    def get_server_token(server_url):
        m = re.search(r"token=([a-f0-9-][^\s]+)", server_url)
        return m.group(1) if m else None
    
    @staticmethod
    def get_server_platform(instance):
        labels = docker_get_container_labels(instance)
        # Fallback to desktop platform for legacy servers without labels
        if not "sinaraml.platform" in labels:
            return SinaraPlatform.Desktop
        return SinaraPlatform(labels["sinaraml.platform"])
    
    @staticmethod
    def get_server_ip(platform):
        if platform == SinaraPlatform.Desktop:
            return "127.0.0.1"
        public_ip = get_public_ip()
        if not public_ip:
            return "{{vm_public_ip}}"
        return public_ip

    
    @staticmethod
    def wait_for_token(jupyter_ui_url):
        import urllib.request
        http_exception = None
        for i in range(30):
            try:
                req = urllib.request.Request(jupyter_ui_url)
                urllib.request.urlopen(req)
            except Exception as e:
                http_exception = e
                time.sleep(1)
                continue
            else:
                http_exception = None
                time.sleep(1)
                break
        if http_exception:
            raise http_exception

    @staticmethod
    def start(args):
        if not docker_container_exists(args.instanceName):
            print(f"Sinara server with name {args.instanceName} doesn't exist yet, run 'sinara server create' first")
            return
        
        print(f'Starting sinara server {args.instanceName}...')
        
        docker_container_start(args.instanceName)
        SinaraServer.prepare_mounted_folders(args.instanceName)

        host_port = docker_get_port_on_host(args.instanceName, 8888)
        server_alive_url = f"http://127.0.0.1:{host_port}"

        # Wait for server token to be available in container logs, may take some time
        SinaraServer.wait_for_token(server_alive_url)

        url = SinaraServer.get_server_url(args.instanceName)
        token = SinaraServer.get_server_token(url)
        token_str = f"?token={token}" if token else ""
        protocol = SinaraServer.get_server_protocol(url)
        
        platform = SinaraServer.get_server_platform(args.instanceName)
        server_ip = SinaraServer.get_server_ip(platform)
        server_url = f"{protocol}://{server_ip}:{host_port}/{token_str}"

        if not platform == SinaraPlatform.Desktop:
            server_hint = f"Detected server url {protocol}://{server_ip}:{host_port}/{token_str}\nIf server is not accessible, find your public VM IP address manually"
        else:
            server_hint = f"Go to {server_url} to open jupyterlab"

        print(f"Sinara server {args.instanceName} started, platform: {platform}\n{server_hint}")

    @staticmethod
    def stop(args):
        if not docker_container_exists(args.instanceName):
            raise Exception(f"Your server with name {args.instanceName} doesn't exist")
        docker_container_stop(args.instanceName)
        print(f'Sinara server {args.instanceName} stopped')

    @staticmethod
    def remove(args):
        if not docker_container_exists(args.instanceName):
            print(f"Server with name {args.instanceName} has been already removed")
        docker_container_remove(args.instanceName)
        if args.withVolumes == "y":
            print("Removing docker volumes")
            data_volume = f"jovyan-data-{args.instanceName}"
            work_volume = f"jovyan-work-{args.instanceName}"
            tmp_volume =  f"jovyan-tmp-{args.instanceName}"
            docker_volume_remove(data_volume)
            docker_volume_remove(work_volume)
            docker_volume_remove(tmp_volume)
        print(f'Sinara server {args.instanceName} removed')

    @staticmethod
    def update(args):
        args_dict = vars(args)
        sinara_image_num = -1
        if not args.image:
            while sinara_image_num not in [1, 2]:
                try:
                    sinara_image_num = int(input('Please, choose a Sinara image to update 1) ML or 2) CV projects: '))
                except ValueError:
                    pass
        elif args.image == "ml":
            sinara_image_num = 1
        elif args.image == "cv":
            sinara_image_num = 2

        sinara_image = SinaraServer.sinara_images[ int(args.experimental) ][ sinara_image_num-1 ]
        docker_pull_image(sinara_image)
        print(f'Sinara server image {sinara_image} updated successfully')
