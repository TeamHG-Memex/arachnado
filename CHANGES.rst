Changes
=======

unreleased
----------

* Fixed AttributeError on Windows: num_fds() is not available on Windows,
  use num_handles() instead. The code now checks for platform-specific
  methods and uses the appropriate one.

0.2 (2015-08-07)
----------------

Initial release.
