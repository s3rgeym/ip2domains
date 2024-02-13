# ip2domains

Scans IP addresses and finds domains

Installation:

```bash
pip install ip2domains
```

Usage:

```bash
# help
$ ip2domains -h

# scan domains
$ echo 171.25.225.0/24 | ip2domains --no-banner
{"ip": "171.25.225.10", "domains": ["octogate.online", "*.octogate.online"]}
{"ip": "171.25.225.3", "domains": ["*.octogate.de", "octogate.de"]}
{"ip": "171.25.225.8", "domains": ["*.octogate.de", "octogate.de"]}
{"ip": "171.25.225.18", "domains": ["*.central.octogate.de", "central.octogate.de"]}
{"ip": "171.25.225.78", "domains": ["octogate.online", "*.octogate.online"]}
{"ip": "171.25.225.79", "domains": ["octogate.online", "*.octogate.online"]}
{"ip": "171.25.225.86", "domains": ["sense.hsm.de"]}
{"ip": "171.25.225.73", "domains": ["wichtelwunsch.de", "must4rd.de"]}
{"ip": "171.25.225.56", "domains": ["centraltst.octogate.de", "*.centraltst.octogate.de"]}
{"ip": "171.25.225.58", "domains": ["ntest.ssc.schule"]}
{"ip": "171.25.225.71", "domains": ["*.central.octogate.de", "central.octogate.de"]}
{"ip": "171.25.225.80", "domains": ["octogate.online", "*.octogate.online"]}

# output unique domains
$ echo 171.25.225.0/24 | ip2domains --no-banner | jq -r '.domains[]' | sort | uniq
*.central.octogate.de
central.octogate.de
*.centraltst.octogate.de
centraltst.octogate.de
must4rd.de
ntest.ssc.schule
*.octogate.de
octogate.de
*.octogate.online
octogate.online
sense.hsm.de
wichtelwunsch.de
```
