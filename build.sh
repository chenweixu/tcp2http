#!/bin/bash
# 0.1         2018-12-25 15:28:12

version=0.1
container=tcp2http
img_dir=/data/share/docker_images

img_file=$img_dir/chenwx_${container}_${version}.tar

docker stop $container
docker rm $container
docker rmi chenwx/$container:$version
rm $img_dir/chenwx_$container_$version.tar

#------------------------------------------------

docker build -t chenwx/$container:$version -f dockerfile .

sleep 2

docker save chenwx/$container:$version > $img_file


docker run --name $container -h $container --net="host" -d chenwx/$container:$version
# docker run --name $container -h $container --net="host" -d chenwx/$container:1.0.2

# docker run --name tcp2http -h tcp2http --net="host" -d chenwx/tcp2http:0.1