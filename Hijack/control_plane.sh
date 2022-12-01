#!/bin/bash

hijacked_route=0
no_hijacked_route=0
Routers=($(docker ps -f "name=router" -q))
RPKI=($(docker ps -f "name=rpki" -q))

hijacked_prefix=$1

for router in ${Routers[@]}; do
  text=$(docker ps --format '{{.Names}}' -f "ID=$router")
  delimiter="-"
  string=$text$delimiter

  AS_info=()
  while [[ $string ]]; do
    AS_info+=( "${string%%"$delimiter"*}" )
    string=${string#*"$delimiter"}
  done
  echo "############### ${AS_info[0]} ###############" 
  # docker exec $router /bin/bash -c "birdc show route all | grep "74.80.186.0/25"" && let hijacked_route++ || let no_hijacked_route++ 
  docker exec $router /bin/bash -c "birdc show route all | grep $hijacked_prefix" && let hijacked_route++ || let no_hijacked_route++ 
done

echo "#Routers that have the hijacked route in its RIB: $hijacked_route"
echo "#Routers that do not have the hijacked route in its RIB: $no_hijacked_route"
echo "#ASs deployed RPKI: $(echo ${#RPKI[*]})"
