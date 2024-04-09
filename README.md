# env2sif

[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/tron-bioinformatics/env2sif)](https://github.com/TRON-Bioinformatics/env2sif/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)



## Introduction  

**env2sif** is a tool made to alleviate creation and editing of Singularity images on a HPC servers where users do not have sudo rights.

## Tool summary 

This tool enables you to:
- create conda or python virtual environments based on environment scripts (yml for conda, txt for python)
- define operating system and version you wish to build your image upon (Ubuntu, Debian, CentOS, Alpine)
- define conda and python versions you wish to install in your image
- add packages to an existing conda/python image in a form of yml/txt file or comma separated list (e.g. pandas,numpy)
- delete packages from an existing conda/python in a form of comma separated list (e.g. pandas,numpy)

## Usage 

### Software requirements 

Requirements: 

- `python 3`
- `singularity-ce >= 3.10.0`  
- `--fakeroot` rights for Singularity (reed more about fakeroot and giving fakeroot rights [here](https://docs.sylabs.io/guides/3.10/user-guide/fakeroot.html))

### Input files 

There are three types of input files supported by this tool:
 
`environment.yml`: 

```
name: <environment_name>
channels:
  - <channel1_name>
  - <channel2_name>
dependencies:
  - <package1>=<package1_version>
  - <package2>=<package2_version>
```

`environment.txt`: 

```
<package1>==<package1_version>
<package2>==<package2_version>
```

`image.sif`
> **Note**
> Input singularity image that you wish to edit. It is crucial not to forget .sif extension in order for the tool to recognize the input type.  


### How to run the tool 

If you wish to create virtual environment from yml/txt file, download the tool and run it as follows...

```bash
$ python env2sif.py --input_file <YOUR_INPUT_YML_OR_TXT_FILE> --output_file <YOUR_OUTPUT_SIF_FILE> --environment_type <CONDA_OR_PYTHON>
```

If you wish to edit already existing singularity image, download the tool and run it as follows...
```bash
$ python env2sif.py --input_file <YOUR_INPUT_SIF_FILE> --output_file <YOUR_INPUT_SIF_FILE> --environment_type <CONDA_OR_PYTHON> --add <YML/TXT_FILE_OR_PACKAGE_LIST> --delete <PACKAGE_LIST>
```

If you wish to edit already existing singularity image and save the resulting environment in another image, download the tool and run it as follows...
```bash
$ python env2sif.py --input_file <YOUR_INPUT_SIF_FILE> --output_file <YOUR_OUTPUT_SIF_FILE> --environment_type <CONDA_OR_PYTHON> --add <YML/TXT_FILE_OR_PACKAGE_LIST> --delete <PACKAGE_LIST>
```

If you wish to check installed System, Conda, Python versions and installed Conda/Python packages in created image, run the following...
```bash
$ sigularity test <SIF_FILE>
```

See help message for all of the available options when running the pipeline: 

```
$ python env2sif.py --help
usage: env2sif.py [-h] -i INPUT_FILE -o OUTPUT_FILE -e ENVIRONMENT_TYPE [-a ADD] [-d DELETE] [-t TEMPLATE] [-s SYSTEM] [-v SYSTEM_VERSION] [-r] [-n]
                  [-m MICROMAMBA_VERSION] [-p PYTHON_VERSION]

Create Singularity container from environment file or edit existing image

options:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input_file INPUT_FILE
                        Specify environment file (.yml for conda, .txt for python) or an existing .sif image that you would like to edit
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Specify output container file path
  -e ENVIRONMENT_TYPE, --environment_type ENVIRONMENT_TYPE
                        Choose between conda or python environment build
  -a ADD, --add ADD     Add new packages to an existing environment in a form of .yml file (.txt for python) or comma separated list of packages
  -d DELETE, --delete DELETE
                        Delete packages from an existing environment in a form of comma separated list of packages
  -t TEMPLATE, --template TEMPLATE
                        Specify building template file (default ../templates/conda_py_template.def)
  -s SYSTEM, --system SYSTEM
                        Specify container system from CentOS, Ubuntu, Debian or Alpine (default Alpine)
  -v SYSTEM_VERSION, --system_version SYSTEM_VERSION
                        Specify container system version (default Ubuntu focal, CentOS 8, Debian bookworm and Alpine 3.18)
  -r, --system_remove   Remove system image with installed python or micromamba versions
  -n, --not_slim        Do not install slim version of the system
  -m MICROMAMBA_VERSION, --micromamba_version MICROMAMBA_VERSION
                        Specify container micromamba version that will install conda environment (default 1.5.7)
  -p PYTHON_VERSION, --python_version PYTHON_VERSION
                        Specify container python version (default 3.12.2)
```

## Tool output 

`image.sif`
> **Note**
> System images with installed conda and python versions are saved in ../images folder and reused in future builds. This ensures better reproducibility since public repositories might change their availability. You can disable saving system images by adding -r/--system_remove parameter when using env2sif.py.

## Authors & Acknowledgements 

The env2sif pipeline was originally developed by Ivan Baksic at [TRON - Translational Oncology at the Medical Center of the Johannes Gutenberg University Mainz gGmbH (non-profit)](https://tron-mainz.de/).

Maintenance is now lead by Ivan Baksic. 

Main developers: 

- [Ivan Baksic](mailto:Ivan.Baksic@TrOn-Mainz.DE)   


## Contributing & Support 

If you would like to contribute to this tool, please see the [contributing guidelines](CONTRIBUTING.md). 

Please report issues using the [issue tracker of GitHub](https://github.com/TRON-Bioinformatics/env2sif/issues). 

## Citations

An list of references for the tools used by the tool can be found in the [`CITATIONS.md`](CITATIONS.md) file. 

## CHANGELOG 

- [CHANGELOG](CHANGELOG.md)
