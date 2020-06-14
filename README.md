# nginxlogparser

### Nginx log parser 

Parse and analyze Ngnix log. Find the slowest http queries.

### Requirements

You need Python 3.0 or later

### Using

Log format:

```
	$remote_addr $remote_user  $http_x_real_ip [$time_local] "$request"  
        $status $body_bytes_sent "$http_referer" ' 
        "$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" 
        $request_time
```

optional arguments:

```      
	--config            configuration file name
```

Config file format:
 
```    
[main]
report_size = 1000
report_dir = "./reports"
log_dir = "./log"
monitor_log_file = "./log_parser.log"

```

`report_size` is optional. It defines how many URLs will be in the result report. Default value is 1000. <br>
`report_dir` is optional. Directory where result reports are put. Default value is "./reports". <br>
`log_dir` is optional. Directory where ngnix logs are. Default value is "./log". <br>
`monitor_log_name` is optional. Monitor log path. By default log is written in stdout. <br>


To be able to see report file correctly you should download `jquery.tablesorter.min.js`.

Run script:

```
python3  main.py [--config='./parser.ini']  
```  

`--config` is optional


## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```




