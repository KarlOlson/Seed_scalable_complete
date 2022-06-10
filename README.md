Internet Emulator
---

The objective of the SEED-Emulator project is to help create emulators of 
the Internet. These emulators are for educational uses, and they can be
used as the platform for designing hands-on lab exercises for various subjects,
including cybersecurity, networking, etc.

The project provides essential elements of the Internet (as Python classes), including 
Internet exchanges, autonomous systems, BGP routers, DNS infrastructure, 
a variety of services. Users can use these elements as the building blocks
to build their emulation programmatically. The output of the program 
is a set of docker container folders/files. When these containers are built and 
started, they form a small-size Internet. New building blocks are being added,
including Blockchain, Botnet, and many other useful elements of the Internet. 

![The Web UI](docs/assets/web-ui.png)

## Table of Contents

-  [Getting Started](#getting-started)
-  [Documentation](#documentation)
-  [Contributing](#contributing)
-  [License](#license)

## Changes to base SEED Simulator

Note this is currently deployed in the base SEED environment only and not converted to the cloudlab deployment yet. You should be able to deploy 60-ish nodes on a laptop that has dedicated 8GB of RAM to the environment. 

1. Edited `docker.py` compiler lines `832-837` to add ganache configuration to `ix100`. `ix100` is the base internet exchange and host for the blockchain. Ganache is listening on `10.100.0.100:8545` on this device.
2. Edited `docker.py` compiler lines `851-860` to add base image configuration to each docker device in the network. This includes all software and packages necessary to run blockchain, smart contract and proxy actions.
3. Added `.env` file of 200 pre-made blockchain accounts representing ASNs 0-199 to https://github.com/KarlOlson/bgp_smart_contracts.git in the `/src` directory. This file is used to comply with Greg's account lookup procedures for the smart contracts.
4. Added `accounts.txt` file to `/src` directory to have easily parsable file of accounts. This contains same info as `.env` file, but is space separated.
5. Added `solc_ver_install.py` file to `/src` to pre-install compatability requirements for greg's smart contract. This is installed during docker build now. I did not delete the original from the `compile.py` in order to allow compatability with internet connected systems and completeness of programs. Python will detect installed and skip this in the `compile.py` file.
6. When running `deploy.py` the contract address generated is deterministic and is pre-loaded into the `.env` file. No editing necessary.
7. Added `account_script.py` to `/src`. Running this on `ix100` will deploy the specified ASNs and prefix's to the smart contract. See Account Deployment section for more detail on operation.
8. Added `proxy.py` to `/src`. This is slightly different from the EVE environment in that it works by listening on all local interfaces rather than via a pass-through proxy. 

## Getting Started

To get started with the emulator, install docker, docker-compose, and python3. Then, take a look at the [examples/](./examples/) folder for examples. Detailed explanation is provided in the README file, as well as in the comments of the code. To run an example:

1. Pick an example, say `A00-simple-peering`. 
2. Add `seedemu` to `PYTHONPATH`. This can be done by running `source development.env` under the project root directory.
3. Build the emulation. For this example, cd to `examples/A00-simple-peering/`, and run `python3 ./simple-peering.py`. The container files will be created inside the `output/` folder. For some examples, such as `B02-mini-internet-with-dns`, they depend on other examples, so you need to run those examples first. This is part of our component design.
4. Build and run the containers. First `cd output/`, then do `docker-compose build && docker-compose up`. The emulator will start running. Give it a minute or two (or longer if your emulator is large) to let the routers do their jobs.
5. Optionally, start the seedemu web client. Open a new terminal window, navigate to the project root directory, cd to `client/`, and run `docker-compose build && docker-compose up`. Then point your browser to http://127.0.0.1:8080/map.html, and you will see the entire emulator. Use the filter box if you want to see the packet flow.
6. It doesn't quite appear that ganache is fully automated to start yet and seems like I have to manually enable it one the environment launches. Go into the seed web client, click on the `ix100` device and then click `connect`. This will bring up the command prompt for that device. Deploy ganache by entering `$ ganache -a 200 -p 8545 -h 10.100.0.100 --deterministic`. Optionally, you can add `--database.dbPath /ganache` if you want to store and maintain the updates on the chain. I typically dont. 
7. Establish the contract and the initial conditions by running `$python3 compile.py` followed by `python3 deploy.py ACCOUNT0`. Once this is setup, you can run `account_script.py` to bulk deploy ASNs and Prefix's to the contract. Within here you can specify the ASNs you want authorized for the chain by defining line 16 values. So if you pick `asn_number=[151,152]` as the values, this will load the blockchain by assigning those ASNs to Account 151 and Account 152 along with their prefixes: 10.151.0.0/24 and 10.152.0.0/24. Those routers will then have to validate their actions on the chain when advertising. 

## Known issues/To be worked.

1. When deploying the seed environment, the `ix100` start script does not seem to autoload the blockchain and maintain it live. When I connect, it does not seem to be running and must be manually started.
2. I have not automated the deployment of the blockchain configuration into the docker build script yet...trying to determine if that is the best approach or if a little bit of automated manual effort is better.
3. The proxy is not autoloaded currently. When I manually load it goes into listening but does not seem to capture any traffic or begin chain validation. Not sure why at the moment.
4. Looks like when deploying larger ASN counts that everything begins at 150 and counts upward. So the first 150 ganache accounts don't really provide any value at the moment. Not an issue, but something to be aware of. 

## Documentation

Documentation is in progress inside the [docs/](./docs/) folder.

## Contributing

Contributions to SEED-Emulator are always welcome. For contribution guidelines, please see [CONTRIBUTING](./CONTRIBUTING.md).

## License

The software is licensed under the GNU General Public License v3.0 license, with copyright by The SEED-Emulator Developers (see [LICENSE](./LICENSE.txt)).
