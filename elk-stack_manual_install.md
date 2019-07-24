# ELK Testing

## Create new VM as per CHC Policies, etc.

## Create 2 Storage disks, then add to VM:

### Create Elastic data directory using /dev/sdb
```
sudo mkdir -p /mnt/disks/data
sudo mount -o discard,defaults /dev/sdb /mnt/disks/data
sudo chmod a+w /mnt/disks/data
echo UUID=`sudo blkid -s UUID -o value /dev/sdb` /mnt/disks/data ext4 discard,defaults,nofail
0 2 | sudo tee -a /etc/fstab
sudo mkdir /mnt/disks/data/elasticsearch
sudo chown -R elasticsearch.elasticsearch /mnt/disks/data/elasticsearch/
```

## Update
`sudo yum update`

## Java
`sudo yum install -y java-1.8.0-openjdk`

## Elastic
`sudo rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch`

`sudo vi /etc/yum.repos.d/elasticsearch.repo`:

```[elasticsearch-7.x]
name=Elasticsearch repository for 7.x packages
baseurl=https://artifacts.elastic.co/packages/7.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
```
`sudo yum install -y elasticsearch`

`sudo vi /etc/elasticsearch/elasticsearch.yml`
Add the following:
  path.data: /mnt/disks/data/elasticsearch

`sudo systemctl enable elasticsearch.service`
`sudo systemctl start elasticsearch.service`

## Logstash
https://www.elastic.co/guide/en/logstash/current/plugins-inputs-google_pubsub.html
`sudo yum install -y logstash`

`/usr/share/logstash/bin/logstash-plugin list`

`/usr/share/logstash/bin/logstash-plugin install logstash-input-google_pubsub`

`/etc/logstash/conf.d/10-pubsub.conf`:
```
input {
    google_pubsub {
        project_id => "iwcs-img-dit01"
        topic => "sdmz-ingress-nginx-json"
        subscription => "sdmz-nginx-ingress-json-sub"
        json_key_file => "/opt/pubsubkey.json"
        create_subscription => false
    }
}

filter {
  json {
    source => "message"
  }
}

output { stdout { codec => rubydebug } }
```


`30-elasticsearch-output.conf`:
```
output {
  elasticsearch {
    hosts => ["localhost:9200"]
    manage_template => false
    index => "stackdriver-%{+YYYY.MM.dd}"
  }
}
```

## Install Kibana

`sudo yum install kibana nginx`
`sudo systemctl enable kibana`
`sudo systemctl start kibana`
`sudo systemctl enable nginx`
`sudo systemctl start nginx`
`echo "kibanaadmin:`openssl passwd -apr1`" | sudo tee -a /etc/nginx/htpasswd.users`

```
sudo setsebool httpd_can_network_connect 1 -P
sudo firewall-cmd --add-service=https
sudo firewall-cmd --runtime-to-permanent
sudo mkdir /etc/ssl/private
sudo chmod 700 /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
```

`sudo vi /etc/nginx/conf.d/jmftest.conf`

Add contents from nginx.conf in this directory

`sudo nginx -t`
`sudo systemctl restart nginx`

## Install grafana

`sudo yum install https://dl.grafana.com/oss/release/grafana-6.2.5-1.x86_64.rpm`


```
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```
