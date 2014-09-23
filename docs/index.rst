Documentation
=============
Documentation for Django Sellmo, a modular e-commerce platform thats bends to your needs.

.. toctree::
	:maxdepth: 2
	
	fundamentals
	
Intro
-----
We wanted a generic yet flexible e-commerce solution for our python/django projects. We didn't 
want to build some losely coupled django apps, requiring us to tie everything together every project.
Still we want it to bend to every requirement ranging from a plain simple webshop to a fully tailored
webshop solution for our clients.

Fundamentals
------------
Sellmo isn't a typical django project, it extends django with some core concepts of it's own:

* **View & Function chaining**
Sellmo's predefined views do a all the heavy lifting, yet 'by design' they don't render anything. You
write your own views and hook them up to Sellmo's views. Upon initialisation Sellmo builds an execution 
chain for all known views and api functions.

* **Delayed model loading**
In order to extend Sellmo's logic through function chaining, the need for extended models also arrives.
Sellmo's core modules trie to keep every required model as simple as possible, only defining those fields
and relations that are absolutely necessary for Sellmo's 'shopping cart' functionality to work. However
due to Sellmo's delayed model loading process, every custom Sellmo module and every Django app can tie into 
this process and inject the needed fields, relations and logic into Sellmo's core models.

* **Sellmo modules**
Finally to facilitate 