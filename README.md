# MDN spec links

This space holds JSON files for individual specs; each file contains data
which maps fragment IDs from a particular spec to MDN articles which have
*Specifications* sections that contain links to that spec and fragment ID.

The names of the JSON files match the corresponding spec-shortname keys
used in the data provided by https://www.specref.org/

The `SPECMAP.json` file has a complete mapping of spec URLs to the
corresponding filenames here.

The JSON files are built with data from
https://github.com/w3c/browser-compat-data, a fork of
https://github.com/mdn/browser-compat-data (aka “BCD”).

The anticipation is that the data in the JSON files will be useful for
doing things like adding MDN annotations to specs, and implementing
MDN-annotation-injecting features in Bikeshed, Respec and other such tools.

## ⚠ Warning

This is all experimental and unsupported at this point. The format of the
JSON files is still highly open to being changed. The data in the files is
being provided here in the hope that it will prove useful to spec editors
and others. If it does, then we’ll eventually settle on a stable format.

### Adding data

All JSON files in the root directory here are generated files. So you don’t
want to edit them directly; instead you’d need to edit the upstream data at
https://github.com/mdn/browser-compat-data and
https://developer.mozilla.org/docs/Web articles.

The files in the `.local` directory are static files, for handling cases
where an MDN article has links to a particular spec but that MDN article
doesn’t have any corresponding data in BCD. The structure of each `.local`
file is similar a simplification of the structure of the JSON files in the
root directory — with the `summary` and `title` fields omitted, and with a
string for the value of the `support` field. Use that string to specify
a feature whose `support` data should be borrowed and used as the `support`
value for the spec ID give in the `.local` file.

