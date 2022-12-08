
asn=100
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/b00-mini-internet/IX$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"

asn=101
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/b00-mini-internet/IX$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"


asn=102
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/b00-mini-internet/IX$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"

asn=103
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/b00-mini-internet/IX$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"

asn=104
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/b00-mini-internet/IX$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"

asn=105
router=$(docker container ls  | grep 'output_rs_ix_ix'$asn | awk '{print $1}')

docker cp ../../configs/b00-mini-internet/IX$asn.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn bird.conf updated"


asn=2
router_num=101
router=$(docker container ls  | grep 'output_rnode_'$asn'_r'$router_num | awk '{print $1}')
echo $router

docker cp ../../configs/b00-mini-internet/$asn-r$router_num.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn router: $asn"_r"$router_num bird.conf updated"

asn=3
router_num=103
router=$(docker container ls  | grep 'output_rnode_'$asn'_r'$router_num | awk '{print $1}')
echo $router

docker cp ../../configs/b00-mini-internet/$asn-r$router_num.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn router: $asn"_r"$router_num bird.conf updated"

asn=12
router_num=101
router=$(docker container ls  | grep 'output_rnode_'$asn'_r'$router_num | awk '{print $1}')
echo $router

docker cp ../../configs/b00-mini-internet/$asn-r$router_num.conf $router:/etc/bird/bird.conf
docker exec $router /bin/bash -c "birdc configure"

echo "ASN$asn router: $asn"_r"$router_num bird.conf updated"