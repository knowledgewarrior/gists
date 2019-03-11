# Block Device Settings, aka "Readahead" for MongoDB
### Jason Fowler, Technical Services Engineer

## What is `readahead` ?

`Readahead` is a setting on a block device (usually a storage device like a harddrive or NAS) that controls how much data is fetched whenever a read from that block device happens. Disk seeks on spinning disks are very expensive, but accessing sequential blocks of data is relatively cheap. Since many applications tend to access data sequentially, it makes sense that if you're going to pay the cost to do a disk seek to read in data, you should try to read some extra data after.

We (MongoDB Technical Services) have observed that when using 256 blocks `readahead` on filesystems hosting both the database and backups, the snapshot creation speed improved.

If `readahead` is set too high MongoDB won't be able to use all the RAM available on the machine effectively. This is because each disk read will be pulling a lot of extra data which will take up room in memory, but will never be accessed before being paged out to make room for data read in by another read operation.  Please see below for more information on setting `readahead` for MongoDB.

## How do I know how to find `readhead` settings?

### Linux commands to **find** `readahead` for device:

To list all devices, type `sudo blockdev --report`

(The following assumes `/dev/sda` as the block device.)

### BLOCKDEV
`sudo blockdev --getra /dev/sda`

### UDEVADM
`sudo udevadm info -a -p /sys/block/sda`

### HDPARM
`sudo hdparm -a /dev/sda`

### TUNED
### Red Hat/Centos
The [tuned tool](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-red_hat_enterprise_linux-performance_tuning_guide-tuned_) is typically included in Red Hat and derivatives, eg Centos/Amazon Linux
"Tuned is a daemon that uses udev to monitor connected devices and statically and dynamically tunes system settings according to a selected profile."  It is a tool used for much more than just setting disk `readahead` and is provided here for information purposes.

Please see the [documentation](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-red_hat_enterprise_linux-performance_tuning_guide-storage_and_file_systems) for more information on Red Hat (and derivatives) performance and storage tuning.

##  What do I do when I want to make a change to the `readahead` settings?

While all the above tools are great for finding and setting `readahead` for storage systems, `hdparm` is the easier tool to use (IMHO) on both Red Hat and Debian Linux derivatives.

In 2005, Canadian Mark Lord developed the small `hdparm` utility to test Linux drivers for IDE hard drives. Since then, the program has developed into a valuable tool for diagnosis and tuning of hard drives. For example, it tests the speed of hard drives and solid state disks, puts devices to sleep, and turns the energy-saving mode on or off. With modern devices, it can activate the acoustic mode and clean up SSDs.

**Installation**:
To install `hdparm` on Debian use `apt` and on Red Hat use `yum`:
`sudo {apt|yum} install hdparm`

### What is the `readahead`?
`sudo hdparm -a /dev/sda`

### How fast is the disk?
`sudo hdparm -t /dev/sda`

```
dev/sda:
 Timing buffered disk reads: 1496 MB in  3.00 seconds = 498.47 MB/sec
```

You can test the speed to see what the results are before and after making the `hdparm` change.

### Linux commands to **SET** `readahead` for device:

(The following assumes `/dev/nvme0n1` as the block device.)

First find the device itself:

`sudo blockdev --report`

The `sudo blockdev --report` command displays all devices with `readahead` setting under the `RA` column.

```
RO    RA   SSZ   BSZ   StartSec            Size   Device
rw   256   512  4096          0     64424509440   /dev/nvme0n1
rw   256   512   512       4096     64422395392   /dev/nvme0n1p1
rw   256   512  4096       2048         1048576   /dev/nvme0n1p128
```

Then double-check the `readahead` setting to confirm in `hdparm`:

`sudo hdparm -a /dev/nvme0n1`

The `sudo hdparm -a /dev/nvme0n1` command displays the `readahead` setting and whether it is on or off for the specified block device.

```
/dev/nvme0n1:
 readahead     = 128 (on)
```

To set the block device to a setting of `256` for `readahead`:

`sudo hdparm -a256 /dev/sda`

To keep the changes permanent after reboots, use the `/etc/hdparm.conf` file as per instructions according to your Linux distribution.  

## Debian and derivatives including Ubuntu and Linux Mint

Debian Linux and derivatives read the /etc/hdparm.conf configuration file on system startup. In it is a section for each hard drive with the following format:

```
/dev/sda {
  #sector count for filesystem read-ahead
  read_ahead_sect = 512
  #disable/enable the IDE drive's read-lookahead feature
  lookahead = on
}
```

## Red Hat and derivatives including CentOS and Amazon Linux

To make `readahead` changes persistent across reboots:
 (ensure <device> set to the appropriate volume)

```bash
$ echo 'ACTION=="add|change", KERNEL=="<device>", ATTR{bdi/read_ahead_kb}="16"' | sudo tee -a /etc/udev/rules.d/85-mongodb.rules
```

The value of ATTR bdi/read_ahead_kb is in kb. One sector = 512 bytes; eg 256 kb = 512 sectors.
Note: You will need to restart your mongod process/s after this change for the new readahead settings to take effect.  You will need to set it for the physical devices, the logical devices, and the mount.

For more information on SDD disk tuning for Red Hat systems, please see the [Red_Hat_Enterprise_Linux-Performance_Tuning_Guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html-single/performance_tuning_guide/#sect-Red_Hat_Enterprise_Linux-Performance_Tuning_Guide-Considerations-Solid_State_Disks)

## Proof is in the Pudding

We ran tests to find out how changing `readahead` on the Linux block device for a BackupDaemon, a `node` used to run and perform backups and database snapshots, affects running backups for a 4TB Head DB.  

ReadAhead                                 Snapshot Completion (hrs)
256kb / 512 blocks                            7.7

1024kb / 2048 blocks                          5.6

4096kb / 8192 blocks                          4.4

## Conclusion

As you can see in the above table, snapshot creation time is reduced by almost half changing `readahead` from 512 blocks to 8192 blocks.
