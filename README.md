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

### How to use
Zelig can be configured using some environment variables:
 * TARGET_SERVER_BASE_URL - url of a real server that is hidden behind zelig (`http://www.httpbin.org`)
 * [optional] ZELIG_CASSETTE_FILE - name of file with request-response logs. Default is `cassette.yml`
 * [optional] ZELIG_PLAYBACK_REPORT - name of file to which we save logs in `playback` mode. Default is `playback_report.yml`
 * [optional] ZELIG_OBSERVE_REPORT - name of file to which we save logs in `observe` mode. Default is `observe_report.yml`
 * [optional] ZELIG_HOST - host of the server. Default is `0.0.0.0`
 * [optional] ZELIG_PORT - port of the server. Default is `8081`
 * [optional] REQUEST_MATCH_ON - space separated list of request properties, that are used to compare requests. Default is `method scheme host port path query body`
 * [optional] RESPONSE_MATCH_ON - space separated list of response properties, that are used to compare responses. Default is `body status`
 * [optional] DEBUG - enables debug level console logs. Set to `1` or `true`

Also you should map your local directory to `/files` directory inside container. This directory will contain all logs writen by Zelig.
