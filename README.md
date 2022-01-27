# History on Demand - Python SDK
This is a small Python package with a single module / script for submitting Jobs read from a CSV to HoD Archive via its REST API.

## Documentation

* [History on Demand (HoD) - Archive](https://docs.google.com/document/d/1S21137fFwX9o7ZqT2kjqwjgikmPUNOpmkEO6ex7ts_U)

## Quick start

You'll need:

* [An IBM Cloud account and Cloud Object Storage (COS) instance](https://docs.google.com/document/d/1S21137fFwX9o7ZqT2kjqwjgikmPUNOpmkEO6ex7ts_U/edit#heading=h.t3a08xhznh4c)
* A valid API key registered with HoD Archive
* A jobs CSV file

## Jobs CSV

The CSV must contain a header line that includes a ``startDateTime``, ``endDateTime``, ``location``, ``format``, ``units``, and ``resultsLocation``. Header names are case-insensitive and may contain underscores, hyphens, and spaces. Column order does not matter.

CSV values should match the formats expected by the HoD Archive API. Because most location expressions contain commas, it's a good idea to surround that value in quotes. For more details, see the HoD Archive documentation and [sample-jobs.csv](./sampledata/sample-jobs.csv) in the `sampledata` directory.

## Example usage

```shell
$ ./hodarchive/hodarchive.py --jobs ./sampledata/sample-jobs.csv --api-key 1234
Job (cbb54705-82fd-4919-baed-6ff02b175ade) submitted from line 1.
Job (6b6b79cb-1427-4fbb-ad49-40baedef3fd3) submitted from line 2.
Job (0a495e7a-add2-4f8c-8fbf-cc1080e8c26b) submitted from line 3.
Job (4d536173-a418-47c1-8000-907f537897c1) submitted from line 4.
Job (6b6b79cb-1427-4fbb-ad49-40baedef3fd3) complete. rowsReturned=209 usage=209
Job (0a495e7a-add2-4f8c-8fbf-cc1080e8c26b) complete. rowsReturned=72 usage=3
Job (4d536173-a418-47c1-8000-907f537897c1) complete. rowsReturned=1 usage=1
Job (cbb54705-82fd-4919-baed-6ff02b175ade) complete. rowsReturned=6 usage=1

Results:

Jobs run: 4, Errors: 0
```

## Questions and support

For support, please contact twcapi@us.ibm.com.

## Open source @ IBM

Find more open source projects on the [IBM Github](https://github.com/IBM) page.

## License

This SDK is distributed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). To read the full text of the license, see [LICENSE](./LICENSE).
