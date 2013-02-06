Documentation
=============
Documentation for Django Sellmo, a modular e-commerce platform thats bends to your needs.

.. toctree::
	:maxdepth: 2
	
	fundementals
	
Intro
-----
We wanted a generic yet flexible e-commerce solution for our python/django projects. We didn't 
want to build some losely coupled django apps, requiring us to tie everything together every project.
Still we want it to bend to every requirement ranging from a plain simple webshop to a fully tailored
webshop solution for our clients.

Fundementals
------------
Sellmo isn't a typical django project, it extends django with some core concepts of it's own:

* **View & Function chaining**
Sellmo's predefined views do a all the heavy lifting, yet 'by design' they don't render anything. You
write your own views and hook them up to Sellmo's views. Upon initialization Sellmo builds an execution 
chain for all known views and api functions.

* **Plugable initialization process**
* **Sellmo modules**