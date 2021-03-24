FROM ubuntu:20.04

EXPOSE 80
EXPOSE 8080
EXPOSE 8545
EXPOSE 443

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install python3 python3-pip -y
RUN pip3 install cython cmake web3 py-solc-x python-dotenv eth-abi
WORKDIR /

USER root
RUN mkdir deployment
RUN mkdir tools
RUN mkdir mountedcum
RUN useradd -ms /bin/bash admin

COPY --chown=admin:admin applyCommits.py ./tools
COPY --chown=admin:admin . ./deployment

RUN chmod 777 -R ./deployment
RUN chmod 777 -R ./mountedcum

RUN cd deployment