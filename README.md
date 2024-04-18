<p align="center">
  <img src="https://github.com/4-DS/.github/assets/55787399/edbd76dd-e296-4bde-9cca-c1d902c5504c" height=140 />
</p>

## SinaraML is a lightweight open source framework that simplifies Data Scientist's work and eliminates pain of accompanying engineering routines

Like many others, SinaraML designed as a full-stack MLOps solution that allows Data Scinentist to focus on machine learning code development and takes care of the engineering tasks associated with scaling, reproducibility, model maintenance, data tracking, and experiment management.

But unlike other similar solutions SinaraML is many more. It is next generation MLOps framework incorporated with ready to use MLOps platforms. From one side to work in platform you don't need to setup servers neither you no need cloud provider - you are fully independent. You can start develop you code [just now](https://github.com/4-DS/sinara-tutorials/wiki/Getting-started) on you Windows or Linix desktop or VM. From the other side SinaraML Framework ready for integration to corporate infra to get full-blown enterprise MLOps platform. SinaraML Framework provides abstractions to connect corporate storage (like S3/HDFS), corporate servers for spark clusters (for PandasOnSpark), corporate Git and CI/СD tools and so on. Once written your ML code is fully transferable beetween all of platforms based on SinaraML. So, you can start development on your desktop and continue in the corporate MLOps platform.

SinaraML doesn't require you to learn its own API for reading/writing data, managing experiments, or logging as previous generation platforms require. You don't have to constantly remember tracking or logging tasks by inserting special strings into your ML code. All you need is to insert cell in the beginning of notebooks with inputs and outputs definitions. So the time from the first acquaintance to the launch of the first ML pipeline takes no more than 15 minutes.

SinaraML is a thin wrapper around the technologies of de facto standards in the field of machine learning and data engineering: Python, Jupyter, PandasOnSpark, CUDA, etc. Plus, SinaraML precisely closes the gaps that arise when integrating these technologies. 

SinaraML brings together the best of different worlds:

- Functionality of experiment management solutions such as MLFlow
- Flexibility and simplicity of Jupyter Notebooks for data and ML experiments visualization and logging
- Scalability and power of Spark for data engineering
- Functionaity ML and data pipelines
- Out of the box automatic data versioning and traceability (Data Lineage across whole ML Pipeline)
- Model Serving by Data Scientist. Data scientists build Docker Images with REST interface without special knowledge about Docker, K8s, SinaraML APIs and REST frameworks. The resulting docker images do not require special infrastructure like as K8s or SinaraML servers and can run on any machine with docker installed. Model Versioning does not require special Model Storage
- Out of the box, up to date, carefully selected Python envs for developing both classic ML and Computer Vision models 

SinaraML is lightweight in all its aspects. The SinaraML framework not only addresses the needs of Data Scientists, but also the needs of MLOps engineers. SinaraML has an architecture with minimal operating costs. The platform relies heavily on the stateless servers, and the corporate MLOps platform can be implemented without relational and NoSQL DBMS


To start you off, go to [**Getting started page**](https://github.com/4-DS/sinara-tutorials/wiki/Getting-started) to try **SinaraML Tutorials**

[**SinaraML Book**](https://sinara-definitive-guide.readthedocs.io/en/latest/) allows you to dive deeply into the development of ML products.

# Installation
To install SinaraML CLI into your environment, run:
```
pip install sinaraml
```
Reload shell or reboot your machine after installation to enable CLI commands

# Quick Start
Commands start with the keyword sinara (similar to git, docker, kubectl)<br>
If a command call is made without a mandatory parameter, help is displayed on the available parameters and methods of calling the command, for example
SinaraML server for personal use on desktop
```
sinara server create
```
```
sinara server start
```

Or SinaraML server on remote machine (via ssh):
```
sinara server create --platform remote
```
```
sinara server start
```
To remove a server, run:
```
sinara server remove
```