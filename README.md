# Cluster and Cloud Computing Project


## CouchDB Deployment

Requires Python 3.5+.

To deploy, call

```
./automation/deploy.py --nodes <num of nodes> --size <vol size> --type <instance type>
```

Note: the SSH private key can either be placed at `~/.ssh/ccc-project`
or supplied in the `CCC_PRIVATE_KEY` environmental variable. This can be done
by prefixing the below call with `CCC_PRIVATE_KEY=<path-to-key>`.

For example, to generate 4 instances of type `m1.medium`, each with a 50gb volume attached:

```
./automation/deploy.py --nodes 4 --size 50 --type m1.medium
```

The deployment script will take some time to run, as it is spinning up
instances, installing packages, and compiling configuring CouchCB. For example,
the above deployment takes about 26 minutes to complete.

The final result will be `n` instances set up in a CouchDB cluster. Each instance
will have a volume attached at `/mnt` (`/dev/vdb/`) that contains the CouchDB
databases. This volume will persist if the instance is terminated, and can
be reattached to a new instance if required.

The script will output the admin links for each node, and they can be accessed using the
admin username and username set in `automation/playbook/roles/cluster/vars/main.yml`.

