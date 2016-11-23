## Item Catalog Application

This flask and sqlaclhemy database is an item catalog with the ability for the public to read categories, items, and item descriptions within the catalog, and the ability for users to add/edit/delete the same.

### Installation, or How To Run

1.  Install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/).
2.  Ensure flask/sqlalchemy/oauth2 modules as required in application.py are available.
3.  Download the git repository [here](https://github.com/acct252000/udacity_item_catalog) by clicking on the green button.  Download to a file accessible by your vagrant virtual machine.
4.  Launch the vagrant machine by typing `vagrant up.` in the command line from the vagrant directory.
5.  Type `vagrant ssh.`
6.  Navigate to the folder where you downloaded and extracted the zip file, ensuring you are in the directory that contains application.py
7.  Type `application.py` to run test file.
8.  You must login to add, edit or delete categories and items.  To add an item, click on one of the category descriptions from the home page.
9.  To edit or delete an item, access the item page by clicking on the item name.

### Accessing the JSON API

1.  To access the json api for a given integer category id, say 1, and integer item id, say 2, the url is /category/1/item/2/JSON.  This url can be found by navigating to the item's page and ading /JOSN to the end of the current url.

### Attributions

* The structure heavily relies on the [Udacity](https://www.udacity.com) course Full Stack Foundations and Authentication and Authorization.
* Additional help from user Arhtur Kapp on [this stackflow question.](http://stackoverflow.com/questions/14580346/vertical-divider-between-two-column-in-bootstrap)
