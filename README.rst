py-gzip-header
==============

Python library to parse and edit gzip file header.

Library
-------

.. code:: python

    import gzip
    import gzip_header

    with open('/path/to/file.gz', 'rb') as f:
        header = gzip_header.Header.from_reader(f)

    # change data

    header.fname = 'new_name'
    header.fcomment = 'hello'

    print(bytes(header))
