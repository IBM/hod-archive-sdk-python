#!/usr/bin/env python3
#  Copyright 2022 IBM Corp. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

""" Module for submitting Jobs read from a CSV to HoD Archive via its REST API.

The CSV must contain a header line that includes a ``startDateTime``, ``endDateTime``, ``location``, ``format``,
``units``, and ``resultsLocation``. Header names are case-insensitive and may contain underscores, hyphens, and spaces.
Column order does not matter.

CSV values should match the formats expected by the HoD Archive API. Because most location expressions contain commas,
it's a good idea to surround that value in quotes. For more details, see the HoD Archive documentation at
https://ibm.co/2YEa7Q1 and `sample-jobs.csv` in the `sampledata` directory.

Example usage::
    ./hodarchive.py --jobs=../sampledata/sample-jobs.csv --api-key=1234

Dependencies:
    requests - https://docs.python-requests.org
"""

import argparse
import csv
import json
import time
from collections import namedtuple, deque
from typing import Any, Union, Generator, Dict, Deque

import requests

_HOD_ARCHIVE_URL = 'https://api.weather.com/v3/wx/hod/r1/archive'
_HOD_ACTIVITY_URL = 'https://api.weather.com/v3/wx/hod/r1/activity'

ArchiveRequest = namedtuple(
    'ArchiveRequest',
    ['start_date_time', 'end_date_time', 'location', 'format', 'units', 'results_location']
)


class Job:
    def __init__(self, line_number: int, request: ArchiveRequest):
        self.line_number = line_number
        self.request = request
        self.info: Dict[str, Any] = {}


def _main():
    ap = argparse.ArgumentParser(prog='hodarchive.py')
    ap.add_argument('--api-key', metavar='KEY', help='A valid API key registered with HoD Archive', required=True)
    ap.add_argument('--jobs', metavar='JOBS.csv', help='Jobs CSV file', required=True)
    args = ap.parse_args()

    run_jobs(args.api_key, args.jobs)


def run_jobs(api_key: str, jobs_file_path: str):
    """ Run all jobs from the CSV identified by ``jobs_file_path``
    Args:
        api_key: A valid API key registered with HoD Archive
        jobs_file_path: A CSV with rows defining HoD Archive jobs to be submitted. Each row should always contain a
         ``startDateTime``, ``endDateTime``, ``location``, ``format``, ``units``, and ``resultsLocation``.
    """

    completions = 0
    errors = 0

    jobs_in_progress = deque()
    for job in yield_jobs(jobs_file_path):
        try:
            job.info = post_with_retry(api_key, job.request)
            notify_job_submitted(job)
            jobs_in_progress.appendleft(job)

            new_completions, new_errors = clean_completed(api_key, jobs_in_progress)
            completions += new_completions
            errors += new_errors
        except requests.HTTPError as e:
            errors += 1
            handle_error(e.response)

    # All jobs submitted. Now wait for the last of them to finish.
    while jobs_in_progress:
        new_completions, new_errors = clean_completed(api_key, jobs_in_progress)
        completions += new_completions
        errors += new_errors
        time.sleep(10.0)

    print('\nResults:')
    print(f'\nJobs run: {completions + errors}, Errors: {errors}')


def yield_jobs(jobs_file_path: str) -> Generator[Job, None, None]:
    """ Yield jobs read from the file at ``jobs_file_path``
    Args:
        jobs_file_path: A file path to the jobs CSV

    Yields:
        Each record from the jobs CSV translated to a ``Job``
    """

    with open(jobs_file_path) as jobs_file:
        jobs_csv = csv.DictReader(jobs_file, skipinitialspace=True)
        for index, row in enumerate(jobs_csv):
            row_number = index + 1
            request = to_request(row)
            yield Job(row_number, request)


def post_with_retry(api_key: str, req: ArchiveRequest) -> Dict[str, Any]:
    """ Submit an ``ArchiveRequest`` to HoD Archive while handling the 429 backpressure
    Args:
        api_key: The api key to use
        req: The ``ArchiveRequest`` to submit

    Returns:
        The job info returned by the HoD Archive API

    Raises:
        requests.HTTPError
    """

    while True:
        try:
            return post(api_key, req)
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                time.sleep(int(e.response.headers.get('Retry-After', '10')))
            else:
                raise


def post(api_key: str, req: ArchiveRequest) -> Dict[str, Any]:
    """ Submit an ``ArchiveRequest`` to HoD Archive.
    Args:
        api_key: The api key to use
        req: The ``ArchiveRequest`` to submit

    Returns:
        The job info returned by the HoD Archive API

    Raises:
        requests.HTTPError
    """

    params = {'apiKey': api_key}
    response = requests.post(
        _HOD_ARCHIVE_URL,
        headers={'Content-Type': 'application/json'},
        params=params,
        data=json.dumps({
            'location': req.location,
            'startDateTime': req.start_date_time,
            'endDateTime': req.end_date_time,
            'format': req.format,
            'units': req.units,
            'resultsLocation': req.results_location
        }))
    response.raise_for_status()  # raise error if one occurred
    body = read_response_body(response)
    return body['job']


def clean_completed(api_key: str, jobs: Deque[Job]):
    """ Update each job's status and clear completed jobs
    Args:
        api_key: The api key to use
        jobs: A deque of active jobs
    """

    complete_count = 0
    error_count = 0
    for i in range(len(jobs)):
        job = jobs.pop()  # pop right
        job.info = get_status(api_key, job.info['jobId'])
        if 'complete' == job.info['jobStatus']:
            complete_count += 1
            notify_job_complete(job)
        elif 'error' == job.info['jobStatus']:
            error_count += 1
            notify_job_errored(job)
        else:
            jobs.appendleft(job)
    return complete_count, error_count


def get_status(api_key: str, job_id: str) -> Dict[str, Any]:
    """ Get the status of a submitted job.
    Args:
        api_key: The api key to use
        job_id: The ID of the job to check

    Returns:
        The returned job status
    """

    params = {'apiKey': api_key, 'jobId': job_id}
    response = requests.get(
        _HOD_ACTIVITY_URL,
        headers={'Content-Type': 'application/json'},
        params=params
    )
    response.raise_for_status()  # raise error if one occurred
    return read_response_body(response)


def to_request(row: dict) -> ArchiveRequest:
    """ Convert a CSV record to an ``ArchiveRequest`` """
    normalized_row = {}
    for k, v in row.items():
        normalized_row[normalize_key(k)] = v
    return ArchiveRequest(**normalized_row)


def normalize_key(key: str):
    """ Normalize CSV header values """
    key = key.lower().replace('_', '').replace('-', '').replace(' ', '')
    return {
        'startdatetime': 'start_date_time',
        'enddatetime': 'end_date_time',
        'resultslocation': 'results_location'
    }.get(key, key)


def handle_error(response: requests.Response):
    """ Handle an error response from the API """
    body = read_response_body(response)
    print(f'Error ({response.status_code} - {response.reason}): {body}')


def read_response_body(response: requests.Response) -> Union[Dict[str, Any], str]:
    """ Read response body as a ``dict`` if possible, else as a ``str`` """
    body = response.content.decode('utf-8')
    try:
        body = json.loads(body) if response.content else None
    except json.decoder.JSONDecodeError:
        pass
    return body


def notify_job_submitted(job: Job):
    """ Print a message indicating that the job was successfully submitted """
    job_id = job.info['jobId']
    print(f'Job ({job_id}) submitted from line {job.line_number}.')


def notify_job_complete(job: Job):
    """ Print a message indicating that the job has successfully completed """
    job_id = job.info['jobId']
    rows_returned = job.info.get('rowsReturned', 0)
    usage = job.info.get('usage', 0)
    print(f'Job ({job_id}) complete. rowsReturned={rows_returned} usage={usage}')


def notify_job_errored(job: Job):
    """ Print a message indicating that the job encountered an error """
    job_id = job.info['jobId']
    error = job.info['error']
    print(f'Job ({job_id}) error. {error}')


def _cancel(code=0, message='Operation canceled'):
    print(f"\n{message}")
    exit(code)


if __name__ == '__main__':
    try:
        _main()
    except KeyboardInterrupt:
        _cancel(2)
