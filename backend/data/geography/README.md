# Local world city index

Source: [GeoNames daily gazetteer](https://download.geonames.org/export/dump/),
`cities500.zip`, `admin1CodesASCII.txt`, `countryInfo.txt`, retrieved 2026-10-23.
© GeoNames contributors, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Commercial reuse and redistribution are permitted with attribution.

The transformed SQLite/FTS5 index preserves city identifiers, names and aliases,
country, administrative region, coordinates and timezone. It contains settlements
with population over 500 and administrative seats from the source. It is not a
complete historical list of every settlement. Manual entry remains available.
Names/boundaries follow the source; no claim of accuracy or completeness is made.

Build with `scripts/build-city-index.py` (arguments in its docstring). Input hashes
and row count are in `cities.json`. Search uses this read-only local file; no user
query, account data, birth date, or location is sent to GeoNames. The in-process
query cache is bounded to 128 entries and is not persisted.
