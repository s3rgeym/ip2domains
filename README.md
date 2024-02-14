# ip2domains

Scans IP addresses and finds domains. Domain names are extracted from SSL certificates. This method does not guarantee 100% finding of all domains. You can also use the method of obtaining a domain name through a reverse DNS lookup, but 99% of domains do not contain a PTR record:

```bash
$ dig +short example.com
93.184.216.34
# NO PTR
$ php -r 'echo(gethostbyaddr("'$(dig +short example.com)'"));'
93.184.216.34  # <-- fail: if successful there should be example.com
```

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

# Scan domains
# KLM is sucks. Don't use these f*gots. Give me back my money, assholes!
$ echo 171.21.120.0/22 | ip2domains --no-banner

# List unique domains
$ echo 171.21.120.0/22 | ip2domains --no-banner | jq -r '.domains[]' | sort | uniq

# Remember that not all domains listed in the certificate actually use this IP
$ dig +short af-klm.com
171.21.122.81

$ dig +short bluebiz.com
52.166.78.97
```
