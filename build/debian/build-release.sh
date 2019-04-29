#!/bin/bash
rm simpleschema_*
mkdir -p build-dir/usr/share/simplequeue
mkdir -p build-dir/etc
mkdir -p build-dir/DEBIAN

pkgbuild=`cat pkgbuild`
((pkgbuild++))
echo $pkgbuild > pkgbuild

build=`git rev-list --count HEAD`
version=`cat ../../VERSION`
sed -i "s/Version:.*/Version: $version-$build-$pkgbuild/" files/control

cp files/control build-dir/DEBIAN
cp files/conffiles build-dir/DEBIAN

cp ../../config.ini build-dir/etc
cp ../../SimpleQueue.py build-dir/usr/share/simplequeue

dpkg-deb --build ./build-dir simpleschema_$version-$build-$pkgbuild.deb

if [ -f /opt/dist.sh ]; then
	/opt/dist.sh `pwd`/simpleschema_$version-$build-$pkgbuild.deb simpleschema
fi
rm simpleschema_*
rm -fr build-dir
