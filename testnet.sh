#!/usr/bin/env bash

# A testing script for my sockets.
# options
# -n => network
# -f => filename to read into socket | -t => literal text to read into socket
# -all => test all available network types
#
helpp() {
   echo "# Usage"
   echo "#   test -f <filename> -n <networkname(s)> -a <addrinfo> OR"
   echo "#   test -t <text> -n <networkname(s)> -a <addrinfo> OR"
   echo "#   test -all -a <addrinfo>"
   echo "#"
   echo "#   <networkname> can be a space separated string of networks"
   echo "#   Posible network names are:"
   echo "#      tcp, tcp6, udp, udp6, unix-connect, unix-client"
   echo "#"
   echo "#  The -all option test all the network names available,"
   echo "#  make sure there is a server running on the address else it will error."
}

if [[ -z "$@" ]]; then
    helpp
    exit 1
fi  

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        -all)
            ALL="yes"
            shift
            ;;
        -u)
            UNIXADDR="$2"
            shift
            shift
            ;;
        -a)
            IPADDR="$2"
            shift
            shift
            ;;
        -n)
            NET="$2"
            shift
            shift
            ;;
        -f)
            FILE="$2"
            shift
            shift
            ;;
        -t)
            TEXT="$2"
            shift
            shift
            ;;
        *)
            echo Unknown argument $1
            helpp
            exit 1
        ;;
    esac
done

# parse network types to test
if [[ "$ALL" == "yes" ]]; then
    NET="tcp tcp6 udp udp6 unix-connect unix-client"

    # if you are testing on all network types, you need a separate
    # unix address for the unix domain sockets.
    if [[ -z "$UNIXADDR" ]]; then
        echo You need a unix address to test unix domain sockets
        helpp
        exit 1
    fi
elif [[ -z "$NET" ]]; then
    echo you need a network type to connect to
    helpp
    exit 1
fi

# check the address to connect to
if [[ -z "$IPADDR" ]] && [[ -z "$UNIXADDR" ]]; then
    echo You need an address to connect to
    helpp
fi

# check if data to be sent is a file or text
if [[ -n "$FILE" ]]; then
    CMD="cat ${FILE}"
elif [[ -n "$TEXT" ]]; then
    CMD="echo ${TEXT}"
else
    echo you need some kind of data to write into the connection
    helpp
fi

debug() {
    echo "---------- executing '$1 | socat $2:$3 - > /dev/null' ----------"
}


for net in $NET; do
    if [[ "$net" == *"unix"* ]]; then
        ADDR="$UNIXADDR"
    else
        ADDR="$IPADDR"
    fi

    debug "$CMD" $net "$ADDR"
    # socat [options] <address> <address>
    $CMD | socat $net:"$ADDR" - > /dev/null
done


#cat $1 | socat $net:$2 - > /dev/null
