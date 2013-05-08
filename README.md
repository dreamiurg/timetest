timetest
========

This is small demo project for my Vagrant presentation http://www.slideshare.net/dreamiurg/virtualization-with-vagrant-uapycon-2011 for details.

See how it works in this screencast: www.youtube.com/watch?v=O3-MNsowgHc

Usage
-----

Install prerequisites

    $ ... install python (required for fab setup that runs on host box)
    $ ... install ruby
    $ ... install VirtualBox
    $ gem install vagrant
    $ pip install fab
	

Clone this repo and get submodules

    $ git clone https://github.com/dreamiurg/timetest.git
    $ cd timetest
    $ git submodule init
    $ git submodule update
	
Add lucid32 vagrant box

    $ vagrant box add lucid32 http://files.vagrantup.com/lucid32.box
	
Create, boot up and provision VM
	
    $ vagrant up
	
Set up apache configuration on VM, create database, etc.

    $ fab setup vagrant
	
Test that everything is up
