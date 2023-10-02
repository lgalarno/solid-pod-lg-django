# **Solid Pod LG** #

This is the repository for the Solid Pod LG

### Note: this is a preliminary attempt to interact with Solid Pods using Python and Django ###
### This is small project with nothing guaranteed to work; no unit tests; minimal exception handling, etc ###

### Requirements: ###
1. Python 3 (development environment using >= 3.11)
2. Django 4 (development environment using >= 4.2)
3. Packages in requirements.txt


### The core features offered by SOLID LG: ###

1. Login to Solid pod providers
   - Supported:
      - CommunitySolidServer (https://github.com/CommunitySolidServer/CommunitySolidServer)
      - node-solid-server (https://github.com/nodeSolidServer/node-solid-server)
   - Unupported: Inrupt Solid Pods 
2. View ttl files, folders and other files
3. Download files (not ttl)
4. Upload Files
5. Delete Files

### Installation Instructions ###

* Clone the repository
* Create Python 3 virtual environment
* Create a virtualenv using Python 3
* pip install –r requirements.txt
* Create .env file in the src folder which should contain:

  - ALLOWED_HOSTS
     - Comma-separated list of domains (no spaces), e.g. 'example.com,example.net'. Must be set when DEBUG=1:
     - example: '127.0.0.1,localhost,example.com'
  - OID_CALLBACK_URI
     - example: "http://localhost:8000/oidc/callback" (see the oidc urls.py file)
  - CLIENT_NAME
    - example: "SolidPodLG"
  - CLIENT_CONTACT
    - email address
  - CLIENT_URL
    - example: '127.0.0.1:8000/'

* During development, use the database: db.sqlite3. Otherwise, put the DB config in the .env file:
    - DATABASE_ENGINE='*****'
    - DATABASE_HOST='*****'
    - DATABASE_USER='*****'
    - DATABASE_PASSWORD='****'
    - DATABASE_NAME='****'
    - DATABASE_PORT='*****'

### Credit
The project [solid-file-python/twonote](https://github.com/twonote/solid-file-python) was modified to be used as the crud api
and [Otto-AA/solid-flask](https://github.com/Otto-AA/solid-flask) was inspirational for the authentication system.
Thanks to the original authors.
