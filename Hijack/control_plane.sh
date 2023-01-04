#!/bin/bash

hijacked_route=0
no_hijacked_route=0
Routers=($(docker ps -f "name=(-router)|(-r[0-9])" -q))
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
  echo "############### ${AS_info[0]} ############### ${router}" 
  if [[ $(docker exec $router /bin/bash -c "birdc show route all | grep $hijacked_prefix") ]]; then
    echo "Hijacked route found in ${AS_info[0]}"
    let hijacked_route++
  else
    echo "No hijacked route found in ${AS_info[0]}"
    let no_hijacked_route++
  fi
done

echo "#Routers that have the hijacked route in its RIB: $hijacked_route"
echo "#Routers that do not have the hijacked route in its RIB: $no_hijacked_route" # need to subtract 1. always gets 1 extra router for whatever reason
echo "#ASs deployed RPKI: $(echo ${#RPKI[*]})"
