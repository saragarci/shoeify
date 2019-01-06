# Shoeify!

## Application

This is an application that classifies shoes.
It has lots of categories and inside each of these you can store any kind of shoes (their name and description).
Categories are fixed and therefore cannot be modified. Shoes can be added once you are logged in. Shoes can be inserted, modified and deleted.
In order to log in a google account is necessary as the proccess of authentication & authorization in is done with the Google API.

## JSON endpoint

This application contains an endpoint with three possible GET requests that can be done.

* http://localhost:5000/categories/JSON returns a JSON with all the categories available in the app. Every category contains id and name.
* http://localhost:5000/`category_id`/item/JSON returns a JSON with all the shoes available inside a particular category. Note that you must specify the id of the category in the call in order to retrive all the information. For every shoes, name, id and description are given.
* http://localhost:5000/`category_id`/item/`item_id`/JSON returns a JSON with the name, id and description of a pair of shoes. In this request you have to specify both category id in which the item you want to query belongs to, and the id of the item itself. 

## Usage

### Setting up the environment

The usage of this report is intended to be done by using Vagrant and VirtualBox. Therefore, both of them need to be installed.

Once you have both of them installed in your computer. Download the VM configuration by forking and then cloning this [repo](https://github.com/udacity/fullstack-nanodegree-vm).

Then, `cd` into the **vagrant** directory and paste the items inside. After this, run `vagrant up` to download the Linux OS and install it.

After this, you just need to do `vagrant ssh` to log in into the VM.

### Running the report

In order to see the report, run the following commands:
* `cd` into the folder which contains the code for this project
* Run `python database_setup.py` in order to create the database
* Run `python items_db.py` to populate the database
* Run `python itemcatalog.py` and navigate to localhost:5000 in your browser

## Credits

### Images

* [Restaurant](https://pixabay.com/en/breakfast-food-eating-meal-morning-690128/)

### Contributors

* Sara Garci <s@saragarci.com>

## License

© Copyright 2018 by Sara Garci. All rights reserved.