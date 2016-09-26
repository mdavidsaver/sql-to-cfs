The sql-to-cfs script is designed to transfer all of the data within a specifically formatted SQLite Database into
an active ChannelFinder Service. It will create any properties or tags that are necessary for the channels to be
added.

The SQL-to-CFS script can be run with the following command from the scripts directory:

$ ./sql-to-cfs.py /path/to/db.sqlite


The cfs-to-sql script is designed to transfer channels from an active ChannelFinder Service into a formatted SQLite
Database, it will create the necessary tables in an existing database if they do not already exist or it will create
a new Database file at the specified location if there is no file at the specified location.

The CFS-to-SQL script can be run with the following command from the scripts directory:

$ ./cfs-to-sql.py /path/to/target.sqlite


The integration test uses the following process and calls both scripts using their command line interface:

1. Converts existing test_db.sqlite database into existing CFS using sql-to-cfs.
2. Asserts that the new channel names exist.
3. Converts all channels in CF into new _test_output.sqlite database using cfs-to-sql.
4. Iterates through test_db.sqlite and asserts that all data was migrated to _test_output.sqlite.