#!/usr/local/bin/ruby

# Ruby script to download metrics from Jenkins
# Jason Fowler March 2015

# cron for job:
#*/30 * * * * /usr/local/bin/ruby /home/ubuntu/buildmetrics/buildmetrics.rb

require 'json'
require 'jenkins_api_client'
require 'open-uri'
require 'erb'
require 'mysql'
require 'logger'

$LOG = Logger.new('bmapp.log', 0, 100 * 1024 * 1024)
 
#$LOG.level = Logger::ERROR
$LOG.level = Logger::DEBUG

# Function Section

def get_builds(dbjob) 
	gb = @client.job.get_builds(dbjob)
	gb.each do |build|
		buildnumber = build['number']
		get_details dbjob, buildnumber
	end
	return
end

def get_details(dbjob, buildnumber)

job_details = @client.job.get_build_details(dbjob, buildnumber)
	uniquejob = job_details['fullDisplayName']
  jobname = job_details['fullDisplayName'].split.last
  duration = job_details['duration']
  timedate = job_details['timestamp']
  status = job_details['result']
	builds_by_branch_name = job_details['actions'].detect {|x| x['buildsByBranchName'] }
	
	if builds_by_branch_name
		bbbn = job_details['actions'].detect {|x| x['buildsByBranchName'] }
		branch =
			if bbbn.empty?
				nil
			else
				bbbn['lastBuiltRevision']['branch'].first['name'].gsub(%r|^origin/|, "")
			end
	end

	$LOG.debug("dbjob: #{dbjob}, buildnumber: #{buildnumber},unique: #{uniquejob}, jobname: #{jobname}, duration: #{duration}, timedate: #{timedate}, status: #{status}, branch_builds: #{builds_by_branch_name}")  

	job_sql = @build_db.prepare "insert into buildinfo (uniquejob, dbjob, jobname, branch, buildnumber,
		status, duration, timedate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		on duplicate key update dbjob=VALUES(dbjob), jobname=VALUES(jobname), branch=VALUES(branch), buildnumber=VALUES(buildnumber),
		status=VALUES(status), duration=VALUES(duration), timedate=VALUES(timedate);"

	job_sql.execute uniquejob, dbjob, jobname, branch, buildnumber, status, duration, timedate
	return
end

# Main Section

@client = JenkinsApi::Client.new(server_ip: 'my_jenkins_server',
     username: '', password: '')

@build_db = Mysql.new('webtest2.stage.us-east-1.hootops.com', 'bmadmin', 'xxxxxxxxxx', 'buildmetrics')  

# Get all Dashboard jobs, loop through to get build # and url
#one job from dashboard jobs
#dbjobs = @client.job.list("Dashboard", "Dashboard-Build")
# all dashboard jobs

dbjobs = ["Dashboard", "Dashboard-Build", "Dashboard-Deploy-Production", "Dashboard-Deploy-Production-Candidates", "Dashboard-Deploy-Production-Check", 
	"Dashboard-Deploy-Staging", "Dashboard-Deploy-Staging-Candidates",
	"Dashboard-JS-Documentation", "Dashboard-Metrics", "Dashboard-Post-Deploy-Production", 
	"Dashboard-SOA-Test-API", "Dashboard-Test-API", "Dashboard-Test-Automation", 
	"Dashboard-Test-Documentation", "Dashboard-Test-JS", "Dashboard-Test-JS-Casper", 
	"Dashboard-Test-JS-Casper-MW", "Dashboard-Test-Mobile", "Dashboard-Test-PHP-1", 
	"Dashboard-Test-PHP-2", "Dashboard-Test-PHP-3"]

dbjobs.each do |dbjob|
	get_builds(dbjob)
end
@build_db.close
