Readahead is a setting on a block device (usually a storage device like a harddrive or NAS) that controls how much data is fetched whenever a read from that block device happens. This is done because disk seeks on spinning disks are very expensive, but accessing sequential blocks of data is relatively cheap. Since many applications tend to access data sequentially, it makes sense that if you're going to pay the cost to do a disk seek to read in data, you should try to read some extra data after With some customers using spinning HDDs we have observed that using 256 blocks readahead the snapshot creation speed improved.

If readahead is set too high MongoDB won't be able to use all the RAM available on the machine effectively. This is because each disk read will be pulling a lot of extra data which will take up room in memory, but will never be accessed before being paged out to make room for data read in by another read operation.  Please see below for more information on setting `readahead` for MongoDB.

Please let us know if you have any follow-up questions.

Kind regards,
Jason and the MongoDB Team

### readahead=0 vs default readahead=8092

If you only need a few KB of data for each request, the system will waste ~8MB of RAM holding unnecessary data and it will waste ~8MB worth of IO capacity retrieving that data.

### How to set readahead using blockdev

One can set the readahead using the blockdev command as root/superuser (replace <device> with appropriate value for the node>.

`sudo blockdev --setra 32 <device>`

and to make this change persistent across reboots (again change <device> to the appropriate volume).

```bash
$ echo 'ACTION=="add|change", KERNEL=="<device>", ATTR{bdi/read_ahead_kb}="16"' | sudo tee -a /etc/udev/rules.d/85-mongodb.rules
```

Note: This rule is also possible, it prevents any misunderstandings (for non-virtual systems change queue/scheduler to cfq)
```bash
$ echo SUBSYSTEM=="block", ACTION=="add|change", ATTR{bdi/read_ahead_kb}="16", ATTR{queue/scheduler}="noop" ' | sudo tee -a /etc/udev/rules.d/85-mongodb.rules
```

The value of ATTR bdi/read_ahead_kb is in kb. For example 16 kb = 32 sectors.

Note: You will need to restart your mongod process/s after this change for the new readahead settings to take effect.  You will need to set it for the physical devices, the logical devices, and the mount.


## Jason Fowler
## March 2019

# Block Device Settings, aka "Readahead" for MongoDB

(The following assumes `/dev/sda` as the block device.
To list all devices, type `sudo blockdev --report`)

## Generic Linux commands to find `readahead` for device:
### BLOCKDEV
`sudo blockdev --getra /dev/sda`

### UDEVADM
`sudo udevadm info -a -p /sys/block/sda`

## Debian/Ubunut/Linux Mint commands to find `readahead` for device:
### HDPARM
(The `hdparm` tool is included "for free" in Debian and derivatives, eg Ubuntu/Linux Mint).

`sudo hdparm -a /dev/sda`

  #### How fast is the disk?
  ```
  /sudo hdparm -t /dev/sda
  dev/sda:
   Timing buffered disk reads: 1496 MB in  3.00 seconds = 498.47 MB/sec
   ```


### TUNED
### Red Hat/Centos
The [tuned tool](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-red_hat_enterprise_linux-performance_tuning_guide-tuned_) is included "for free" in Red Hat and derivatives, eg Centos/Amazon Linux
"Tuned is a daemon that uses udev to monitor connected devices and statically and dynamically tunes system settings according to a selected profile."

Please see the [documentation](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-red_hat_enterprise_linux-performance_tuning_guide-storage_and_file_systems) for more information on Red Hat (and derivatives) performance and storage tuning

`sudo yum -y install tuned`
`sudo vi /usr/lib/tuned/throughput-performance/tuned.conf`
Change
`sudo tuned-adm profile no-thp`
