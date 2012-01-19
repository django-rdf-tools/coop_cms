Coop-cms, a really pluggable CMS
===============================================


Quick Start, Docs, Contributing
-------------------------------
* `Yet another CMS ?`_
* `Quick start`_

.. _Yet another CMS?: #yacms
.. _Quick start?: #quick-start


.. _yacms:

Yet another CMS ?
------------------------------------

#. Coop-cms is built around Articles. It defines a basic abstract model so you can define your own model.
#. It has a website tree in a nice admin widget, to let you order Articles and *any other standard django model* you've defined in your project.
#. Based on the tree, you get templatetags for menu navigation, siblings links, breadcrumb, etc

Coop-cms has some sister apps to make it more usable:

* `coop_bar <https://github.com/quinode/coop-bar/>`_, an extensible toolbar (same concept : any app you create can add links in the toolbar)
* `djaloha <https://github.com/quinode/djaloha/>`_, a great in-site editor based on `Aloha Editor <http://aloha-editor.org/>`_


.. _quick-start:

Quick start
------------------------------------

Install it with ``pip install coop-cms``

In settings.py, add 'coop_cms' (with an underscore) to the INSTALLED_APPS 
Under Django 1.3, the static folder should be found automatically, as the templates folder
At *the very end* of your urls.py file, add ``(r'^', include('coop_cms.urls'))`` to your urlpatterns, because coop-cms will handle any page slug, except the ones you will have defined before.

The ``apps```folder contains two example projects of how coop-cms can be used.

(to be continued)


License
=======

coop_cm uses the same license as Django (BSD).

