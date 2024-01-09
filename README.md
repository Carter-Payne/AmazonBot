# AmazonBot
This project was designed to fetch the price of selected amazon products and email the price of them if they fit the specifications of the user. The script Amazon_Bot.py is designed to be the user interface, allowing one to create an account and add amazon links to the account, along with features such as being able to change how you want to recieve emails, changing your email, and viewing all your products. The script BotRunner.py is the script to apply to the bot, running a version of Amazon_Bot.py that updates all the products in the SQL database and sends out emails.

--How to run--

In order to run this code, a few things are needed. An SQL server, an email account to send the emails from, and a method to run the script BotRunner.py. The SQL Server must have the following tables if wanted to be run as is.

Table: UserInfo

Columns:
USERNAME-varchar(20)
EMAIL-varchar(45)
PASSWORD-varchar(120)

Table: LINKS

Columns:
URL-varchar(1000)
EMAIL-varchar(50)
BASEPRICE-varchar(100)
ISSALE-tinyint(1)
PERCENTAGE-varchar(10)
SALEPRICE-varchar(100)
LOWERTHANBEFORE-tinyint(1)
MESSAGEMETHOD-varchar(12)
NAME-varchar(300)

If instead you want to host the code, it is recommended you add security measures with user passwords and the sql tables.

Because this code relies on sending requests to Amazon, it is prone to stop working. In the case that too many requests are sent, it is recommended to add a proxy to each fetch request. If the code fails to fetch the information from the amazon links, you can manually add another css selection to the product info in the data class.
