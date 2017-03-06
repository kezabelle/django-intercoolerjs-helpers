django-intercooler_helpers
==========================

:author: Keryn Knight
:version: 0.2.0

.. |travis_stable| image:: https://travis-ci.org/kezabelle/django-intercoolerjs-helpers.svg?branch=0.2.0
  :target: https://travis-ci.org/kezabelle/django-intercoolerjs-helpers

.. |travis_master| image:: https://travis-ci.org/kezabelle/django-intercoolerjs-helpers.svg?branch=master
  :target: https://travis-ci.org/kezabelle/django-intercoolerjs-helpers

==============  ======
Release         Status
==============  ======
stable (0.2.0)  |travis_stable|
master          |travis_master|
==============  ======


.. contents:: Sections
   :depth: 2

What it does
------------

``intercooler_helpers`` is a small reusable app for `Django`_ which provides a
few improvements for working with `Intercooler.js`_.

It providea a middleware which extracts relevant `Intercooler.js`_ data from the
querystring, and attaches it to the request as a separate ``QueryDict`` (ie: it
behaves like ``request.POST`` or ``request.GET``)

It also provides a small middleware for changing request method based on either the
query string (``_method=PUT``) or a request header(``X-HTTP-Method-Override: PUT``)

Between them, they should capture all the incoming `Intercooler.js`_ data on
which the server may act.

Installation and usage
----------------------

This application depends on `django-intercoolerjs`_ which provides a copy of
`Intercooler.js`_ bundled up for use with the standard `Django`_ staticfiles
application.

Installation
^^^^^^^^^^^^

You can grab ``0.2.0`` from `PyPI`_ like so::

  pip install django-intercooler-helpers==0.2.0

Or you can grab it from  `GitHub`_  like this::

  pip install -e git+https://github.com/kezabelle/django-intercooler-helpers.git#egg=django-intercooler-helpers

Configuration
^^^^^^^^^^^^^
You need to add ``intercooler_helpers.middleware.IntercoolerData`` to your
``MIDDLEWARE_CLASSES`` (or ``MIDDLEWARE`` on Django **1.10+**).

You may optionally want to add ``intercooler_helpers.middleware.HttpMethodOverride``
as well, if you don't already have a method by which to fake the HTTP Method change.
If you're using ``<meta name="intercoolerjs:use-actual-http-method" content="true"/>``
then you don't need ``HttpMethodOverride`` at all.

Usage
^^^^^

A brief overview of the public API provided so far:

IntercoolerData
***************

For fully correct detection of `Intercooler.js`_ requests, you can call
``request.is_intercooler()``.
Behind the scenes, it uses ``request.maybe_intercooler()`` to
detect whether ``ic-request`` was present, indicating it *may* have been a
valid `Intercooler.js`_ request, and also checks ``request.is_ajax()``

To parse the Intercooler-related data out of the query-string, you can use
``request.intercooler_data`` (not a method!) which is a ``QueryDict`` and should
behave exactly like ``request.GET`` - It pulls all of the ``ic-*`` keys out
of ``request.GET`` and puts them in a separate data structure, leaving
your ``request.GET`` cleaned of extraenous data.

``request.intercooler_data`` is a **lazy** data structure, like ``request.user``,
so will not modify ``request.GET`` until access is attempted.

The following properties exist, mapping back to the keys mentioned in the
`Intercooler.js Reference document`_

- ``request.intercooler_data.url`` returns a ``namedtuple`` containing

  - returns the ``ic-current-url`` (converted via ``urlparse``) or ``None``
  - A `Django`_ ``ResolverMatch`` pointing to the view which made the request (based on ``ic-current-url``) or ``None``
- ``request.intercooler_data.element`` returns a ``namedtuple`` containing

  -  ``ic-element-name`` or ``None``
  -  ``ic-element-id`` or ``None``
- ``request.intercooler_data.id``

  - the ``ic-id`` which made the request. an ever-incrementing integer.
- ``request.intercooler_data.request``

  - a boolean indicating that it was an `Intercooler.js`_ request. Should always
    be true if ``request.is_intercooler()`` said so.
- ``request.intercooler_data.target_id``

  -  ``ic-target-id`` or ``None``
- ``request.intercooler_data.trigger`` returns a ``namedtuple`` containing

  -  ``ic-trigger-name`` or ``None``
  -  ``ic-trigger-id`` or ``None``
- ``request.intercooler_data.prompt_value``

  - If no ``ic-prompt-name`` was given and a prompt was used, this will contain
    the user's response. Appears to be undocumented?


HttpMethodOverride
******************

- ``request.changed_method`` is a boolean indicating that the request was
  toggled from being a ``POST`` to something else (one of
  ``GET``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``, ``OPTIONS`` ...
  though why you'd want to ``POST`` and have it act as a ``GET`` is beyond me.
  But that's your choice)
- ``request.original_method`` if either ``_method=X`` or
  ``X-HTTP-Method-Override: X`` caused the request to change method, then this
  will contain the original request. It should always be ``POST``
- ``request.method`` will reflect the desired HTTP method, rather than the one
  originally used (``POST``)


IntercoolerRedirector
*********************

If a redirect status code is given (> 300, < 400), and the request originated from `Intercooler.js`_ (assumes ``IntercoolerData`` is installed so that ``request.is_intercooler()`` may be called), remove the ``Location`` header from the response, and create a new ``HttpResponse`` with all the other headers, and also the ``X-IC-Redirect`` header to indicate to `Intercooler.js`_ that it needs to do a client side-redirect.


Supported Django versions
-------------------------

The tests are run against Django 1.8 through 1.10, and Python 2.7, 3.3, 3.4 and 3.5.

Running the tests
^^^^^^^^^^^^^^^^^

If you have a cloned copy, you can do::

  python setup.py test

If you have tox, you can just do::

  tox

Running the demo
^^^^^^^^^^^^^^^^

I've not yet built the demo, but eventually you'll be able to do something like
the following. It assumes you're using something like `virtualenv`_ and
`virtualenvwrapper`_ but you can probably figure it out otherwise::

    mktmpenv --python=`which python3`
    pip install -e git+https://github.com/kezabelle/django-intercooler-helpers.git#egg=django-intercooler-helpers

Then probably::

    cd src/django-intercooler-helpers
    python demo_project.py runserver


Contributing
------------

Please do!

The project is hosted on `GitHub`_ in the `kezabelle/django-intercooler-helpers`_
repository.

Bug reports and feature requests can be filed on the repository's `issue tracker`_.

If something can be discussed in 140 character chunks, there's also `my Twitter account`_.

Roadmap
-------

TODO.

The license
-----------

It's `FreeBSD`_. There's should be a ``LICENSE`` file in the root of the repository, and in any archives.

.. _FreeBSD: http://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29
.. _Django: https://www.djangoproject.com/
.. _Intercooler.js: http://intercoolerjs.org/
.. _django-intercoolerjs: https://github.com/brejoc/django-intercoolerjs
.. _GitHub: https://github.com/
.. _PyPI: https://pypi.python.org/pypi
.. _Intercooler.js Reference document: http://intercoolerjs.org/reference.html
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _kezabelle/django-intercooler-helpers: https://github.com/kezabelle/django-intercooler-helpers/
.. _issue tracker: https://github.com/kezabelle/django-intercooler-helpers/issues/
.. _my Twitter account: https://twitter.com/kezabelle/
