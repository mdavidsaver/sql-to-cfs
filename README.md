The sql-to-cfs script is designed to transfer all of the data within a specifically formatted SQLite Database into
an active ChannelFinder Service.

The SQL-to-CFS script can be run with the following command:

$ ./sql-to-cfs.py /path/to/db.sqlite


The cfs-to-sql script is designed to transfer channels from an active ChannelFinder Service into a formatted SQLite
Database, it will create a new Database file at the specified location if one does not already exist.

The CFS-to-SQL script can be run with the following command:

$ ./cfs-to-sql.py /path/to/target.sqlite
