#!/bin/bash
mkdir -p build-dir/usr/bin
mkdir -p build-dir/usr/share/simplequeue
#mkdir -p build-dir/etc/init.d
mkdir -p build-dir/DEBIAN
mkdir -p build-dir/etc/systemd/system
mkdir -p build-dir/etc/rsyslog.d

pkgbuild=`cat pkgbuild`
((pkgbuild++))
echo $pkgbuild > pkgbuild

build=`git rev-list --count HEAD`
version=`cat ../../VERSION`
sed -i "s/Version:.*/Version: $version-$build-$pkgbuild/" files/control

cp 20-simplequeue.conf build-dir/etc/rsyslog.d
cp files/control build-dir/DEBIAN
cp files/conffiles build-dir/DEBIAN
#cp files/simplequeue build-dir/etc/init.d
cp files/simplequeue.service build-dir/etc/systemd/system

cp ../../config.ini build-dir/etc/SimpleQueue.ini
cp ../../SimpleQueue.py build-dir/usr/share/simplequeue
cp ../../sq.py build-dir/usr/bin/sq
cp ../../testJob.py build-dir/usr/share/simplequeue
cp ../../testJob.php build-dir/usr/share/simplequeue

chmod 755 build-dir/usr/bin/sq

dpkg-deb --build ./build-dir simplequeue_$version-$build-$pkgbuild.deb

if [ -f /opt/dist.sh ]; then
	/opt/dist.sh `pwd`/simplequeue_$version-$build-$pkgbuild.deb simplequeue
fi
rm simplequeue_*
rm -fr build-dir
