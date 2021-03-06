# python-aws-reboot
### Requirements

- boto3
- tabulate
- click


Reboots instances based on one or more name tags

```python reboot.py name1 name2 name3```
```
usage: reboot.py [-h] [--region REGION] [--verbose] [--dry-run] [--batch BATCH] [--wait WAIT] [--no-confirm] [--no-reboot] Name [Name ...]

Process some integers.

positional arguments:
  Name             instance Name tag to reboot

optional arguments:
  -h, --help       show this help message and exit
  --region REGION
  --verbose        Enable Verbose Output
  --dry-run        Enable Dry Run
  --batch BATCH    Batch Size
  --wait WAIT      wait time
  --no-confirm     Disable Confirmation
  --no-reboot      Disable reboot
  ```