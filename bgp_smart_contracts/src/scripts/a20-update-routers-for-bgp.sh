
asn=100
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/ix$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"

asn=101
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/ix$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"

asn=3
router_num=1
router=$(docker container ls  | grep 'output_rnode_'$asn'_r'$router_num | awk '{print $1}')

docker cp ../../configs/as$asn-r$router_num.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn router: $asn"_r"$router_num bird.conf updated"

asn=3
router_num=4
router=$(docker container ls  | grep 'output_rnode_'$asn'_r'$router_num | awk '{print $1}')

docker cp ../../configs/as$asn-r$router_num.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn router: $asn"_r"$router_num bird.conf updated"