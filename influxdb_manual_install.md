# Install InfluxDB
  https://docs.influxdata.com/influxdb/v1.7/introduction/installation/

# Create VM Instance

## Create new VM as per CHC Policies, etc.

## Create 2 Storage disks, then add to VM:

  ### Create influxdb DB directory using /dev/sdb
  ```
  lsblk
  sudo mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb
  sudo mkdir -p /mnt/disks/db
  sudo mount -o discard,defaults /dev/sdb /mnt/disks/db
  sudo chmod a+w /mnt/disks/db
  echo UUID=`sudo blkid -s UUID -o value /dev/sdb` /mnt/disks/db ext4 discard,defaults,nofail 0 2 | sudo tee -a /etc/fstab
  ```
  ### Create influxdb WAL directory using /dev/sdc
  ```
  lsblk
  sudo mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdc
  sudo mkdir -p /mnt/disks/wal
  sudo mount -o discard,defaults /dev/sdc /mnt/disks/wal
  sudo chmod a+w /mnt/disks/wal
  echo UUID=`sudo blkid -s UUID -o value /dev/sdc` /mnt/disks/wal ext4 discard,defaults,nofail 0 2 | sudo tee -a /etc/fstab
  ```

## Add InfluxDB Repo and Install
  ```
  cat <<EOF | sudo tee /etc/yum.repos.d/influxdb.repo
  [influxdb]
  name = InfluxDB Repository - RHEL \$releasever
  baseurl = https://repos.influxdata.com/rhel/\$releasever/\$basearch/stable
  enabled = 1
  gpgcheck = 1
  gpgkey = https://repos.influxdata.com/influxdb.key
  EOF
  ```
  ```
  sudo yum install influxdb
  ```
  ```
  sudo systemctl start influxdb
  ```
  ```
  sudo chown influxdb:influxdb /mnt/disks/wal
  ```
  ```
  sudo chown influxdb:influxdb /mnt/disks/db
  ```

## Change db and wal directories in influxdb.conf
  ```
  sudo vi /etc/influxdb/influxdb.conf
  ```
  Find [data] section and make change like below
  ```
  [data]
  # The directory where the TSM storage engine stores TSM files.
  dir = "/mnt/disks/db"

  # The directory where the TSM storage engine stores WAL files.
  wal-dir = "/mnt/disks/wal"
  ```

## Grafana

  Install as per generic installation
  See `grafana.ini` and `nginx.conf` as examples which work.  You'll need to generate certs to enable SSL:

  `openssl req -new -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out jmf-grafana.crt -keyout jmf-grafana.key`

## Telegraf

`curl -O https://dl.influxdata.com/telegraf/releases/telegraf-1.11.2-1.x86_64.rpm`
`sudo rpm -vhU telegraf-1.11.2-1.x86_64.rpm`

`/etc/telegraf/telegraf.conf`
```
# Global Agent Configuration
[agent]
  hostname = "jmf-influxdb"
  flush_interval = "15s"
  interval = "15s"

# Input Plugins
[[inputs.cloud_pubsub]]
  project = "iwcs-img-dit01"
  subscription = "sdmz-ingress-nginx-json-telegraf"
  data_format = "json"
  credentials_file = "/opt/pubsubkey.json"
  tag_keys = ["resource_labels_cluster_name"]
  json_string_fields = ["jsonPayload_BodyReponseSize", "jsonPayload_DateTime", "jsonPayload_FullHTTPRequest", "jsonPayload_HTTPMethod", "jsonPayload_HTTPReferrer", "jsonPayload_HTTPRequest", "jsonPayload_RequestID", "jsonPayload_RequestTime", "jsonPayload_SourceIPAddress", "jsonPayload_UpstreamAddress", "jsonPayload_UpstreamHTTPResponse", "jsonPayload_UpstreamProxyName", "jsonPayload_UpstreamResponseLength", "jsonPayload_UpstreamResponseTime"]
  json_name_key = "logName"

[[inputs.cloud_pubsub]]
  project = "iwcs-img-dit01"
  subscription = "sdmz-errors-telegraf"
  data_format = "json"
  credentials_file = "/opt/pubsubkey.json"
  tag_keys =  ["resource_labels_cluster_name"]
  json_string_fields = ["jsonPayload_bizProcId", "jsonPayload_bizTxId", "jsonPayload_logger", "jsonPayload_msg", "jsonPayload_namespace", "jsonPayload_parentReqId", "jsonPayload_reqId", "jsonPayload_tenantId", "jsonPayload_threadId"]
  json_name_key = "logName"
  json_time_key = "timestamp"
  json_time_format = "2006-01-02T15:04:05Z07:00"

# Output Plugin InfluxDB
[[outputs.influxdb]]
  database = "telegraf"
  urls = [ "http://127.0.0.1:8086" ]
  username = "telegraf"
  password = "jmf-pass"

[[outputs.file]]
  files = ["/tmp/telegraf-metrics.out"]
  rotation_max_size = "60MB"
  data_format = "influx"
```


```
SELECT * FROM "cloud_pubsub" WHERE "jsonPayload_msg_HTTPResponse" = 200 GROUP BY time($__interval) fill(null)
```
