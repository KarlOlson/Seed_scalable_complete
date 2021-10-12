#!/bin/bash

set -e

cd "`dirname "$0"`"
results="`pwd`/results"

[ ! -d "$results" ] && mkdir "$results"

for ((i=10; i<=1000; i+=10)); do {
    rm -rf out

    echo "generating emulation..."
    ./lots-of-networks.py --ases $i --ixs 5 --routers 1 --hosts 0 --outdir out --yes
    this_results="$results/bench-$i-ases"
    [ ! -d "$this_results" ] && mkdir "$this_results"
    pushd out

    echo "starting emulation..."
    docker-compose build
    docker-compose up -d

    echo "waiting 60s for ospf/bgp, etc..."
    sleep 60 # wait for ospf, bgp, etc.
    for j in {1..100}; do {
        now="`date +%s`"
        echo "[$now] snapshotting cpu/mem info..."
        cat /proc/stat > "$this_results/stat-$now.txt"
        cat /proc/meminfo > "$this_results/meminfo-$now.txt"
        sleep 1
    }; done

    docker-compose down
    popd
}; done