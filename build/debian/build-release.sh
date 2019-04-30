#!/bin/bash
mkdir -p build-dir/usr/share/simplequeue
mkdir -p build-dir/etc/init.d
mkdir -p build-dir/DEBIAN

pkgbuild=`cat pkgbuild`
((pkgbuild++))
echo $pkgbuild > pkgbuild

build=`git rev-list --count HEAD`
version=`cat ../../VERSION`
sed -i "s/Version:.*/Version: $version-$build-$pkgbuild/" files/control

cp files/control build-dir/DEBIAN
cp files/conffiles build-dir/DEBIAN
cp files/simplequeue build-dir/etc/init.d

cp ../../config.ini build-dir/etc/SimpleQueue.ini
cp ../../SimpleQueue.py build-dir/usr/share/simplequeue
cp ../../testJob.py build-dir/usr/share/simplequeue
cp ../../testJob.php build-dir/usr/share/simplequeue

dpkg-deb --build ./build-dir simpleschema_$version-$build-$pkgbuild.deb

if [ -f /opt/dist.sh ]; then
	/opt/dist.sh `pwd`/simpleschema_$version-$build-$pkgbuild.deb simpleschema
fi
rm simpleschema_*
rm -fr build-dir
