FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
RUN echo 'exec zsh' > /root/.bashrc
RUN apt-get update && apt-get install -y --no-install-recommends curl dnsutils ipcalc iproute2 iputils-ping jq mtr-tiny nano netcat tcpdump termshark vim-nox zsh
RUN curl -L https://grml.org/zsh/zshrc > /root/.zshrc
RUN apt-get update && apt-get install -y build-essential python3 python3-pip python-dev nodejs git
RUN apt-get install -y npm
RUN pip3 install py-solc-x web3 python-dotenv scapy==2.4.4
RUN npm update -g
RUN npm install -g ganache
RUN npm install -g npm@8.5.3
RUN pip3 install --upgrade pip
RUN pip3 install eth-brownie Flask scapy flask-restful
RUN pip3 install eth-utils
RUN git clone --depth 1 --filter=blob:none --no-checkout https://github.com/KarlOlson/Seed_scalable_complete/
WORKDIR /Seed_scalable_complete
RUN git sparse-checkout set bgp_smart_contracts
RUN mv bgp_smart_contracts ../bgp_smart_contracts
WORKDIR /
RUN python3 /bgp_smart_contracts/src/solc_ver_install.py
