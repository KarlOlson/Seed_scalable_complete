#!/bin/bash

SAMPLE_COUNT='100'

set -e

cd "`dirname "$0"`"
results="`pwd`/results"

[ ! -d "$results" ] && mkdir "$results"

function collect {
    for j in `seq 1 $SAMPLE_COUNT`; do {
        now="`date +%s`"
        echo "[$now] snapshotting cpu/mem info..."
        cat /proc/stat > "$this_results/stat-$now.txt"
        cat /proc/meminfo > "$this_results/meminfo-$now.txt"
        sleep 1
    }; done
}

this_results="$results/bench-0-ases"
[ ! -d "$this_results" ] && {
    mkdir "$this_results"
    collect
}

for ((i=${RESUME:-10}; i<=1000; i+=10)); do {
    rm -rf out

    echo "generating emulation..."
    ./lots-of-networks.py --ases $i --ixs 5 --routers 1 --hosts 0 --outdir out --yes
    this_results="$results/bench-$i-ases"
    [ ! -d "$this_results" ] && mkdir "$this_results"
    pushd out

    echo "buliding emulation..."
    docker-compose build
    # docker-compose up -d # bugged? stuck forever at "compose.parallel.feed_queue: Pending: set()"...
    # start only 10 at a time to prevent hangs
    echo "start emulation..."
    ls | grep -Ev '.yml$|^dummies$' | xargs -n10 -exec docker-compose up -d

    echo "waiting 60s for ospf/bgp, etc..."
    sleep 60 # wait for ospf, bgp, etc.
    collect

    docker-compose down
    popd
}; done