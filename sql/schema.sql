-- SOFE 3700U Data Management Systems
-- Phase II - Part A: Relational Schema
-- Project: NuclearOps - Nuclear Plant Maintenance and Outage Tracker
-- DBMS: PostgreSQL

-- Drop old tables first so the script can be run again
DROP TABLE IF EXISTS USER_ACCOUNT CASCADE;
DROP TABLE IF EXISTS WEATHER_LOG CASCADE;
DROP TABLE IF EXISTS WORK_ORDER_PART CASCADE;
DROP TABLE IF EXISTS SPARE_PART CASCADE;
DROP TABLE IF EXISTS INSPECTION CASCADE;
DROP TABLE IF EXISTS WORK_ORDER CASCADE;
DROP TABLE IF EXISTS OUTAGE CASCADE;
DROP TABLE IF EXISTS WORKER CASCADE;
DROP TABLE IF EXISTS EQUIPMENT CASCADE;
DROP TABLE IF EXISTS PLANT_SYSTEM CASCADE;
DROP TABLE IF EXISTS REACTOR_UNIT CASCADE;
DROP TABLE IF EXISTS STATION CASCADE;


-- A nuclear generating station
CREATE TABLE STATION (  Station_id      INT             NOT NULL,
                        Name            VARCHAR(50)     NOT NULL,
                        City            VARCHAR(30)     NOT NULL,
                        Province        CHAR(2)         NOT NULL    DEFAULT 'ON',
                        Latitude        DECIMAL(8,5)    NOT NULL,
                        Longitude       DECIMAL(8,5)    NOT NULL,
        CONSTRAINT STATIONPK PRIMARY KEY (Station_id),
        CONSTRAINT STATIONSK UNIQUE (Name) );


-- A reactor unit at a station
CREATE TABLE REACTOR_UNIT ( Unit_id         INT             NOT NULL,
                            Station_id      INT             NOT NULL,
                            Unit_number     INT             NOT NULL    CHECK (Unit_number > 0),
                            Reactor_type    VARCHAR(20)     NOT NULL    DEFAULT 'CANDU',
                            Capacity_mw     INT             NOT NULL    CHECK (Capacity_mw > 0),
                            Status          VARCHAR(20)     NOT NULL    DEFAULT 'Operating',
        CONSTRAINT UNITPK PRIMARY KEY (Unit_id),
        CONSTRAINT UNITSK UNIQUE (Station_id, Unit_number),
        CONSTRAINT UNITSTATIONFK FOREIGN KEY (Station_id) REFERENCES STATION (Station_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CHECK (Status IN ('Operating', 'In Outage', 'Refurbishment', 'Shut Down')) );


-- A system inside a reactor unit (for example, the cooling system)
CREATE TABLE PLANT_SYSTEM ( System_id       INT             NOT NULL,
                            Unit_id         INT             NOT NULL,
                            Name            VARCHAR(50)     NOT NULL,
                            Safety_related  BOOLEAN         NOT NULL    DEFAULT FALSE,
        CONSTRAINT SYSTEMPK PRIMARY KEY (System_id),
        CONSTRAINT SYSTEMUNITFK FOREIGN KEY (Unit_id) REFERENCES REACTOR_UNIT (Unit_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE );


-- A piece of equipment that gets inspected and repaired
CREATE TABLE EQUIPMENT (    Equipment_id    INT             NOT NULL,
                            System_id       INT             NOT NULL,
                            Tag_number      VARCHAR(20)     NOT NULL,
                            Name            VARCHAR(50)     NOT NULL,
                            Equipment_type  VARCHAR(20)     NOT NULL,
                            Manufacturer    VARCHAR(50),
                            Install_date    DATE            NOT NULL,
                            Inspection_interval_days INT    NOT NULL    CHECK (Inspection_interval_days > 0),
        CONSTRAINT EQUIPPK PRIMARY KEY (Equipment_id),
        CONSTRAINT EQUIPSK UNIQUE (Tag_number),
        CONSTRAINT EQUIPSYSTEMFK FOREIGN KEY (System_id) REFERENCES PLANT_SYSTEM (System_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE );


-- A maintenance worker (technician or inspector)
CREATE TABLE WORKER (   Worker_id       INT             NOT NULL,
                        Station_id      INT             NOT NULL,
                        Fname           VARCHAR(20)     NOT NULL,
                        Lname           VARCHAR(20)     NOT NULL,
                        Email           VARCHAR(50)     NOT NULL,
                        Trade           VARCHAR(20)     NOT NULL,
                        Cert_expiry     DATE            NOT NULL,
        CONSTRAINT WORKERPK PRIMARY KEY (Worker_id),
        CONSTRAINT WORKERSK UNIQUE (Email),
        CONSTRAINT WORKERSTATIONFK FOREIGN KEY (Station_id) REFERENCES STATION (Station_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CHECK (Email LIKE '%_@_%._%') );


-- A period of time when a reactor unit is shut down
CREATE TABLE OUTAGE (   Outage_id           INT             NOT NULL,
                        Unit_id             INT             NOT NULL,
                        Outage_type         VARCHAR(10)     NOT NULL,
                        Start_date          DATE            NOT NULL,
                        Planned_end_date    DATE            NOT NULL,
                        Actual_end_date     DATE,
                        Status              VARCHAR(15)     NOT NULL    DEFAULT 'Scheduled',
        CONSTRAINT OUTAGEPK PRIMARY KEY (Outage_id),
        CONSTRAINT OUTAGEUNITFK FOREIGN KEY (Unit_id) REFERENCES REACTOR_UNIT (Unit_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CHECK (Outage_type IN ('Planned', 'Forced')),
        CHECK (Status IN ('Scheduled', 'In Progress', 'Completed')),
        CHECK (Start_date <= Planned_end_date) );


-- A repair or maintenance job on one piece of equipment
-- Outage_id is NULL if the job is not part of an outage
-- Worker_id is NULL if no one has been assigned yet
CREATE TABLE WORK_ORDER (   Work_order_id   INT             NOT NULL,
                            Equipment_id    INT             NOT NULL,
                            Outage_id       INT,
                            Worker_id       INT,
                            Title           VARCHAR(100)    NOT NULL,
                            Description     VARCHAR(255),
                            Priority        VARCHAR(10)     NOT NULL,
                            Status          VARCHAR(15)     NOT NULL    DEFAULT 'Open',
                            Created_date    DATE            NOT NULL,
                            Due_date        DATE            NOT NULL,
                            Completed_date  DATE,
        CONSTRAINT WOPK PRIMARY KEY (Work_order_id),
        CONSTRAINT WOEQUIPFK FOREIGN KEY (Equipment_id) REFERENCES EQUIPMENT (Equipment_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CONSTRAINT WOOUTAGEFK FOREIGN KEY (Outage_id) REFERENCES OUTAGE (Outage_id)
                                    ON DELETE SET NULL  ON UPDATE CASCADE,
        CONSTRAINT WOWORKERFK FOREIGN KEY (Worker_id) REFERENCES WORKER (Worker_id)
                                    ON DELETE SET NULL  ON UPDATE CASCADE,
        CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        CHECK (Status IN ('Open', 'In Progress', 'Completed', 'Cancelled')),
        CHECK (Created_date <= Due_date) );


-- An inspection done on one piece of equipment
CREATE TABLE INSPECTION (   Inspection_id   INT             NOT NULL,
                            Equipment_id    INT             NOT NULL,
                            Worker_id       INT             NOT NULL,
                            Inspection_date DATE            NOT NULL,
                            Result          VARCHAR(15)     NOT NULL,
                            Notes           VARCHAR(255),
        CONSTRAINT INSPPK PRIMARY KEY (Inspection_id),
        CONSTRAINT INSPEQUIPFK FOREIGN KEY (Equipment_id) REFERENCES EQUIPMENT (Equipment_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CONSTRAINT INSPWORKERFK FOREIGN KEY (Worker_id) REFERENCES WORKER (Worker_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CHECK (Result IN ('Pass', 'Needs Repair', 'Fail')) );


-- A spare part kept in inventory
CREATE TABLE SPARE_PART (   Part_id         INT             NOT NULL,
                            Part_number     VARCHAR(20)     NOT NULL,
                            Name            VARCHAR(50)     NOT NULL,
                            Qty_in_stock    INT             NOT NULL    DEFAULT 0   CHECK (Qty_in_stock >= 0),
                            Reorder_level   INT             NOT NULL    DEFAULT 0   CHECK (Reorder_level >= 0),
                            Unit_cost       DECIMAL(10,2)   NOT NULL    CHECK (Unit_cost >= 0),
        CONSTRAINT PARTPK PRIMARY KEY (Part_id),
        CONSTRAINT PARTSK UNIQUE (Part_number) );


-- Which parts were used on which work order (many-to-many)
CREATE TABLE WORK_ORDER_PART (  Work_order_id   INT     NOT NULL,
                                Part_id         INT     NOT NULL,
                                Qty_used        INT     NOT NULL    CHECK (Qty_used > 0),
        CONSTRAINT WOPARTPK PRIMARY KEY (Work_order_id, Part_id),
        CONSTRAINT WOPARTWOFK FOREIGN KEY (Work_order_id) REFERENCES WORK_ORDER (Work_order_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE,
        CONSTRAINT WOPARTPARTFK FOREIGN KEY (Part_id) REFERENCES SPARE_PART (Part_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE );


-- Weather data saved from the external weather API during an outage
CREATE TABLE WEATHER_LOG (  Weather_id      INT             NOT NULL,
                            Outage_id       INT             NOT NULL,
                            Recorded_at     TIMESTAMP       NOT NULL,
                            Temperature_c   DECIMAL(4,1)    NOT NULL,
                            Wind_speed_kmh  DECIMAL(5,1)    NOT NULL    CHECK (Wind_speed_kmh >= 0),
                            Precip_mm       DECIMAL(5,1)    NOT NULL    DEFAULT 0   CHECK (Precip_mm >= 0),
                            Conditions      VARCHAR(30)     NOT NULL,
        CONSTRAINT WEATHERPK PRIMARY KEY (Weather_id),
        CONSTRAINT WEATHEROUTAGEFK FOREIGN KEY (Outage_id) REFERENCES OUTAGE (Outage_id)
                                    ON DELETE CASCADE   ON UPDATE CASCADE );


-- Login accounts for the web app (used in Phase III)
-- Worker_id is NULL for accounts that are not linked to a worker (for example, guests)
CREATE TABLE USER_ACCOUNT ( User_id         INT             NOT NULL,
                            Username        VARCHAR(30)     NOT NULL,
                            Password_hash   VARCHAR(255)    NOT NULL,
                            Role            VARCHAR(10)     NOT NULL,
                            Worker_id       INT,
        CONSTRAINT USERPK PRIMARY KEY (User_id),
        CONSTRAINT USERSK UNIQUE (Username),
        CONSTRAINT USERWORKERFK FOREIGN KEY (Worker_id) REFERENCES WORKER (Worker_id)
                                    ON DELETE SET NULL  ON UPDATE CASCADE,
        CHECK (Role IN ('admin', 'user', 'guest')) );
