## Zelig
One tool to test all your APIs

### Description
Zelig provides a possibility to test your local and remote APIs.
It could work in 4 modes:
 * `record`
 * `serve`
 * `playback`
 * `observe`

#### Record
In `record` mode Zelig propagates all incoming requests to the specified server. Also it logs all request-response pairs.
#### Serve
In `serve` mode Zelig do not propagates incoming requests. Instead it returns previously recorded responses. Also it closes
the connection on unknown requests.
#### Playback
In `playback` mode Zelig reads all recorded request-response pairs and send all requests again. Then it compares old and new responses and logs mismatches
#### Observe
In `observe` mode Zelig works like in `record` mode, but it also logs all unknown incoming requests and all mismatched responses.

### Test summary
Zelig stores some basic test info when running in `playback` and `observe` modes. It is stored in `.meta` file in the report's directory.
You can see human readable tests summary by running following command
```bash
docker run -v <files_directory>:/files zelig summary <report_folder>
```
*example*
```bash
docker run -v ~/tmp/zelig-test:/files zelig summary playback_report_2017-04-19_08-37-39
```

### How to use
Run `docker run -v <files_directory>:/files -p <host_port>:<container_port> --env-file ./env zelig`
 * `<files_direcotry>` is a directory that is required by Zelig to store data/reports,
 * `<host_port>` is a port on the host machine that will be used to communicate with Zelig.
 * `<container_port>` is a port inside the container. It should be equal to the `ZELIG_PORT` env variable if it specified (default is `8081`).
 * `env` is a name of file that contains environment variables which Zelig use.





Zelig can be configured using environment variables:
 * __ZELIG_MODE__ - name of the current Zelig mode. Should be one of `record`, `playback`, `serve`, `observe`
 * __TARGET_SERVER_BASE_URL__ - url of a real server that is hidden behind zelig (`http://www.httpbin.org`)
 * __ZELIG_DATA_DIRECTORY__ - name of directory where to store data(request-response files). Autogenerated if absent. 
 Generation template is `data_%Y-%m-%d_%H-%M-%S`. *Optional in `record` mode.*
 * [optional] __ZELIG_PLAYBACK_REPORT_DIRECTORY__ - name of directory to which we save logs in `playback` mode. Default is `playback_report_%Y-%m-%d_%H-%M-%S`
 * [optional] __ZELIG_OBSERVE_REPORT_DIRECTORY__ - name of directory to which we save logs in `observe` mode. Default is `observe_report_%Y-%m-%d_%H-%M-%S`
 * [optional] __ZELIG_HOST__ - host of the server. Default is `0.0.0.0`
 * [optional] __ZELIG_PORT__ - port of the server. Default is `8081`
 * [optional] __REQUEST_MATCH_ON__ - space separated list of request properties, that are used to compare requests. Default is `method scheme host port path query body`
 * [optional] __RESPONSE_MATCH_ON__ - space separated list of response properties, that are used to compare responses. Default is `body status`
 * [optional] __DEBUG__ - enables debug level console logs. Set to `1` or `true`

Also you should map your local directory to `/files` directory inside container. This directory will contain all logs writen by Zelig.

Example `docker-compose.yml` file
 ```yaml
 version: "3"
 services:
     z1:
         image: zelig:latest
         ports: ["8081:8081"]
         volumes:
             - ~/tmp/zelig-test/test_files:/files
         environment:
             - ZELIG_MODE=record
             - TARGET_SERVER_BASE_URL=http://www.httpbin.org
 ```

### Notes
1. Zelig will interrupt connection in `serve` mode if incoming request is unknown so you need to handle connection errors. It also will save log as for the usual request but will use 490 response code to signal that request was not recognized.
2. Zelig always force error responses to not match each other. So if we recorded error in `record` mode and then encountered the same error in `playback` or `observe` modes report will be generated.

### How to build container from sources
1. [Install Docker](https://docs.docker.com/engine/installation/#platform-support-matrix)
2. Clone project from Github: `git clone https://github.com/acceradev/zelig.git <directory>` or `git clone git@github.com:acceradev/zelig.git <directory>`. Project will be cloned to the specified `<directory>`
3. Run `docker build -f <directory>/Dockerfile -t zelig --no-cache`. This will build a docker image with a name `zelig` from sources.


