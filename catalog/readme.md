## Getting Started

1. Clone this project into your desired project location
2. If you wish to use the provided sample database, skip to 4
3. Delete the file named "items.db" in /yourdirectory/itemproject/catalog
4. Open a unix prompt and navigate to the project location, then navigate to /itemproject
3. Run vagrant up
4. Ensure virtual server has booted. Run vagrant ssh
5. navigate to /vagrant/catalog
6. If you performed step 3, run python database_setup.py at this time to create a fresh database. Otherwise, skip to step 7
7. Run python index.py. You should see language showing server running on port 8000
8. Open a browser and navigate to localhost:8000

### Prerequisites

You will need the latest versions of virtualbox and vagrant, as well as python 2.7 and access to a UNIX prompt. Be advised,
if you do not have the latest version of virtual box and are running windows 10, a recent update to windows will prevent your
vagrant vm from booting properly. You will be given a certification error when checking your vm's error logs. Please navigate 
[here](https://www.virtualbox.org/wiki/Downloads) to get the latest version of virtualbox. The system also uses Google as the only 
way to login, so you will need an active Google account. I would've added Facebook, but I am not a facebook user myself so would 
be unable to test that functionality, so it has been omitted.

### Purpose

This is a project for Udacity, demonstrating the use of an MVC framework being used to facilitate a webapp that has authorization-based 
CRUD functionality, and uses a 3rd party OAUTH 2.0 as a login system (Google in this case). Be advised you will not be able to test update and delete
on the sample database items, as they are created under my user name. You will need to create your own items to test this.

### Functionality

The app should do the following:

- Allow anyone to view the top 10 most recent items and all categories on the home page
- Anyone may click a category and see all of the child items of that category
- Anyone may click an item and see it's description
- Logged in users may create new items and categories
- Logged in users may edit and delete only the items they've created
- JSON endpoint provided at /catalog/categories/json for JSON of all categories
- JSON endpoint provided at catalog/items/json for JSON of all items
- JSON endpoint provided at catalog/"Categoryname"/json for JSON of all items for that given category name