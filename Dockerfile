FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install python3 python3-pip -y
RUN pip3 install cython cmake web3 py-solc-x python-dotenv eth-abi
WORKDIR /

USER root
RUN mkdir deployment
RUN useradd -ms /bin/bash admin

COPY --chown=admin:admin . ./deployment

RUN chmod 777 -R ./deployment
RUN cd deployment

CMD python3 deploy.py