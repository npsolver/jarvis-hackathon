We will build a simple banking transaction system. It will have the following components:

1. Tables:
    1.1 Account - table of accounts
    1.2 Transactions - table of transactions made by users
    1.3 Human review - table to suspicious transactions that need to be verified by an admin

2. Apis/functions(scripts)
    2.1 user api(s) - for when a user creates an account, makes a transaction, etc.
    2.2. data review script - to verify a specific transaction is correct. called by the user apis and whenever we want to review items from a csv file.
    2.3 data migration script - adding accounts or transactions to the tables after it goes through review
    2.4 send to review table api - If data review script says something is wrong, send the account or transaction to the Human Review table
    2.5 Add/Remove api - after an admin reviews something from human review table, this api sends the transaction to the data review script again, which may send it to the data migration script or back to the send to review table api which sends it back to the human review table.


Implement the above by writing the apis and scripts using python and use django to interact with the tables. the tables should be in postgreSQL. 

Migrate the accounts.csv and transactions.csv at the end.
