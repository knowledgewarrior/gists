#!/usr/bin/env python

###############################
# Autoconfig for Icinga 
# to emulate service discovery
# Jason Fowler, Avid Technology
# March 2016
#
# IMPORTANT:    - please do a "pip -R requirements.txt" to import all the python tools
#               - you need a ".boto" file in your home directory containing your AWS access and secret keys
#
###############################

import logging
import os
import re
import boto.ec2
import argparse

from jinja2 import Environment
from jinja2 import FileSystemLoader

############################
# all the function goodness
############################

class Service:
    def __init__(self, service_name, host_names, check_command):
        self.service_name = service_name
        self.host_names = host_names
        self.check_command = check_command

def populate_instance_dictionary(conn, instance_dictionary):
    reservation_list = conn.get_all_instances()
    for current_reservation in reservation_list:
        for instance in current_reservation.instances:
            if instance.state == "running": 
                if instance.tags.has_key("Name"):
                        if re.search(avidenv, instance.tags["Name"]):  
                            instance_dictionary[instance.id] = instance

def populate_service_dictionary(instance_dictionary, service_dictionary):
    for instance in instance_dictionary:
        if 'Name' in instance_dictionary[instance].tags:
            name_tag = instance_dictionary[instance].tags.get("Name").encode('utf-8')
        else:
            name_tag = "None"
        if 'Services' in instance_dictionary[instance].tags:
            instance_services = instance_dictionary[instance].tags.get("Services").split(",")
            for instance_service in instance_services:
                if instance_service in service_dictionary.keys():
                    service_dictionary[instance_service].host_names += ',' + name_tag
                else:
                    logging.info('Service {instance_service!s} has been added to the service dictionary.'.format
                        (instance_service=instance_service))
                    new_service = Service(instance_service, name_tag, "check_" + instance_service)
                    service_dictionary[instance_service.encode('utf-8')] = new_service

def populate_nrpe(instance_dictionary, service_dictionary):
    instance_dictionary_csv = ''
    for instance in instance_dictionary:
        if 'Name' in instance_dictionary[instance].tags:
            instance_dictionary_csv += instance_dictionary[instance].tags.get('Name').encode('utf-8') + ','
            instance_dictionary_csv_trim = instance_dictionary_csv[:-1]
            service_dictionary['nrpe_disk_space'] = Service('nrpe_disk_space',
                instance_dictionary_csv_trim, 'check_nrpe!check_disk_space!10%20% /')
            service_dictionary['nrpe_disk_inode'] = Service('nrpe_disk_inode',
                instance_dictionary_csv_trim, 'check_nrpe!check_disk_inode!10%20% /')
            service_dictionary['nrpe_cpu_load'] = Service('nrpe_cpu_load',
                instance_dictionary_csv_trim, 'check_nrpe!check_cpu_load!30,25,2015,10,5')
            service_dictionary['nrpe_mem_swap'] = Service('nrpe_mem_swap',
                instance_dictionary_csv_trim, 'check_nrpe!check_mem_swap!80%90%')

def write_host_configs(instance_dictionary, config_file_dir, host_template, avidenv):
    '''writes host configs'''
    logging.info('write_host_configs called')
    for instance in instance_dictionary:
        if instance_dictionary[instance].tags.has_key("Name"):
            host_file_content = host_template.render(host_name=instance_dictionary[instance].tags.get("Name"),
                check_command='check-host-alive', private_ip_address=instance_dictionary[instance].private_ip_address)
            host_file_path = str('{config_file_dir!s}/hosts/{host!s}.conf'.format
                (config_file_dir=config_file_dir, host=instance_dictionary[instance].tags.get("Name")))
            host_file_handle = open(host_file_path, 'w')
            host_file_handle.write(host_file_content)
            host_file_handle.close()

def write_service_configs(service_dictionary, config_file_dir, service_template):
    '''write service configs'''
    logging.info('write_service_configs called')
    for service in service_dictionary:
        logging.info('service template for {service!s} will be rendered'.format(service=service))
        service_file_content = service_template.render(host_list=service_dictionary[service].host_names,
            service_description=service_dictionary[service].service_name, check_command=service_dictionary[service].check_command)
        service_file_path = str('{config_file_dir!s}/services/{service!s}.conf'.format(config_file_dir=config_file_dir, service=service))
        service_file_handle = open(service_file_path, 'w')
        service_file_handle.write(service_file_content)
        service_file_handle.close()

##################################
# Main Section
# call all the function goodness!
##################################

parser = argparse.ArgumentParser()
parser.add_argument('--region', help='region for which icinga_aws_autodiscover should be run. Default is us-east-1.', default='us-east-1')
parser.add_argument('--configpath', dest='configpath', help='configuration path for icinga files', default='./config_dir')
parser.add_argument('--avidenv', help='avid environment, ie stg or prd. Default is stg.', default='stg')
args = parser.parse_args()

region = args.region
config_file_dir = args.configpath
avidenv = args.avidenv

env = Environment(loader=FileSystemLoader('icinga_templates_dir'))
host_template = env.get_template('host.template')
service_template = env.get_template('service.template')

log_level = 'INFO'
#log_level = 'NOTSET'
logging.basicConfig(level=log_level)

try:
    conn = boto.ec2.connect_to_region(region)
except boto.exception.EC2ResponseError(401, 'AuthFailure'):
    logging.critical('An error occured. Authorization failed when connecting to AWS.')

instance_dictionary = {}
service_dictionary = {}

populate_instance_dictionary(conn, instance_dictionary)
#populate_service_dictionary(instance_dictionary, service_dictionary)
#populate_nrpe(instance_dictionary, service_dictionary)

for file in os.listdir(config_file_dir + '/hosts/'):
    os.remove(config_file_dir + '/hosts/' + file)
write_host_configs(instance_dictionary, config_file_dir, host_template, avidenv)

# for file in os.listdir(config_file_dir + '/services/'):
#     os.remove(config_file_dir + '/services/' + file)
# write_service_configs(service_dictionary, config_file_dir, service_template)

##########
