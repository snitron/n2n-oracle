#!/bin/bash
FROM python:latest

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install python3 python3-pip -y
RUN pip3 install cython cmake web3 py-solc-x python-dotenv
WORKDIR /deployment

COPY . .
RUN chmod +x run.sh