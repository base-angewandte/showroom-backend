.. base Showroom Backend documentation master file, created by
   sphinx-quickstart on Mon May 16 15:03:30 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to base Showroom Backend's documentation!
=================================================

*Showroom* is the showcasing component of the open source CRIS (current research
information system) *Portfolio*. For background information on the project, visit the
`Portfolio/Showroom website <https://portfolio-showroom.ac.at/>`_. It is developed by
the `base <https://base.uni-ak.ac.at>`_ dev team at the
`University of Applied Arts Vienna <https://www.dieangewandte.at>`_.

The *Showroom Backend* is the component containing all entries and activities, which users
of Portfolio have published. Those entries are transformed to be displayed and searched
for by the Showroom Frontend.

For how *Showroom* is built and why it is built in that way, take a look at the
:doc:`architecture` section. This might be helpful to understand the entanglement of
this component with *Portfolio* but also the *CAS/UserPreferences* component, without
which no entity information will be available in *Showroom*. Once you get the big
picture :doc:`install` will guide you to a first running version of the *Showroom*
backend, and how to set it up.

The rest of the sections give you a little more insight into how the
:doc:`configuration` works in detail, the :doc:`management_commands` you can use,
some context for the :doc:`rest_api` and the available :doc:`api_plugins`, a few words
on the :doc:`lists_logic`, that is used to create sub-structured lists of activities for
entity pages. Also the :doc:`search_logic` section explains how search works in
*Showroom* and it also contains the source definition of all available filters and how
they are supposed to work.

.. toctree::
   :maxdepth: 2
   :caption: Overview & Setup

   architecture
   install
   configuration
   management_commands

.. toctree::
   :maxdepth: 2
   :caption: Developer References

   rest_api
   api_plugins
   lists_logic

.. toctree::
   :maxdepth: 2
   :caption: Definitions

   search_logic
   data_transformation_definitions
