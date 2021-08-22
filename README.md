# PWP SUMMER 2021
# GAMESCORESERVICE
# Group information
* Student 1. Petteri Valli pvalli@paju.oulu.fi
* Student 2. Mirva Luukkainen miluukka@paju.oulu.fi


# Preface

The GameScoreService API is developed under Python 3.9.x and it's recommended to have at least Python 3.3 to have the necessary tools included. The API uses SQLite 3 database engine and Flask framework with SQLAlchemy toolkit.

The instructions shown in this file apply on Linux based environments.


# Preparations

You might want to run the API in a virtual environment and to create it, use the following command line:  
```python3 -m venv gss-env```

Then activate the newly created virtual environment:  
```source gss-env/bin/activate```

Change your current working directory into project's directory (GameScoreService) for the next steps.


# Installation

Exact requirements are listed in the requirements.txt file, which can be given to the pip command:  
```pip install -r requirements.txt```

The project can then be installed with the following command:  
```pip install -e .```


# Running

## Preparations

If you haven't activated the virtual Python environment (see the previous steps), do it now.

Couple environment variables need to be set. It can be made with:  
```source setup_flask_env```

Now you can initialize a new empty database if you haven't made it before:  
```flask init-db```


## Optional Database Populating

To populate a newly created database with some test data (optional step):  
```flask populate-db```


## Launching the API

To run the API, just use the following command:  
```flask run```

Or to set the env variables and launch the API at one go:  
```source run_gss```


## Accessing the API

# Enrty Point

The API is available at /api/ URI on the system you run it. By default it opens in the port 5000.

When running both server and client on the same machine, it can be found from:  
```http://localhost:5000/api/```


# Testing

## Preparations

Provided test scripts require installation of the *pytest* tool.

Execute the following lines when your virtual environment is active:  
```
pip install pytest
pip install pytest-cov
```

## Running Tests

### Basic Testing

To run all tests, just launch *pytest* in the project directory:  
```pytest```

Or to test only the database:  
```pytest tests/db_test.py```

And to test the API/resources only:  
```pytest tests/api_test.py```

### Coverage Reports

More detailed coverage reports can be generated with the *coverage* plugin:  
```pytest --cov-report term-missing --cov=gamescoreservice```

### Revealed Issues

Functional testing was important part of the development, and it revealed few issues on the implementation. Main issues were with Put methods in resource classes. They weren't implemented for all resources and had some missing checks.


# Client

## About

An example client that uses the API can be found from:  
[GSS Submitter](https://github.com/petvalli/GSS_Submitter)

It is coded in [Hollywood](https://www.hollywood-mal.com/index.html) 9.0, which is a Lua based scripting language, but which also offers options to compile scripts as applets that can be run with the [Hollywood Player](https://www.hollywood-mal.com/download.html) application or even as stand-alone executables for about 15 different platforms.

## Requirements

- [RapaGUI plugin](https://www.hollywood-mal.com/download.html) (not needed on Android)
- [hURL plugin](https://www.hollywood-mal.com/download.html)
- On Linux platforms: OpenSSL 1.0.x (1.1.x won't work)
- Operating system specific requirements can be seen [here](https://www.hollywood-mal.com/docs/html/hollywood/Requirements_.html)

**Note:** When running provided [pre-compiled executables](https://github.com/petvalli/GSS_Submitter/releases/tag/v1.0), the plugins are linked in the executable files and installation of them is not required!

## Running

There are three options to run the client application.

1. If you have the Hollywood development environment installed, just use the Hollywood interpreter to run the script file:  
```hollywood gss_submitter.hws```
2. Run a compiled applet in Hollywood Player on any of the supported platforms (plugin installation may vary depeding of the platform. For example, on Android it must be placed in the Hollywood/Plugins/ directory found on your device's internal storage or SD card after installation of the player).
3. Run a [pre-compiled executable](https://github.com/petvalli/GSS_Submitter/releases/tag/v1.0) (provided for Windows (x64) and Linux (x64/GTK3) in this example project), this is the easiest solution. Note that you might need to give the execute permission for the downloaded file.

## Configuring

After launching the application, configuration options can be found from the *File/Settings...* drop-down menu entry. The API server address, entry point path, and user (player) credentials can be changed from there.

## Usage

Click the *Home* button to access the API entry point, and then select the next action from control buttons at the bottom. Resource items can be accessed by single-clicking them on the *Items* list and the *Parent* button takes you back to the previous resource in the hierarchy tree.

User (player) specific actions do use the configured player information. Adding a new player will try to add the player with the configured information, as well as adding or editing scores.
