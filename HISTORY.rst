=======
History
=======

0.9.8 (2019-04-10)
------------------

* Added X-Requested-By so some servers won't block requests because of CSRF protection.

0.9.4 (2019-03-15)
------------------

* Session expiration was not handled properly when create-session was set and stored
  session Id was expired. It should try to authenticate again. Fixed.

0.9.4 (2019-03-15)
------------------

* Allow the session Id to be stored in the configuration file for subsequent pygray
  calls
* Fixed various calls to str's "encode", no longer necessary in Python3

0.9.2 (2019-03-15)
------------------

* Messages were printed as Python3's "bytestrings", not regular strings. Fixed.

0.9.1 (2019-03-15)
------------------

* Fixed crash when follow mode was activated

0.9.0 (2019-03-15)
------------------

* First release on PyPI.
