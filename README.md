## SinaraML Framework is a framework for creating and operating MLOps platforms
From the first sight of a Data Scientist with Sinara to receiving the first Docker image with a model accessible via REST, it will take 15 minutes only.

SinaraML Framework provides Sinara Server, Sinara Storage, Sinara Lib, Sinara Step Template, Sinara Tools to the Data Scientist.

- **SinaraML Server** is a Jupyter Server, with all the necessary libraries for working with data and training models. SinaraML provides three Basic Servers for different purposes — classic ML, computer vision (CV) and natural language processing (NLP).
- **SinaraML Storage** is a long-term storage where ML pipeline stored input and output entities. Depending on infrastructure Sinara Storage can be implemented based on S3, HDFS protocols or local disk.
- **SinaraML Spark** (pandas_api) is a effective and uniform way to work with big data sets using Apache Spark. Pandas_api gives Apache Spark's effectivenes and familiar pandas datasets functions.
- **SinaraML Lib** is a compact library that contains everything you need to create ML pipelines, for data preparation and versioning, model versioning and serving.
- **SinaraML Step Template** is a component template for creating a SinaraML Step — an ML pipeline step. The ML pipeline consists of several steps. Each step based on this template.
- **SinaraML CLI** is a number of CLI tools for creating, deleting, stopping and starting a Sinara Server, creating docker images from BentoServices created by ML pipelines, ML pipelines management, visualization etc.
- **SinaraML Basic** is a preconfigured personal MLOps platform working on desktop, remote virtual machine which can be located on-prem or on clouds like Google Collab/DataProc + Google Objecs, Azure DataBricks + Azure Blobs, Yandex DataSphere/DataProc + S3 etc.
- **SinaraML Customizable Infra** is a way to customize orchestration of Sinara Server, Sinara Storage and Sinara Spark for integration with your infrastructure (Git, Docker repos, authentication and authorization methods including Active Directory).
- **SinaraML Customizable Dev Process** is a way to configure Sinara Template and Sinara Step for your development process.
- **SinaraML Examples** is a library of ready to use configurable ML pipelines can be customized for your needs.
- [**SinaraML Book**](https://sinara-definitive-guide.readthedocs.io/en/latest/) allows you to dive deeply into the development of ML products with SinaraML examples.

To start you off, go to [**Getting started page**](https://github.com/4-DS/sinara-tutorials/wiki/Getting-started) to try **SinaraML Tutorials**

# Installation
To install SinaraML CLI into your environment, run:
```
pip install sinaraml
```
Reload shell or reboot your machine after installation to enable CLI commands

# Quick Start
Commands start with the keyword sinara (similar to git, docker, kubectl)<br>
If a command call is made without a mandatory parameter, help is displayed on the available parameters and methods of calling the command, for example:

```
sinara server create
```
```
sinara server start
```

Or, for a remote VM platform:
```
sinara server create --platform remote_vm
```
```
sinara server start
```
To remove a server, run:
```
sinara server remove
```