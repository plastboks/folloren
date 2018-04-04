#!/bin/bash

docker create \
    --name=folloren \
    -p 8765:5000 \
    folloren:latest
