# DOCX source corpus v1

Original synthetic FORMA examples and 8×8 solid-color PNG/JPEG plus a minimal one-page
PDF, dedicated to the public domain under CC0-1.0. No third-party document content.
Images were authored offline; Pillow is an authoring tool, not a project dependency.

manifest.json lists source files, assets, support levels, expected structural results
and warning locations. Every case is standalone; paths resolve from this directory.
Use refs.bib with citeproc for DX-013. No external fetch, custom filters or Lua.

Static tests check corpus integrity only. BE-040/042 must run actual conversion and
structural golden assertions inside the ADR-0004 sandbox. Do not execute these TeX
sources with a host compiler. Unsupported fixtures deliberately exercise warnings.
