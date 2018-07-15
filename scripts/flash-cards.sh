#!/bin/bash
umount /dev/sdd1
umount /dev/sde1
umount /dev/sdf1
umount /dev/sdg1
umount /dev/sdh1
umount /dev/sdi1
umount /dev/sdj1
umount /dev/sdd2
umount /dev/sde2
umount /dev/sdf2
umount /dev/sdg2
umount /dev/sdh2
umount /dev/sdi2
umount /dev/sdj2

dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sdd &
dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sde &
dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sdf &
dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sdg &
dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sdh &
dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sdi &
dd if=rpi-esu-bridge-ro-20180630-a96e7c.img of=/dev/sdj &

