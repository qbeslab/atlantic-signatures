=====================
Introduction to Vicon
=====================

Before we jump to the how-to part of this guide it is prudent to know the
terminology and equipment. If you wish to learn more about Vicon cameras and
their tracking software go to the corresponding section of the `Vicon
documentation website <https://help.vicon.com>`__.

----------
Lab Layout
----------

.. figure:: images/lab-layout.svg
    :height: 600

    Blue arrows: Ethernet connections.
    Black arrows: Power connections.
    UPS: Uninterruptible power supply.

The leftmost lab desk is a dedicated workstation for use with the Vicon motion
capture system.

--------
Hardware
--------

As seen in the lab layout diagram, the four main components of the Vicon System
are the eight Vicon Vero cameras, an ethernet hub, a UPS (uninterruptible power
supply), and the "host" lab computer. Through the ethernet hub, camera data is
relayed to the lab computer. The ethernet hub has a second purpose and that is
to power the cameras (power over ethernet, PoE). The UPS provides power during
momentary power failures so that a several second or even several minute
blackout will not affect the cameras.

When the user wishes to start up the cameras all they need to do is plug the
power cable of the ethernet hub directly into the UPS. Connect the hub into the
port at the back of the UPS labeled "Surge + Battery" like the following:

.. figure:: images/ups.svg
    :height: 600

Once connected you will hear a fan rev up and see the lights on the cameras
turn on.

Next, turn on the lab computer if it's not on already. Open the Start Menu and
type in "Vicon" in the search bar. Vicon Tracker 3.7.0 x64 (or some later
version) should appear. The green icon of Vicon Tracker should also be visible
on the desktop. Open the program.

.. figure:: images/tracker_in_win_search.png
    :height: 400

Once loaded, Vicon Tracker will welcome you with the "Resources" pane on the
left side of the screen and a much larger camera perspective pane on the right.
Don't worry if the cameras are red instead of green - that's why we calibrate!
Please familiarize yourself with the application layout before moving on.

.. figure:: images/vicon-tracker-first-screen.png
    :height: 400

There are four tabs in the Resources pane: System, Calibrate, Objects, and
Recording. The first three are the only ones of importance since we do not take
any recordings using Vicon. The System tab contains settings that you should not
need to change, but a problem camera can be rebooted from here by right-clicking
the camera and selecting "Reboot". The Calibrate tab will be explained in detail
in a :ref:`later section <vicon-calibration>`. Finally, the Objects tab allows
you to select and deselect objects that the cameras will track. The Create
robots typically will have an object name like "Create2 - Robot 1".

.. table:: The three main tabs you will be bouncing between
    :align: center

    +----------------------------------------------------+------------------------------------------------------+------------------------------------------------------+
    | .. image:: images/vicon-tracker-system-tab.png     | .. image:: images/vicon-tracker-calibrate-tab.png    | .. image:: images/vicon-tracker-objects-tab.png      |
    |   :width: 240px                                    |   :width: 240px                                      |   :width: 240px                                      |
    |   :height: 480px                                   |   :height: 480px                                     |   :height: 480px                                     |
    |   :align: left                                     |   :align: center                                     |   :align: right                                      |
    +----------------------------------------------------+------------------------------------------------------+------------------------------------------------------+
