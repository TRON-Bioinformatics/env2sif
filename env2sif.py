#!/usr/bin/env python

from argparse import ArgumentParser
from subprocess import check_call
import os
import shutil
import urllib.request
import tarfile


def download_micromamba(micromamba_version, micromamba_path, cwd):
    
    link = os.path.join("https://micromamba.snakepit.net/api/micromamba/linux-64/", micromamba_version)
    
    try:
        urllib.request.urlretrieve(link, micromamba_path)
        with tarfile.open(micromamba_path, "r") as tf:
            print("Opened tarfile")
            tf.extractall(path=cwd)
            print("All files extracted")
        os.remove(micromamba_path)
    except:
        print("MICROMAMBA NOT FOUND!!! CHECK YOUR VERSION!")
        exit()


def create_docker_name(environment_type, system, system_version, not_slim, micromamba_version, python_version):
    docker_name = ""
    if system == "Alpine":
        print("NO SLIM VERSION OF ALPINE!")
        if environment_type == "conda":
            docker_name = "mambaorg/micromamba:" + micromamba_version + "-alpine" + system_version
        elif environment_type == "python":
            docker_name = "python:" + python_version + "-alpine" + system_version

    elif not_slim and environment_type == "conda" and system not in ["CentOS", "Alpine"]:
        docker_name = "mambaorg/micromamba:" + micromamba_version + "-" + system_version

    elif not_slim and environment_type == "python" and system not in ["CentOS", "Alpine"]:
        docker_name = "python:" + python_version + "-" + system_version

    elif not not_slim and environment_type == "conda" and system not in ["CentOS", "Alpine"]:
        docker_name = "mambaorg/micromamba:" + micromamba_version + "-" + system_version + "-slim"

    elif not not_slim and environment_type == "python" and system not in ["CentOS", "Alpine"]:
        docker_name = "python:" + python_version + "-slim-" + system_version

    return docker_name


def build_singularity(output_file):
    cwd = os.getcwd()
    temp_def_path = os.path.join(cwd, "temp_def.def")
    try:
        check_call([
            "singularity",
            "build",
            "--fakeroot",
            "--disable-cache",
            "--force",
            output_file,
            temp_def_path,
            ])
    except:
        print("Problem with running Singularity! Check your fakeroot rights!")
        raise Exception()
    os.remove(temp_def_path)


def test_singularity(image):
    try:
        check_call([
            "singularity",
            "test",
            image
            ])
    except:
        print("Problem with the following image: " + image)


def create_docker_image(input_template, docker_name, output_file):
    # edit template files
    with open(input_template, "r") as template_read, open ("temp_def.def", "w") as temp_def_write:
        edit_template = template_read.read()
        edit_template = edit_template.format(docker_name = docker_name)
        temp_def_write.write(edit_template)
    # run singularity build
    build_singularity(output_file)


def create_system_image(input_template, environment_type, system, system_version, output_file, python_version = "", python_version_list = "", source = True, micromamba_path = ""):

    docker_name = system.lower() + ":" + system_version
    
    # edit template files
    with open(input_template, "r") as template_read, open ("temp_def.def", "w") as temp_def_write:
        edit_template = template_read.read()
        
        if environment_type == "conda":
            edit_template = edit_template.format(docker_name = docker_name, 
                                                 micromamba_path = micromamba_path)
        
        elif environment_type == "python" and system == "Ubuntu" and not source:
            # we need to detect lower versions of python in order to find correct pip installation in external repository
            if int(python_version_list[0]) == 3 and int(python_version_list[1]) >= 7:
                python_pip_version_status = "new"
            else:
                python_pip_version_status = "old"

            # installation of older versions of python have problems with module installation
            # this is a workaround
            if int(python_version_list[1]) < 6:
                py3_version = "old"
            else:
                py3_version = "new"

            edit_template = edit_template.format(docker_name = docker_name,
                                                 python_version = python_version,
                                                 python_pip_version_status = python_pip_version_status,
                                                 py2_or_py3 = python_version_list[0],
                                                 py3_version = py3_version)

        elif environment_type == "python":
            
            # only some distribution of python come with pip preinstalled
            if int(python_version_list[0]) == 3 and int(python_version_list[1]) >= 6:
                python_pip_version_status = "pip"
            else:
                # TODO: install pip on source distributions that do not contain it
                python_pip_version_status = "no_pip"
                print("PLEASE SELECT UBUNTU SYSTEM AND PYTHON VERSIONS THAT COME WITH PIP:\n2.7.18\n3.5.10\n>=3.6\nOR ANY OTHER SYSTEM AND PYTHON VERSIONS THAT COME WITH PIP:\n>=3.6")
                exit()
            
            # newer versions of Ubunt and Debian do not support libreadline-gplv2-dev
            if (system == "Debian" and system_version in ["bullseye", "bookworm", "trixie"]) or (system == "Ubuntu" and system_version in ["noble", "jammy"]):
                libreadline_support = "None"
            else:
                libreadline_support = "Supported"
            
            # centos template is different from other sytem templates
            if system == "CentOS":
                edit_template = edit_template.format(docker_name = docker_name,
                                                     python_version = python_version,
                                                     system_version = system_version)

            else:
                edit_template = edit_template.format(docker_name = docker_name,
                                                     python_version = python_version,
                                                     python_pip_version_status = python_pip_version_status,
                                                     python_pip_version = python_pip_version_status,
                                                     libreadline_support = libreadline_support)

        
        else:
            print("ERROR! --environment_type (-e) NOT CORRECT!")
            exit()
        temp_def_write.write(edit_template)
    # run singularity build
    build_singularity(output_file)


def create_conda_py_image(input_template, image_path, environment_type, output_file, env_file, python_version_list):
    # edit template files
    with open(input_template, "r") as template_read, open ("temp_def.def", "w") as temp_def_write, open(env_file, "r") as env_file_read:
        edit_template = template_read.read()
        env_file_line = env_file_read.readline()

        # extract environment name from the first row of environment file if possible and check if it matches environment type
        try:
            env_name = env_file_line.split(":")[1].strip()
        except:
            env_name = ""

        if env_file_line == "":
            print("ERROR! CHECK YOUR yml/txt FILE!")
            exit()
        elif (environment_type == "python" and env_name != "") or (environment_type == "conda" and env_name == ""):
            print("ERROR! --environment_type (-e) OR yml ENVIRONMET NAME IS NOT CORRECT!")
            exit()
        
        # in newer versions of python venv is created with venv module, in older with virtualenv module
        if int(python_version_list[1]) < 6:
            py3_version = "old"
        else:
            py3_version = "new"

        edit_template = edit_template.format(system_image = image_path, 
                                             env_input = env_file, 
                                             env_name = env_name,
                                             conda_or_py = environment_type,
                                             py2_or_py3 = python_version_list[0],
                                             py3_version = py3_version)

        temp_def_write.write(edit_template)
    # run singularity build
    build_singularity(output_file)


def edit_conda_py_image(input_template, image_path, environment_type, output_file, add_or_delete, env_file, file_or_list = "", packages = ""):
    # edit template files
    with open(input_template, "r") as template_read, open ("temp_def.def", "w") as temp_def_write:
        edit_template = template_read.read()
        edit_template = edit_template.format(input_image = image_path, 
                                             env_input = env_file,
                                             conda_or_py = environment_type,
                                             edit = add_or_delete,
                                             file_or_list = file_or_list,
                                             packages = packages)
        temp_def_write.write(edit_template)
    # run singularity build
    build_singularity(output_file)


def env2sif(input_file, output_file, environment_type, add, delete, template, system, system_version, system_remove, not_slim, micromamba_version, python_version):

    # add default system vaersions to systems
    if system == "Ubuntu" and system_version == "None":
        system_version = "focal"
    elif system == "CentOS" and system_version == "None":
        system_version = "8"
    elif system == "Debian" and system_version == "None":
        system_version = "bookworm"
    elif system == "Alpine" and system_version == "None":
        system_version = "3.18"
        not_slim = True
    elif system == "Alpine":
        not_slim = True

    # currently only python can be installed on CentOS
    # TODO: enable conda environment on CentOS
    if system == "CentOS" and environment_type == "conda":
        print("CURRENTLY ONLY PYTHON ENVIRONMENT CAN BE INSTALLED ON CentOS SYSTEM! TRY ANOTHER SYSTEM!")
        exit()

    script_path = os.path.realpath(__file__)
    absoulute_path = os.path.dirname(script_path)
    
    template = os.path.join(absoulute_path, template)
    edit_template = os.path.join(absoulute_path, "templates/edit_template.def")

    if environment_type == "conda":
        folder_name = "micromamba" + micromamba_version
        python_version_list = ["0","0"]
    elif environment_type == "python":
        folder_name = "python" + python_version
        python_version_list = python_version.split(".")
    folder_path =  os.path.join(absoulute_path, "images", folder_name)

    
    image_name = folder_name + "_" + system + system_version.capitalize() + ".sif"
    image_path =  os.path.join(folder_path, image_name)

    image_slim_name = folder_name + "_slim_" + system + system_version.capitalize() + ".sif"
    image_slim_path =  os.path.join(folder_path, image_slim_name)

    system_template_name = "system_" + environment_type + "_template.def"
    system_template_path = os.path.join(absoulute_path, "templates", system_template_name)

    docker_template_name = "docker_" + environment_type + "_template.def"
    docker_template_path = os.path.join(absoulute_path, "templates", docker_template_name)


    # check input file type and run edit image if the input is singularity image
    input_type = os.path.basename(input_file).split(".")[1]
    if input_type == "sif" and (add != "None" or delete != "None"):
        # create temporary empty dummy file and pass it as environment file in the case when packages are added/deleted 
        dummy_file = open("dummy_file", "w")
        dummy_file.close()
        cwd = os.getcwd()
        dummy_file_path = os.path.join(cwd, "dummy_file")
        input_file_path = os.path.join(cwd, input_file)
        
        # case when added packes are passed in a file
        if add !="None" and os.path.isfile(add):
            edit_conda_py_image(edit_template, input_file_path, environment_type, output_file, "add", env_file = add, file_or_list = "file")
        # case when added packages are passed as comma separated list
        elif add !="None" and not os.path.isfile(add):
            packages = add.replace(",", " ")
            edit_conda_py_image(edit_template, input_file_path, environment_type, output_file, "add", env_file = dummy_file_path, file_or_list = "list", packages = packages)
        
        # if statement because we want to enable both addition and deletion of packages in the same command
        if delete !="None":
            packages = delete.replace(",", " ")
            edit_conda_py_image(edit_template, input_file_path, environment_type, output_file, "delete", env_file = dummy_file_path, packages = packages)
        
        os.remove(dummy_file_path)


    elif input_type == "sif" and add == "None" and delete == "None":
        print("ERROR! CHANGE INPUT FILE TYPE OR SUPPLY ADD/DELETE PACKAGES!")
        exit()


    # if the input immage is not sif, create new image file from .yml/.txt input file
    elif os.path.isfile(image_slim_path) and not not_slim:
        print("SYSTEM IMAGE ALREADY EXISTS!")
        test_singularity(image_slim_path)
        create_conda_py_image(template, image_slim_path, environment_type, output_file, env_file = input_file, python_version_list = python_version_list)
        final_image_path = image_slim_path
    
    elif os.path.isfile(image_path) and not_slim:
        print("SYSTEM IMAGE ALREADY EXISTS!")
        test_singularity(image_path)
        create_conda_py_image(template, image_path, environment_type, output_file, env_file = input_file, python_version_list = python_version_list)
        final_image_path = image_path


    else:
        print("NO REQUIERED SYSTEM IMAGE!!! CHECKING DOCKER....")
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        try:
            # if the system image is not installed and --not_slim parameter is not selected, check for slim version on docker
            if not not_slim:
                print("TRYING TO DOWNLOAD SLIM VERSION...")
                final_image_path = image_slim_path
                try:
                    docker_name = create_docker_name(environment_type, system, system_version, not_slim, micromamba_version, python_version)
                    create_docker_image(docker_template_path, docker_name, image_slim_path)
                    create_conda_py_image(template, image_slim_path, environment_type, output_file, env_file = input_file, python_version_list = python_version_list)
                # sometimes environment cannot be installed on slim version (common with python), therefore the removal of unused system image
                except:
                    if os.path.exists(final_image_path):
                        os.remove(final_image_path)
                    raise Exception()
            else:
                raise Exception()
        except:
            # if there is no slim version on docker, try to use normal system image
            print("SLIM VERSION IS NOT SELECTED, DOES NOT EXIST OR COULD NOT BE INSTALLED! CHECKING FOR ALREADY INSTALLED NORMAL SYSTEM IMAGE...")
            if os.path.isfile(image_path):
                test_singularity(image_path)
                create_conda_py_image(template, image_path, environment_type, output_file, env_file = input_file, python_version_list = python_version_list)
                final_image_path = image_path
            else:
                try:
                    print("NORMAL SYSTEM VERSION NOT INSTALLED! CHECKING DOCKER FOR NORMAL VERSION...")
                    docker_name = create_docker_name(environment_type, system, system_version, True, micromamba_version, python_version)
                    create_docker_image(docker_template_path, docker_name, image_path)
                    create_conda_py_image(template, image_path, environment_type, output_file, env_file = input_file, python_version_list = python_version_list)
                    final_image_path = image_path
                # if the system image could not be downloaded from docker, build a custom one
                except:
                    print("COULD NOT DOWNLOAD DOCKER IMAGE! PLEASE CHECK DIFFERENT SYSTEM AND PYTHON/MICROMAMBA COMBINATIONS ON https://hub.docker.com/ BEFORE BUILDING CUSTOM IMAGE!")
                    msg = "ARE YOU SURE YOU WANT TO CONTINUE WITH BUILDING CUSTOM IMAGE?"
                    shall = input("%s (y/N) " % msg).lower() == 'y'
                    
                    if shall:
                        print("BUILDING CUSTOM SYSTEM IMAGE...")
                        
                        try:
                            if environment_type == "conda":
                                # download micromamba executable
                                cwd = os.getcwd()
                                micromamba_path = os.path.join(cwd, "micromamba.tar.bz")
                                micromamba_extracted_path = os.path.join(cwd, "bin/micromamba")
                                download_micromamba(micromamba_version, micromamba_path, cwd)
                                create_system_image(system_template_path, environment_type, system, system_version, image_path, micromamba_path = micromamba_extracted_path)
                                shutil.rmtree(os.path.dirname(micromamba_extracted_path))

                            elif environment_type == "python":
                                # since older versions of ubuntu python are downloaded from ppa deadsnakes archive, they only contain specific releases for each python version
                                # this is done in order to keep images small

                                # detect if python release is the same as the ones in deadsnakes/ppa repository and download selected python version from the repository
                                python_pypa_versions = ["2.7.18", "3.5.10", "3.6.15", "3.7.17", "3.8.18", "3.9.18", " 3.10.13", "3.11.8", "3.12.2", "3.13.0"]
                                if system == "Ubuntu" and python_version in python_pypa_versions:
                                    python_version = python_version_list[0] + "." + python_version_list[1]
                                    python_version_list = python_version.split(".")
                                
                                # take the latest version of python release if user doesn't specify the release version
                                elif system != "Ubuntu" and len(python_version_list) == 2:
                                    latest_py_versions = {"2.0":"2.0.1", "2.1":"2.1.3", "2.2":"2.2.3", "2.3":"2.3.7", "2.4":"2.4.6", "2.5":"2.5.6", "2.6":"2.6.9", "2.7":"2.7.18",
                                                          "3.0":"3.0.1", "3.1":"3.1.5", "3.2":"3.2.6", "3.3":"3.3.7", "3.4":"3.4.10", "3.5":"3.5.10", "3.6":"3.6.15", "3.7":"3.7.17", "3.8":"3.8.19", "3.9":"3.9.19",
                                                          "3.10":"3.10.14", "3.11":"3.11.9", "3.12":"3.12.2", "3.13":"3.13.0"}
                                    python_version = latest_py_versions[python_version]
                                    print("INSTALLING LATEST PYTHON RELEASE FOR SELECTED VERSION: ", python_version)
                                
                                # this is done because listed versions have different folder name in https://www.python.org/ftp/python/ source repository
                                elif python_version in ["2.0.0", "2.1.0", "2.2.0", "2.3.0", "2.4.0", "2.5.0", "2.6.0", "2.7.0", "3.0.0", "3.1.0", "3.2.0"]:
                                    python_version = python_version_list[0] + "." + python_version_list[1]

                                if len(python_version_list) == 1:
                                    print("BE MORE PERCISE ABOUT PYTHON VERSION!")
                                    exit()

                                elif system == "Ubuntu" and len(python_version_list) == 2:
                                    print("INSTALLING LATEST PYTHON RELEASE FOR SELECTED VERSION: ", )
                                    system_no_soruce_template_name = "ubuntu_no_source_python_template.def"
                                    system_no_source_template_path = os.path.join(absoulute_path, "templates", system_no_soruce_template_name)
                                    create_system_image(system_no_source_template_path, environment_type, system, system_version, image_path, python_version, python_version_list, source = False)

                                elif system == "Ubuntu" and len(python_version_list) == 3:
                                    print("PYTHON VERSION WITH SPECIFIED RELEASE! IN ORDER TO MAKE YOUR IMAGE AS SMALL AS POSSIBLE, YOU SHOULD USE PYTHON VERSION WITHOUT STATED RELEASE (e.g. 3.6)! OTHERWISE, PYTHON WILL BE INSTALLED FROM SOURCE!")
                                    print("RELEASES FOR EACH PYTHON VERSION:")
                                    print("2.7 -> 2.7.18\n3.5 -> 3.5.10\n3.6 -> 3.6.15\n3.7 -> 3.7.17\n3.8 -> 3.8.18\n3.9 -> 3.9.18\n3.10 -> 3.10.13\n3.11 -> 3.11.8\n3.12 -> 3.12.2\n3.13 -> 3.13.0")
                                    msg = "ARE YOU SURE YOU WANT TO CONTINUE WITH BUILDING CUSTOM IMAGE FROM SOURCE?"
                                    shall = input("%s (y/N) " % msg).lower() == 'y'
                                    
                                    if shall:
                                        create_system_image(system_template_path, environment_type, system, system_version, image_path, python_version, python_version_list)
                                    else:
                                        exit()
                                
                                elif len(python_version_list) >= 4:
                                    print("WRONG PYTHON VERSION!")
                                    exit()

                                # installing python from source on CentOS requieres different commands compared to Ubuntu
                                elif system == "CentOS":
                                    system_template_name = "centos_python_template.def"
                                    system_template_path = os.path.join(absoulute_path, "templates", system_template_name)
                                    create_system_image(system_template_path, environment_type, system, system_version, image_path, python_version, python_version_list)
                    
                                else:
                                    create_system_image(system_template_path, environment_type, system, system_version, image_path, python_version, python_version_list)
                            
                            create_conda_py_image(template, image_path, environment_type, output_file, env_file = input_file, python_version_list = python_version_list)

                        except:
                            # TODO: install python from source on alpine system
                            if system == "Alpine":
                                print("HAVING TROUBLE INSTALLING PYTHON/MICROMAMBA ON ALPINE SYSTEM! PLEASE CHECK DOCKER HUB FOR AVAILABLE VERSION COMBINATIONS!")
                            print("COULD NOT BUILD CUSTOM SYSTEM IMAGE! TRY DIFFERENT SYSTEM AND/OR SYSTEM VERSION! EXITING...")
                    else:
                        exit()
                    
                    final_image_path = image_path

    # remove system image if selected in parameters
    if system_remove and os.path.exists(final_image_path):
        os.remove(final_image_path)

    # remove empty dir of system image if it exists
    if os.path.isdir(folder_path) and not os.listdir(folder_path):
        os.rmdir(folder_path)
    
    # remove temp_def file if it exists
    cwd = os.getcwd()
    temp_def_path = os.path.join(cwd, "temp_def.def")
    if os.path.exists(temp_def_path):
        os.remove(temp_def_path)



def main():
    parser = ArgumentParser(description='Create Singularity container from environment file or edit existing image')

    parser.add_argument("-i", "--input_file", dest="input_file", help="Specify environment file (.yml for conda, .txt for python) or an existing .sif image that you would like to edit", required=True)
    parser.add_argument("-o", "--output_file", dest="output_file", help="Specify output container file path", required=True)
    parser.add_argument("-e", "--environment_type", dest="environment_type", help="Choose between conda or python environment build", required=True)
    parser.add_argument("-a", "--add", dest="add", help="Add new packages to an existing environment in a form of .yml file (.txt for python) or comma separated list of packages", default="None")
    parser.add_argument("-d", "--delete", dest="delete", help="Delete packages from an existing environment in a form of comma separated list of packages", default="None")
    parser.add_argument("-t", "--template", dest="template", help="Specify building template file (default ../templates/conda_py_template.def)", default="templates/conda_py_template.def")
    parser.add_argument("-s", "--system", dest="system", help="Specify container system from CentOS, Ubuntu, Debian or Alpine (default Alpine)", default= "Alpine")
    parser.add_argument("-v", "--system_version", dest="system_version", help="Specify container system version (default Ubuntu focal, CentOS 8, Debian bookworm and Alpine 3.18)", default= "None")
    parser.add_argument("-r", "--system_remove", dest="system_remove", help="Remove system image with installed python or micromamba versions", action='store_true')
    parser.add_argument("-n", "--not_slim", dest="not_slim", help="Do not install slim version of the system", action='store_true')
    parser.add_argument("-m", "--micromamba_version", dest="micromamba_version", help="Specify container micromamba version that will install conda environment (default 1.5.7)", default= "1.5.7")
    parser.add_argument("-p", "--python_version", dest="python_version", help="Specify container python version (default 3.12.2)", default= "3.12.2")
    args = parser.parse_args()

    env2sif(args.input_file, args.output_file, args.environment_type, args.add, args.delete, args.template, args.system, args.system_version, args.system_remove, args.not_slim, args.micromamba_version, args.python_version)
    

if __name__ == "__main__":
    main()
