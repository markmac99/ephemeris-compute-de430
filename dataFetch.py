#!/usr/bin/python3
# -*- coding: utf-8 -*-
# dataFetch.py
#
# -------------------------------------------------
# Copyright 2015-2021 Dominic Ford
#
# This file is part of EphemerisCompute.
#
# EphemerisCompute is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EphemerisCompute is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EphemerisCompute.  If not, see <http://www.gnu.org/licenses/>.
# -------------------------------------------------

"""
Automatically download all of the required data files from the internet.
"""

import argparse
import os
import sys
import logging
import urllib.request
import urllib.error


def fetch_file(web_address, destination, force_refresh=False):
    """
    Download a file that we need, using wget.

    :param web_address:
        The URL that we should use to fetch the file
    :type web_address:
        str
    :param destination:
        The path we should download the file to
    :type destination:
        str
    :param force_refresh:
        Boolean flag indicating whether we should download a new copy if the file already exists.
    :type force_refresh:
        bool
    :return:
        Boolean flag indicating whether the file was downloaded. Raises IOError if the download fails.
    """
    logging.info("Fetching <{}>".format(destination))

    # Check if the file already exists
    if os.path.exists(destination):
        if not force_refresh:
            logging.info("File already exists. Not downloading fresh copy.")
            return False
        else:
            logging.info("File already exists, but downloading fresh copy.")
            os.unlink(destination)

    # Check whether source URL is gzipped
    supplied_source_is_gzipped = web_address.endswith(".gz")
    target_is_gzipped = destination.endswith(".gz")

    # Try downloading file in both gzipped and uncompressed format, as CDS archive sometimes changes compression
    for source_is_gzipped in [supplied_source_is_gzipped, not supplied_source_is_gzipped]:
        # Make source source URL has the right suffix
        url = web_address
        if source_is_gzipped and not supplied_source_is_gzipped:
            url = web_address + ".gz"
        elif supplied_source_is_gzipped and not source_is_gzipped:
            url = web_address.strip(".gz")

        # Make sure file destination has the right suffix
        destination_download = destination
        if source_is_gzipped and not target_is_gzipped:
            destination_download = destination + ".gz"
        elif target_is_gzipped and not source_is_gzipped:
            destination_download = destination.strip(".gz")

        # Fetch the file with wget
        logging.info("Downloading <{}> to <{}>".format(url, destination_download))
        try:
            urllib.request.urlretrieve(url=url, filename=destination_download)
        except urllib.error.URLError:
            logging.info("Download failed; attempting alternative URLs")
            continue

        # Check that the file now exists
        if not (os.path.exists(destination_download) and os.path.getsize(destination_download) > 0):
            logging.info("Download failed; attempting alternative URLs")
            continue

        # Check that file is compressed or uncompressed, as required
        if source_is_gzipped and not target_is_gzipped:
            logging.info("Uncompressing to <{}>".format(destination))
            os.system("gunzip {}".format(destination_download))
        elif target_is_gzipped and not source_is_gzipped:
            logging.info("Compressing to <{}>".format(destination))
            os.system("gzip {}".format(destination_download))

        # Check that the file now exists
        if not os.path.exists(destination):
            raise IOError("Failed to create target file. Is gzip/gunzip installed?")

        # Success!
        return True

    # We didn't manage to download the file...
    raise IOError("Could not download file <{}>".format(web_address))


def fetch_required_files(refresh):
    """
    Fetch all of the files we require.

    :param refresh:
        Switch indicating whether to fetch fresh copies of any files we've already downloaded.
    :type refresh:
        bool
    :return:
    """
    # List of the files we require
    required_files = [
        {
            'url': 'ftp://ftp.lowell.edu/pub/elgb/astorb.dat.gz',
            'destination': 'data/astorb.dat',
            'force_refresh': True
        },
        {
            'url': 'https://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt',
            'destination': 'data/Soft00Cmt.txt',
            'force_refresh': True
        },
        {
            'url': 'ftp://ssd.jpl.nasa.gov/pub/eph/planets/ascii/de430/header.430_572',
            'destination': 'data/header.430',
            'force_refresh': refresh
        },
        {
            'url': 'http://cdsarc.u-strasbg.fr/ftp/VI/49/bound_20.dat.gz',
            'destination': 'constellations/bound_20.dat',
            'force_refresh': refresh
        },
        {
            'url': 'http://cdsarc.u-strasbg.fr/ftp/VI/49/ReadMe',
            'destination': 'constellations/ReadMe',
            'force_refresh': refresh
        }
    ]

    # Fetch the JPL DE430 ephemeris
    for year in range(1550, 2551, 100):
        required_files.append({
            'url': 'ftp://ssd.jpl.nasa.gov/pub/eph/planets/ascii/de430/ascp{:04d}.430'.format(year),
            'destination': 'data/ascp{:04d}.430'.format(year),
            'force_refresh': refresh
        })

    # Fetch all the files
    for required_file in required_files:
        fetch_file(web_address=required_file['url'],
                   destination=required_file['destination'],
                   force_refresh=required_file['force_refresh']
                   )


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)

    # Add command-line options
    parser.add_argument('--refresh', dest='refresh', action='store_true', help='Download a fresh copy of all files.')
    parser.add_argument('--no-refresh', dest='refresh', action='store_false', help='Do not re-download existing files.')
    parser.set_defaults(refresh=False)
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Fetch all the data
    fetch_required_files(refresh=args.refresh)
