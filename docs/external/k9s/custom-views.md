# K9s: Custom Views Configuration

## Overview

K9s provides for customizing resource columns while in table views. As such you can tell it which columns you would like to display but also which order they should be in.

To surface this feature, you will need to create a new configuration file, namely `$XDG_CONFIG_HOME/k9s/views.yaml`. This file leverages GVR (Group/Version/Resource) to configure the associated table view columns. If no GVR is found for a view the default rendering will take over (ie what we have now). Going wide will add all the remaining columns that are available on the given resource after your custom columns. To boot, you can edit your views config file and tune your resources views live!

Furthermore, you can tailor your `Custom Views` for specific clusters using `$XDG_DATA_HOME/ClusterX/ContextY/views.yaml`.

As of `release v0.40.X` you can specify json parse expressions to further customize your resources rendering.

### Related Videos

- [SneakCast v0.17.0 on The Beach! - Yup! sound is sucking but what a setting!](https://youtu.be/7S33CNLAofk)
- [K9s v0.40.0 -Column Blow- Sneak peek](https://youtu.be/iy6RDozAM4A)

## Column Syntax

The new column syntax is as follows:

```txt
COLUMN_NAME< :json_parse_expression >< |column_attributes >
```

Where `:json_parse_expression` represents an expression to pull a specific snippet out of the resource manifest. Similar to `kubectl -o custom-columns` command. This expression is optional.

> **IMPORTANT!** Columns must be valid YAML strings. Thus if your column definition contains non-alpha chars they must figure with either single/double quotes or escaped.

> **NOTE!** Be sure to watch k9s logs as any issues with the custom views specification are only surfaced in the logs.

## Column Attributes

Additionally, you can specify column attributes to further tailor the column rendering. To use this you will need to add a `|` indicator followed by your rendering bits. You can have one or more of the following attributes:

- `T` -> time column indicator
- `N` -> number column indicator
- `W` -> turns on wide column aka only shows while in wide mode. Defaults to the standard resource definition when present.
- `S` -> Ensures a column is visible and not wide. Overrides `wide` std resource definition if present.
- `H` -> Hides the column
- `L` -> Left align (default)
- `R` -> Right align

> ⚠️ Work in progress... Options and layout may change in future K9s releases as this feature solidifies.

## Example

Here is a sample views configuration that customize a pods and services views.

```yaml
# $XDG_CONFIG_HOME/k9s/views.yaml
views:
  # Alters the pod view column layout. Uses GVR as key
  v1/pods:
    # Overrides default sort column
    sortColumn: AGE:asc
    columns:
      - AGE
      - NAMESPACE|WR                                     # => Specifies the NAMESPACE column to be right aligned and only visible while in wide mode
      - ZORG:.metadata.labels.fred\.io\.kubernetes\.blee # => extract fred.io.kubernetes.blee label into it's own column
      - BLEE:.metadata.annotations.blee|R                # => extract annotation blee into it's own column and right align it
      - NAME
      - BLEE:.metadata.annotations.blee|R                # => extract annotation blee into it's own column and right align it
      - IP
      - NODE
      - STATUS
      - READY
      - MEM/RL|S                                         # => Overrides std resource default wide attribute via `S` for `Show`
      - '%MEM/R|'                                        # => NOTE! column names with non alpha names need to be quoted as columns must be strings!

  v1/pods@fred:                                          # => As of v0.40.6, you can now further customize pod view for a specific namespace
    # Overrides default sort column
    sortColumn: NAME:asc
    columns:
      - NAME|WR
      - AGE

  v1/pods@fred:                                          # => New v0.40.6! Customize columns for a given resource and namespace!
    columns:
      - AGE
      - NAME|WR

  v1/pods@kube*:                                         # => New v0.40.6! You can also specify a namespace using a regular expression.
    columns:
      - NAME
      - AGE
      - LABELS

  cool-kid:                                              # => New v0.40.8! You can also reference a specific alias and display a custom view for it
    columns:
      - AGE
      - NAMESPACE|WR

  # Alters the service view column layout
  v1/services:
    columns:
      - AGE
      - NAMESPACE
      - NAME
      - TYPE
      - CLUSTER-IP
```

## License

© 2025 Imhotep Software LLC. All materials licensed under [Apache v2.0](http://www.apache.org/licenses/LICENSE-2.0)
