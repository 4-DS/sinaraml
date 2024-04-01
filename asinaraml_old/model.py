from pathlib import Path
import shutil
import zipfile
import tempfile
from docker import types
import glob
from .docker_utils import docker_container_create, \
                          docker_container_exists, \
                          docker_container_start, \
                          docker_container_stop, \
                          docker_container_remove, \
                          docker_container_run, \
                          docker_copy_from_container, \
                          docker_build_image

from .common_utils import compute_md5, get_expanded_path, replace_bentoservice_model_server_image, get_bentoservice_profile_name

bentoservice_profiles_supported = {
    'SinaraOnnxBentoService': 'onnx',
    'SinaraPytorchBentoService': 'pytorch',
    'SinaraBinaryBentoService': 'binary'
}

class SinaraModel():

    subject = 'model'
    server_container_name = 'jovyan-single-use'
    model_container_name = 'sinara-model'

    @staticmethod
    def add_command_handlers(root_parser):
        parser_model = root_parser.add_parser(SinaraModel.subject, help='sinara model subject')
        model_subparsers = parser_model.add_subparsers(title='action', dest='action', help='Action to do with subject')

        SinaraModel.add_containerize_handler(model_subparsers)
        SinaraModel.add_extract_artifacts_handler(model_subparsers)

    @staticmethod
    def add_containerize_handler(root_parser):
        model_containerize_parser = root_parser.add_parser('containerize', help='containerize sinara bento service into a docker image')
        model_containerize_parser.add_argument('--instanceName', default=SinaraModel.server_container_name, help='Custom model container name to start (default: %(default)s)')
        model_containerize_parser.add_argument('--bentoservicePath', help='Path to bentoservice inside sinara server')
        model_containerize_parser.add_argument('--dockerRegistry', help='Docker registry url of a model image')
        model_containerize_parser.set_defaults(func=SinaraModel.containerize)

    @staticmethod
    def add_extract_artifacts_handler(root_parser):
        model_extract_artifacts_parser = root_parser.add_parser('extract_artifacts', help='extract artifacts from sinara model container')
        model_extract_artifacts_parser.add_argument('--modelImage', help='Docker model image to extract artifacts from')
        model_extract_artifacts_parser.add_argument('--extractTo', help='Folder on host, were to place extracted artifacts')
        model_extract_artifacts_parser.set_defaults(func=SinaraModel.extract_artifacts)

    @staticmethod
    def save_extra_info(bentoservice_dir, image_tag):
        file_paths = glob.glob(f'{bentoservice_dir}/*/artifacts/*')
        if len(file_paths) > 0:
            first_artifact_path = Path(file_paths[0])
            bento_service_class = first_artifact_path.parts[-3]
            bentoservice_artifacts_dir = Path(bentoservice_dir) / bento_service_class / 'artifacts'
            checksum_dir = bentoservice_artifacts_dir / 'checksum'
            artifacts_list_path = checksum_dir / 'artifacts_list.txt'
            checksum_dir.mkdir(parents=True, exist_ok=True)

            artifacts_list_path.touch(exist_ok=True)
            with artifacts_list_path.open(mode='w') as artifacts_list_file:
                for file_path in file_paths:
                    file_p = Path(file_path)
                    artifacts_list_file.write(f'{file_p.stem}\n')
                    md5_path = bentoservice_artifacts_dir / 'checksum' / f'{file_p.stem}.md5'
                    with md5_path.open(mode='w') as md5_file:
                        md5_file.write(compute_md5(file_path))

        docker_image_info_path = bentoservice_artifacts_dir / 'checksum' / 'docker_image_info.txt'
        docker_image_info_path.touch(exist_ok=True)
        with docker_image_info_path.open(mode='w') as docker_image_info_file:
            docker_image_info_file.write(image_tag)

    @staticmethod
    def containerize(args):
        def get_run_id_from_path(_path):
            return Path(_path).parts[-2]
        
        def get_bentoserice_cache_dir(bentoservice_name):
            tmp_dir = tempfile.gettempdir()
            return Path(tmp_dir) / Path(bentoservice_name).parts[-1]
        
        def get_model_name(save_info_path):
            with open(save_info_path, 'r') as save_info_file:
                model_name = save_info_file.read()
                model_name = model_name.split("BENTO_SERVICE=")[-1]
                model_name = '.'.join(model_name.split(".")[0:-1])
            return model_name

        args_dict = vars(args)
        if not args.bentoservicePath:
            while not args.bentoservicePath:
                args_dict['bentoservicePath'] = get_expanded_path( input("Please, enter ENTITY_PATH for your bentoservice: ") )

        model_image_tag = get_run_id_from_path(args.bentoservicePath)

        if not args.dockerRegistry:
            while not args.dockerRegistry:
                args_dict['dockerRegistry'] = input("Please, enter Docker registry address for your model image: ")

        bentoservice_cache_dir = get_bentoserice_cache_dir(args.bentoservicePath)

        if bentoservice_cache_dir.exists():
            shutil.rmtree(bentoservice_cache_dir)
        bentoservice_cache_dir.mkdir(parents=True, exist_ok=True)
        docker_copy_from_container(args.instanceName, src_path=args.bentoservicePath, dest_path=bentoservice_cache_dir)
        model_zip_path = bentoservice_cache_dir / "model.zip"
        success_file_path = bentoservice_cache_dir / "_SUCCESS"
        save_info_path = bentoservice_cache_dir / "save_info.txt"
        bentoservice_dockerfile_path = bentoservice_cache_dir / "Dockerfile"


        with zipfile.ZipFile(model_zip_path, 'r') as model_zip:
            model_zip.extractall(path=bentoservice_cache_dir)

        Path(model_zip_path).unlink(missing_ok=True)
        Path(success_file_path).unlink(missing_ok=True)

        model_image_name = get_model_name(save_info_path)
        model_image_name_full = f"{args.dockerRegistry}/{model_image_name}:{model_image_tag}"

        SinaraModel.save_extra_info(bentoservice_cache_dir, model_image_name_full)

        bentoservice_profile = get_bentoservice_profile_name(bentoservice_cache_dir)
        if bentoservice_profile:
            if bentoservice_profile not in bentoservice_profiles_supported.keys():
                raise Exception(f'Unsupported bentoservice profile "{bentoservice_profile}" in bentoservice found. Supported: {", ".join(bentoservice_profiles_supported.keys())}')
            
            print(f'Using bentoservice profile: {bentoservice_profile}')

            if bentoservice_profile == 'SinaraOnnxBentoService':
                replace_bentoservice_model_server_image(bentoservice_dockerfile_path, "buslovaev/sinara-onnx-model-server")

        print(f"Building model image {model_image_name_full}")
        docker_build_image(path=str(bentoservice_cache_dir), tag=model_image_name_full, pull=True, forcerm=True, rm=True, quiet=False)
        print(f"Model image {model_image_name_full} built successfully")

    @staticmethod
    def start(args):
        args_dict = vars(args)
        gpu_requests = []
        model_type = -1

        if not docker_container_exists(args.modelContainerName):
            if not args.modelImage:
                while not args.modelImage:
                    args_dict['modelImage'] = input("Please, enter your model image to run: ")

            if not args.gpuEnabled:
                while model_type not in [1, 2]:
                    model_type = int(input('Please, choose model type for this model 1) ML or 2) CV: '))
                if model_type == 2:
                    args_dict['gpuEnabled'] = "y"
                    gpu_requests = [ types.DeviceRequest(count=-1, capabilities=[['gpu']]) ]

            docker_container_run(
                image = args.modelImage,
                name = args.modelContainerName,
                shm_size = "512m",
                ports = {"5000": "5000"},
                device_requests = gpu_requests # '--gpus all' flag equivalent in python docker client
            )

        docker_container_start(args.modelContainerName)
        print("Your jovyan single use container is started")

    @staticmethod
    def stop(args):
        if not docker_container_exists(args.modelContainerName):
            raise Exception(f"Your model container with name {args.modelContainerName} doesn't exist")
        docker_container_stop(args.modelContainerName)

    @staticmethod
    def extract_artifacts(args):
        args_dict = vars(args)

        if not args.modelImage:
            while not args.modelImage:
                args_dict['modelImage'] = input("Please, input model image name with tag: ")

        if not args.extractTo:
            while not args.extractTo:
                args_dict['extractTo'] = get_expanded_path( input("Please, input path to folder where to extract artifacts: ") )

        Path(args.extractTo).mkdir(parents=True, exist_ok=True)

        docker_container_remove(SinaraModel.model_container_name)

        model_cmd = "bash -c 'cd $BUNDLE_PATH && find \"$(pwd -P)\" -maxdepth 2 -type d -name artifacts | xargs echo -n'"

        artifacts_path = docker_container_run(
                image = args.modelImage,
                command = model_cmd,
                name = SinaraModel.model_container_name,
                remove = True
        )

        docker_container_create(
                image = args.modelImage,
                name = SinaraModel.model_container_name,
        )
        
        shutil.rmtree(args.extractTo)
        Path(args.extractTo).mkdir(parents=True, exist_ok=True)

        docker_copy_from_container(SinaraModel.model_container_name, src_path=artifacts_path, dest_path=args.extractTo)
        print(f"Artifacts extracted from {args.modelImage} to {args.extractTo}")
