#!/usr/bin/env python

import fdb
import threading
import time

# Prepare database.

con = fdb.create_database("create database 'A' user 'sysdba' password 'masterkey'")
con.execute_immediate("create table CASE_TBL (INTERNALID bigint primary key, CASENO varchar(30))")
con.execute_immediate("create generator INTERNALID")
con.execute_immediate("set generator INTERNALID to 0")

con.execute_immediate("""
create trigger INTERNALID for CASE_TBL active
before insert position 0
as
begin
    if ((new.INTERNALID is NULL) or (new.INTERNALID = 0)) then new.INTERNALID = gen_id(INTERNALID, 1);
end
""")

con.execute_immediate("""
create trigger Event for CASE_TBL active
after insert position 0
as
begin
    if (new.CASENO = 1) then
        post_event 'One';
    else if (new.CASENO = 2) then
        post_event 'Two';
    else if (new.CASENO = 3) then
        post_event 'Three';
    else if (new.CASENO = 0) then
        post_event 'Exit';
    else
        post_event 'Other';
end""")

con.commit()
cur = con.cursor()

while True:
    Events = con.event_conduit(['One','Two','Three', 'Other', 'Exit'])
    E = Events.wait()
    localtime = time.asctime(time.localtime(time.time()))
    print localtime
    print 'One = ' + str(E['One'])
    print 'Two = ' + str(E['Two'])
    print 'Three = ' + str(E['Three'])
    print 'Other = ' + str(E['Other'])
    print 'Exit = ' + str(E['Exit'])
    print
    if E['Exit'] == 1:
        break

Events.close()
raw_input("Press disconnect from database & ISQL gracefully. Then press <ENTER>.")

# Finalize
con.drop_database()
con.close()
