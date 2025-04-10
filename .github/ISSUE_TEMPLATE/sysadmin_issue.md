---
name: System Administrator Issue
about: Report issues specific to system administration or CLI usage
title: '[SYSADMIN] '
labels: [sysadmin, cli, needs-triage]
assignees: ''
---

## System Administrator Issue

<!-- Describe the issue you're experiencing as a system administrator -->

## Environment Information

<!-- Complete the following information about your environment -->

- **OS**: <!-- e.g., Ubuntu 22.04, CentOS 8, RHEL 9 -->
- **Python Version**: <!-- e.g., 3.10.4 -->
- **Package Version**: <!-- e.g., 1.2.3 -->
- **Conda Version**: <!-- e.g., 23.3.1 -->
- **Installation Method**: <!-- e.g., pip, conda, from source -->
- **Running as Root**: <!-- Yes/No -->
- **SELinux Enabled**: <!-- Yes/No/N/A -->
- **Multi-user Environment**: <!-- Yes/No -->

## Command or Operation

<!-- Describe the command or operation you were trying to perform -->

<!-- Include the exact command you ran -->

```bash
# Example command
sudo conda-forge-converter -s myenv -t myenv_forge
```

## Expected Behavior

<!-- Describe what you expected to happen -->

## Actual Behavior

<!-- Describe what actually happened -->

<!-- Include any error messages, stack traces, or logs -->

<details>
<summary>Error Messages/Logs</summary>

```
Paste your logs here
```

</details>

## System Configuration

<!-- Provide relevant system configuration details -->

<!-- For example: file permissions, mount options, etc. -->

<details>
<summary>System Configuration</summary>

```
# Example: Output of relevant commands
$ ls -la /path/to/environment
$ mount | grep conda
$ id -a
```

</details>

## Troubleshooting Steps

<!-- Describe any troubleshooting steps you've already taken -->

1.
1.
1.

## Impact

<!-- Describe the impact of this issue on your operations -->

<!-- For example: "Prevents automated environment conversion for 50 users" -->

## Additional Context

<!-- Add any other context about the problem here -->

<!-- For example: Does the issue happen consistently or intermittently? -->

<!-- Have you tried any workarounds? -->

## Checklist

<!-- Put an x in the boxes that apply -->

- [ ] I've searched for similar issues before creating this one
- [ ] I've included all the information requested above
- [ ] I've included error messages and logs if applicable
- [ ] I've tried to reproduce the issue with the latest version
- [ ] I've checked permissions and ownership of relevant files
