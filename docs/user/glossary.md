# Glossary

This glossary provides definitions for terms used throughout the conda-forge-converter documentation.

## A

### Anaconda

A distribution of Python and R for scientific computing that includes pre-installed packages. The conda-forge-converter tool helps migrate environments from Anaconda's default channels to conda-forge.

### Anaconda Channel

The default package repository used by Anaconda, containing packages that are built, reviewed, and maintained by Anaconda, Inc.

## B

### Batch Conversion

The process of converting multiple conda environments at once using the `--batch` flag.

### Batch Size

The number of packages installed in a single operation, controlled by the `--batch-size` option. Larger batch sizes can improve performance but may increase the risk of conflicts.

## C

### Channel

A repository of conda packages. The main channels are "defaults" (Anaconda) and "conda-forge".

### CLI (Command Line Interface)

The text-based interface used to interact with the conda-forge-converter tool through commands typed in a terminal or command prompt.

### conda

A package, dependency, and environment management system that runs on Windows, macOS, and Linux.

### conda-forge

A community-led collection of recipes, build infrastructure, and distributions for the conda package manager.

### Conversion

The process of migrating a conda environment from Anaconda's default channels to conda-forge channels.

## D

### Dependency

A package that another package requires to function properly.

### Dry Run

A mode that shows what would happen during conversion without making any actual changes, activated with the `--dry-run` flag.

## E

### Environment

A directory that contains a specific collection of conda packages. Environments isolate different projects and their dependencies.

### Environment Variable

A dynamic-named value that can affect the way running processes behave on a computer.

## F

### Fast Solver

An alternative dependency resolver (libmamba/mamba) that provides faster resolution of package dependencies compared to the default conda solver.

## L

### libmamba

A fast, dependency solver implementation used by the conda-forge-converter when the `--use-fast-solver` option is enabled.

## O

### Ownership Preservation

The feature that maintains the original user and group ownership of files when converting environments as root, controlled by the `--no-preserve-ownership` flag.

## P

### Package

A bundle of software to be installed. In conda, a package is a compressed tarball file (.tar.bz2 or .conda) containing system-level libraries, Python modules, executable programs, or other components.

### Pattern Matching

Using wildcards to match multiple environment names when using batch conversion, controlled by the `--pattern` option.

### Python Version

The version of Python used in a conda environment, which can be specified during conversion with the `--python-version` option.

## R

### Root User

A user account with administrative privileges in Linux/Unix systems. Running conda-forge-converter as root allows converting environments owned by different users.

## S

### SELinux (Security-Enhanced Linux)

A Linux kernel security module that provides a mechanism for supporting access control security policies. May affect conda-forge-converter when running as root.

### Source Environment

The original Anaconda environment that will be converted, specified with the `-s` or `--source` option.

## T

### Target Environment

The new conda-forge environment that will be created during conversion, specified with the `-t` or `--target` option.

## V

### Verbose Mode

A mode that provides detailed output during conversion, activated with the `--verbose` flag.

## Y

### YAML (YAML Ain't Markup Language)

A human-readable data serialization standard used for configuration files in conda. Environment files are often stored in YAML format with a .yml or .yaml extension.
