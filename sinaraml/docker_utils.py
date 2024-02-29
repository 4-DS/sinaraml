import docker
from docker import errors
import tarfile
from pathlib import Path
import logging
import tqdm
from time import sleep
import requests
    

def docker_volume_exists(volume_name):
    try:
        client = docker.from_env()
        client.volumes.get(volume_name)
        return True
    except errors.NotFound:
        pass
    return False

def ensure_docker_volume(volume_name, already_exists_msg):
    if not docker_volume_exists(volume_name):
        docker_volume_create(volume_name)
    else:
        print(already_exists_msg)


def docker_volume_create(volume_name):
    client = docker.from_env()
    client.volumes.create(name=volume_name)


def docker_volume_remove(volume_name):
    client = docker.from_env()
    if docker_volume_exists(volume_name):
        volume = client.volumes.get(volume_name)
        volume.remove(force=True)

def docker_container_exists(container_name):
    try:
        client = docker.from_env()
        client.containers.get(container_name)
        return True
    except errors.NotFound:
        pass
    return False

def docker_container_running(container_name):
    client = docker.from_env()
    if docker_container_exists(container_name):
        container = client.containers.get(container_name)
        if container.status.lower() == "running":
            return True
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

def docker_container_run(image, command=None, **kwargs):
    output = None
    try:
        client = docker.from_env()
        output = client.containers.run(image, command=command, **kwargs)
    except errors.ImageNotFound:
            print(f"Pulling image {image}")
            docker_pull_image(image)
            print(f"Running container")
            output = client.containers.run(image, command=command, **kwargs) 
    return output

def docker_container_start(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.start()

def docker_container_stop(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.stop()

def docker_container_pause(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    container.pause()

def docker_container_remove(container_name):
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.remove(force=True)
    except errors.NotFound as e:
        logging.debug(e)
    
def docker_container_exec(container_name, command):
    client = docker.from_env()
    container = client.containers.get(container_name)
    return container.exec_run(command, privileged=True, user='root', stream=False, demux=True)

def docker_copy_from_container(container_name, src_path, dest_path):
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

def docker_build_image(**kwargs):
    if "decode" not in kwargs:
        kwargs_with_logging = dict(kwargs, decode=True)
    else:
        kwargs_with_logging = dict(kwargs)
    client = docker.from_env()
    for data in client.api.build(**kwargs_with_logging):
        if "stream" in data:
            print(data["stream"])
    
def docker_pull_image(image):
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

def docker_get_port_on_host(container_name, container_port):
    client = docker.from_env()
    container = client.containers.get(container_name)
    # need to use low-level API to get ports spec
    port_data = client.api.inspect_container(container.id)['NetworkSettings']['Ports']
    for port_spec in port_data:
        if str(container_port) in port_spec:
            return port_data[port_spec][0]['HostPort']
    return None
    
def docker_get_container_labels(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)
    # need to use low-level API to get labels
    return container.labels
    
def docker_get_latest_image_version(image_name, repo_name="buslovaev"):
    registry_host = "hub.docker.com"
    next_url = f"/v2/repositories/{repo_name}/{image_name}/tags?page=1&page_size=50"
    # fallback to latest version if no version tag is found in repo
    result = 'latest'
    image_items = []

    payload = ''
    headers = {}
    tries_left = 3
    response = None
    while next_url:
        page_data = {}
        while tries_left > 0:
            try:
                response = None
                response = requests.get(f"https://{registry_host}{next_url}")
                if response.status_code >= 400:
                    raise Exception(f'Bad status {response.status} response from {registry_host}')
                else:
                    break
            except Exception as e:
                logging.debug(e)
                tries_left -= 1
                sleep(3)

        if not response or response.status_code >= 400:
            logging.warning(f"Cannot get image version for {image_name}")
        else:
            page_data = response.json()

        if "results" in page_data:
            image_items.extend(page_data['results'])

        next_url = page_data['next'] if "next" in page_data else None

    if image_items:
        latest_items = [item for item in image_items if "digest" in item and item["name"] == "latest"]
        if latest_items:
            latest_digest = latest_items[0]['digest']
            image_tags = [item["name"] for item in image_items if "digest" in item and item["digest"] == latest_digest and item["name"] != "latest"]
            if image_tags:
                image_tags.sort(key=str.lower, reverse=True)
                result = image_tags[0]

    return result
