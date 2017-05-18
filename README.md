# Cluster and Cloud Computing Project


## CouchDB on NeCTAR
### Prerequisites
Requires Python 3.5+. It is recommended that you make a virtual environment
and install prerequisites before proceeding. This can be done with the following:

```
mkvirtualenv -p python3 ccc-project
workon ccc-project
pip install -r requirements.txt
```

### Deployment
Before deployment, set the following two environmental variables:

```
export NECTAR_ACCESS_KEY = <nectar access key id>
export NECTAR_SECRET_KEY = <nectar secret access key>
```

To deploy, call

```
./deployment/deploy.py --nodes <num of nodes> --size <vol size> --type <instance type>
```

Note: the SSH private key can either be placed at `~/.ssh/ccc-project`
or supplied in the `CCC_PRIVATE_KEY` environmental variable. This can be done
by prefixing the below call with `CCC_PRIVATE_KEY=<path-to-key>`.

For example, to generate 4 instances of type `m1.medium`, each with a 50gb volume attached:

```
./deployment/deploy.py --nodes 4 --size 50 --type m1.medium
```

The deployment script will take some time to run, as it is spinning up
instances, installing packages, and compiling configuring CouchCB. For example,
the above deployment takes about 26 minutes to complete.

The final result will be `n` instances set up in a CouchDB cluster. Each instance
will have a volume attached at `/mnt` (`/dev/vdb/`) that contains the CouchDB
databases. This volume will persist if the instance is terminated, and can
be reattached to a new instance if required.

The script will output the admin links for each node, and they can be accessed using the
admin username and username set in `deployment/playbook/roles/cluster/vars/main.yml`.

### Website
To build the website, you need npm. Homebrew is recommended for installing it on Mac.
Use `brew install node`. On Windows, use the installer from [http://nodejs.org/](http://nodejs.org/).
In both cases, you can test the installation with `npm -v`, which should return the
version number.

Once you have npm, navigate to `website/`, and run `npm install` to install required
packages.

You can then build by running `gulp`. This will run the tasks as detailed in `gulpfile.js`,
with the output in `website/build/`. The contents of this folder than then be deployed
where required.

For development, run `gulp dev`. This will build the source, as above, but also start
BrowserSync, which will automatically rebuild and reload your browser when it detects
changes to any source files. Note that it'll automatically load the root of `build/`,
so you may have to navigate to the relevant file manually.

## Authors
- David Barrell ([Github](https://github.com/dabarrell/))
- Bobby Koteski ([Github](https://github.com/bkot88))
- Steve Dang ([Github](https://github.com/thanhdang1109))
- Annie Zhou ([Github](https://github.com/anya-z))

