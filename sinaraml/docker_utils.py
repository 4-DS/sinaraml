import docker
from docker import errors
import os
import tarfile
from pathlib import Path
import logging
import tqdm
    

def docker_volume_exists(volume_name):
    try:
        client = docker.from_env()
        client.volumes.get(volume_name)
        return True
    except errors.NotFound:
        pass
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot check volume {volume_name} existance.\nCheck if you have permission to access docker volumes')
    return False

def ensure_docker_volume(volume_name, already_exists_msg):
    if not docker_volume_exists(volume_name):
        docker_volume_create(volume_name)
    else:
        print(already_exists_msg)


def docker_volume_create(volume_name):
    try:
        client = docker.from_env()
        client.volumes.create(name=volume_name)
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot create volume {volume_name}.\nCheck if you have permission to access docker volumes')


def docker_volume_remove(volume_name):
    try:
        client = docker.from_env()
        if docker_volume_exists(volume_name):
            volume = client.volumes.get(volume_name)
            volume.remove(force=True)
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot remove volume {volume_name}.\nCheck if you have permission to access docker volumes')

def docker_container_exists(container_name):
    try:
        client = docker.from_env()
        client.containers.get(container_name)
        return True
    except errors.NotFound:
        pass
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot check container {container_name} existance.\nCheck if you have permission to access docker containers')
    return False

def docker_container_running(container_name):
    try:
        client = docker.from_env()
        if docker_container_exists(container_name):
            container = client.containers.get(container_name)
            if container.status.lower() == "running":
                return True
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot check container {container_name} state.\nCheck if you have permission to access docker containers')
    return False

def docker_container_create(image, command=None, **kwargs):
    try:
        client = docker.from_env()
        client.containers.create(image, command=command, **kwargs)
    except errors.ImageNotFound:
            print(f"Pulling image {image}")
            docker_pull_image(image)
            print(f"Creating container")
            client.containers.create(image, command=command, **kwargs)
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot create container from {image}.\nCheck if you have permission to access docker containers')

def docker_container_run(image, command=None, **kwargs):
    try:
        client = docker.from_env()
        output = client.containers.run(image, command=command, **kwargs)
        return output
    except errors.ImageNotFound:
            print(f"Pulling image {image}")
            docker_pull_image(image)
            print(f"Running container")
            client.containers.run(image, command=command, **kwargs)
            return output
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot run image {image}.\nCheck if you have permission to access docker containers')

def docker_container_start(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.start()
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot start container {container_name}.\nCheck if you have permission to access docker containers')

def docker_container_stop(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.stop()
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot stop container {container_name}.\nCheck if you have permission to access docker containers')

def docker_container_pause(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.pause()
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot pause container {container_name}.\nCheck if you have permission to access docker containers')  

def docker_container_remove(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.remove(force=True)
    except docker.errors.NotFound:
        pass
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot remove container {container_name}.\nCheck if you have permission to access docker containers')
    
def docker_container_exec(container_name, command):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        return container.exec_run(command, privileged=True, user='root', stream=False, demux=True)
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot exec command in container {container_name}.\nCheck if you have permission to access docker containers')

def docker_copy_from_container(container_name, src_path, dest_path):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        stream, stat = container.get_archive(src_path)
        archive_file_path = Path(dest_path) / '_tmp_archive.tar'
        with open(archive_file_path, 'wb') as archive_file:
            for chunk in stream:
                archive_file.write(chunk)
        with tarfile.TarFile(archive_file_path, 'r') as tar_file:
            for member in tar_file.getmembers():
                if member.isreg():
                    # keep folder structure, but without the first folder since it duplicates the parent folder we created
                    member_path_absolute = Path(f"/{member.name}")
                    member_path_relative = Path(*member_path_absolute.parts[2:])
                    member.name = str(member_path_relative)
                    tar_file.extract(member, dest_path)
        Path.unlink(archive_file_path)
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot copy files from container {container_name}.\nCheck if you have permission to access docker containers')

def docker_build_image(**kwargs):
    try:
        if "decode" not in kwargs:
            kwargs_with_logging = dict(kwargs, decode=True)
        else:
            kwargs_with_logging = dict(kwargs)
        client = docker.from_env()
        for data in client.api.build(**kwargs_with_logging):
            if "stream" in data:
                print(data["stream"])
        
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot build image.\nCheck if you have permission to access docker')
    
def docker_pull_image(image):
    try:
        client = docker.from_env()
        with tqdm.tqdm(unit=" b") as progress_bar:
            layers = {}
            for data in client.api.pull(image, stream=True, decode=True):
                progress = data.get("progressDetail")
                layer_id = data.get("id")

                if (layer_id is not None) and (progress is not None):
                    layers[layer_id] = progress

                    progress_bar.total = sum(
                        [
                            val.get("total", 0)
                            for _, val in layers.items()
                            if val is not None
                        ]
                    )
                    progress_bar.n = sum(
                        [
                            val.get("current", 0)
                            for _, val in layers.items()
                            if val is not None
                        ]
                    )
                progress_bar.update(0)
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot pull image {image}.\nCheck if you have permission to access docker')

def docker_get_port_on_host(container_name, container_port):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        # need to use low-level API to get ports spec
        port_data = client.api.inspect_container(container.id)['NetworkSettings']['Ports']
        for port_spec in port_data:
            if str(container_port) in port_spec:
                return port_data[port_spec][0]['HostPort']
        return None
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot get ports of container {container_name}.\nCheck if you have permission to access docker containers')
    
def docker_get_container_labels(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        # need to use low-level API to get labels
        return container.labels
    except Exception as e:
        logging.debug(e)
        raise Exception(f'Cannot get labels of container {container_name}.\nCheck if you have permission to access docker containers')