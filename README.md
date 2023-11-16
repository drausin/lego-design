# Data-driven Lego design

## Fetching data

The script can be run from the command line with various commands. Here are some examples:

### ldraw-parts

The `ldraw-parts` command downloads and extracts a zip file from a specified URL. The data is saved in the local data directory.

Example:

```bash
python src/data/fetch.py ldraw-parts --data-dir ./data
```

This will download the zip file and extract its contents into the `./data` directory.
