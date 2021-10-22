#!/bin/bash

set -e

cd "`dirname "$0"`"
results="`pwd`/results"

for ((i=${RESUME:-10}; i<=250; i+=10)); do {
    rm -rf out

    echo "generating emulation..."
    ./long-network.py --ases 1 --hops $i --outdir out

    this_results="$results/bench-$i-fwd-long"

    [ ! -d "$this_results" ] && mkdir "$this_results"
    pushd out

    echo "buliding emulation..."
    docker-compose build
    # docker-compose up -d # bugged? stuck forever at "compose.parallel.feed_queue: Pending: set()"...
    # start only 10 at a time to prevent hangs
    echo "start emulation..."
    ls | grep -Ev '.yml$|^dummies$' | xargs -n10 -exec docker-compose up -d

    echo "wait for tests..."
    sleep 240

    host_ids="`docker ps | egrep "hnode_.*_a" | cut -d\  -f1`"
    for id in $host_ids; do {
        while ! docker exec $id ls /done; do {
            echo "waiting for $id to finish tests..."
            docker cp "$id:/ping.log" "$this_results/$id-ping.log"
            docker cp "$id:/iperf-tx.txt" "$this_results/$id-iperf-tx.txt"
            docker cp "$id:/iperf-rx.txt" "$this_results/$id-iperf-rx.txt"
        }; done
    }; done

    docker-compose down
    popd
}; done