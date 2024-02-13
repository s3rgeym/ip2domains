# ip2domains

Scans IP addresses and finds domains. Domain names are extracted from SSL certificates. This method does not guarantee 100% finding of all domains. You can also use the method of obtaining a domain name through a reverse DNS lookup, but 99% of domains do not contain a PTR record.

The reason for developing this tool was that many Internet services provide unreliable results:

![image](https://github.com/s3rgeym/ip2domains/assets/12753171/d0f5728c-c9ff-480f-b830-13595b386c06)

Installation:

```bash
pip install ip2domains
```

Usage:

```bash
# help
$ ip2domains -h

# scan domains
$ echo 0.0.0.0/0 | ip2domains --no-banner

# list unique domains
$ echo 0.0.0.0/0 | ip2domains --no-banner | jq -r '.domains[]' | sort | uniq
```
