#!/bin/bash

cd $(dirname "$0")/..

rm -f -r /tmp/tiled_storage
mkdir /tmp/tiled_storage
tiled catalog init sqlite+aiosqlite:////tmp/tiled_storage/catalog.db

# Generate a development key with tiled api_key create, and add it exporting env var to bashrc file 
tiled serve catalog \
    /tmp/tiled_storage/catalog.db \
    -w /tmp/tiled_storage/data/ \
    --api-key="TSCSD" \
    -r /tmp
    -d
