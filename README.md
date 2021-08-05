# PWP SUMMER 2021
# GAMESCORESERVICE
# Group information
* Student 1. Petteri Valli pvalli@paju.oulu.fi
* Student 2. Mirva Luukkainen miluukka@paju.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__


# Preface

The GameScoreService API is developed under Python 3.9.x and it's recommended to have at least Python 3.3 to have the necessary tools included. The API uses SQLite 3 as its database engine.

The instructions shown in this file apply on Linux based environments.


# Preparations

You might want to run the API in a virtual environment and to create it, use the following command line:
```python3 -m venv gamescoreservice-env```

Then activate the newly created virtual environment:
```source gamescoreservice-env/bin/activate```

Change your current working directory into project's directory for the next steps.


# Installation

Exact requirements are listed in the requirements.txt file, which can be given to the pip command:
```pip install -r requirements.txt```

The project can be installed with the following command:
```pip install -e .```


# Running

## Preparations

If you haven't activated the virtual Python environment (see the previous steps), do it now.

Couple environment variables need to be set. It can be made with:
```source setup_flask_env```

Now you can initialize a new empty database if you haven't made it before:
```flask init-db```


## Optional Step for Testing

To populate a newly created database with some test data:
```flask populate-db```


## Launching the API

To run the API, just use the following command:
```flask run```
