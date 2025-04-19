# Running as Root

When running on a Linux server, you may need to convert environments owned by different users. This requires running the converter as root.

## Automatic Ownership Preservation

When running as root, the converter will automatically preserve the original ownership of the source environment. This means that the new conda-forge environment will have the same owner and group as the original Anaconda environment, despite being created by the root user.

For example:

```bash
# Environment 'data_science' is owned by user 'analyst'
sudo conda-forge-converter -s data_science -t data_science_forge
# The new 'data_science_forge' environment will also be owned by 'analyst'
```

This feature is particularly useful in multi-user systems where you want to maintain the original ownership of environments when converting them.

## Disabling Ownership Preservation

If you want to create environments owned by root even when running as root, you can use the `--no-preserve-ownership` flag:

```bash
sudo conda-forge-converter -s data_science -t data_science_forge --no-preserve-ownership
# The new 'data_science_forge' environment will be owned by root
```

## Batch Conversion

The ownership preservation also works when converting multiple environments in batch mode:

```bash
# Convert all environments and preserve their original ownership
sudo conda-forge-converter --batch
```

Or with the option disabled:

```bash
# Convert all environments but make them owned by root
sudo conda-forge-converter --batch --no-preserve-ownership
```

## Security Considerations

When running as root:

- Be aware that this gives the converter the ability to change file ownership
- Consider using a dedicated service account instead of root when possible
- Ensure proper filesystem permissions are configured
- Be cautious when converting environments in system directories

## Troubleshooting

### Permission Issues

If you encounter permission issues even when running as root, it might be due to:

1. SELinux policies restricting access
1. Filesystem restrictions (e.g., NFS with root_squash)
1. Immutable file attributes

In these cases, you may need to:

- Temporarily disable SELinux (`sudo setenforce 0`)
- Check filesystem mount options
- Check for immutable attributes (`lsattr`)

### Ownership Not Preserved

If ownership is not being preserved as expected:

1. Verify you're running as root (`id -u` should return 0)
1. Make sure you haven't used the `--no-preserve-ownership` flag
1. Check if the source environment exists and is accessible
1. Ensure the target environment name doesn't already exist
