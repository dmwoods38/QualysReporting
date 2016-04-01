# QualysReporting
Tool to help with automation of Qualysguard scan report download and delivery.

Disclaimer: This is not associated with Qualys in any way, this is just the
skeleton of something I have created that fits my needs.

Apologies for the poor packaging and coding. I will be improving both in the future.

# Versions
## v 0.2.3
More detailed setup instructions to come.

### Getting Started
The easiest way to get up and running is to use Docker, I have created a basic
Dockerfile [here](https://github.com/dmwoods38/QualysReportingDocker). The way
I've built stuff it can get pretty annoying without docker at the moment.

Since this is/was intended primarily to deliver scan reports (e.g. the scan results
that can be obtained from the Quick Actions menu in Qualysguard Vulnerability Management)
One must first create a scan report template that best approximates these reports.
Note that templates with other options can be used, but issues related to other templates
may not be fixed.

#### Creating the Scan Report Template
These are the options that I have found that gives a report closest to the scan results
from the Quick Actions menu.

* Findings
  * Use "Scan Based Findings"  
* Display
  * Report Summary
    * Summary of Vulnerabilities
      * Check: "Text Summary"
    * Graphics
      * Check: "Vulnerabilities by Severity" and "Operating Systems Detected"
  * Detailed Results
    * Sorting
      * Sort by "Host"
  * Display Host Details Include the following detailed results in the report
    * Check: "Vulnerability Details"
      * Check: "Threat", "Impact"
      * Solution:
        * Check: "Patches and Workarounds" and "Virtual Patches and Mitigating Controls"
      * Check: "Compliance", "Exploitability", "Associated Malware", "Results"
    * Check: "Appendix"
* Filter
  * Selective Vulnerability Reporting
    * Use "Complete"
  * Included Operating Systems
    * Select all
  * Vulnerability Filters
    * Status
      * Check: "New", "Active", "Re-Opened", "Fixed"
    * State
      * Confirmed Vulnerabilities
        * Check: "Active", "Disabled"
      * Potential Vulnerabilities
        * Check: "Active", "Disabled"
      * Information Gathered
        * Check: "Active", "Disabled"
  * Included Categories
    * Select all
* Services and Ports
  * Add all to "Available Services"
  
Once you have created the report template, take note of the Template ID, it will
need to be added to the settings file.

#### User Requirements
A Qualys user that has API access is required.
Given the way the password is stored it is advisable to create a separate user
that only has API access, rotate passwords regularly and give the user the 
least privileges.

The privileges that I have found that work are the following:
* User Role
  * User Role
    * Reader
  * Allow Access to
    * Check: "API"
  * Business Unit
    * This will depend on how your account is setup, I have gone with "Unassigned"
* Asset Groups
  * Any Asset groups that will be reported on
* Permissions
  * Check: "Manage VM Module"

#### Settings Configuration
Settings are stored in config/settings.py. For an example take a look at the
settings-example.py file in the config folder.

* QualysAPI - Qualys settings here
  * username - username of the user who will retrieve reports.
  * password - password of the user who will retrieve reports.
  * url - The URL for the Qualys API endpoint for your account.
  * scan_template - This is the template ID from the scan report template created
                    above
* ELASTICSEARCH - Elasticsearch config if the destination is "elasticsearch"
* AWS - AWS config if using an AWS ES instance for elasticsearch
* report_folder - Destination for where the reports are stored for destination 
                  of "local", temp storage if destination is "email"
* archive_folder - Destination where reports are stored after being sent out
                   via email
* unprocessed_log - Log file, not really very useful at the moment
* email_from - Sender email for "email" destination
* smtp_server - SMTP server for "email" destination
* destination - "local" to save reports locally only, "email" will email reports
                and then move them to the archive_folder, "elasticsearch" will 
                JSONify the vulnerabilities and send them to an Elasticsearch instance.

#### Report Scheduling Configuration
Currently Report schedules are stored in a JSON file in config/reports.json. 
For an example take a look at the reports-example.json file in the config folder.

Schedules are stored as an array of JSON objects, and then are added to a postgresql
database using the add_scheduled_reports.py script. This is one of the reasons why
Docker is best right now, I haven't made a way to update the schedule other than
rebuilding the Docker image.

Schedule Object configuration:
* email_subject - This is the title for the scan report and also the subject for
                  email if the destination is "email".
* asset_groups - If you want to limit a scan report to specific asset groups, 
                 place them here, otherwise leave this as an empty string.
* output_pdf - If you want the report sent out as a PDF set to "True" otherwise
               "False".
* output_csv - If you want the report sent out as a CSV set to "True" otherwise
               "False".
* scan_title - The title of the scheduled scan in Qualys, used to retrieve the reports.
* email_list - The recipients of email reports, unfortunately due to the way this was 
               developed, this needs to be set to something even if destination isn't
               "email".
* list_name - friendly name to identify the email list of recipients, same idiosyncrasy 
              as the email_list field.
* day_of_month - use this for monthly reports.
* day_of_week - use for weekly reports days are numbered 0(Monday)-6(Sunday).

## v 0.2.0
Stuff actually works now. Setup instructions and dockerfile/containers to come.

## v 0.1.0
This is really just a skeleton of something that I have gotten working with
specific configurations that I will not really outline here. I am expecting
this to be the jumping off point before I refactor everything and make this
much more user-friendly and manageable. The way I currently had it set up
is going to end up being a nightmare for me as I add more scans to the
scheduling.

That said, if there is any desire to get this setup before I have made this
easier to setup I can definitely provide instructions.

# Requirements
## Python Packages
* Requests
* Elasticsearch

## Other requirements
* pip to install python packages


