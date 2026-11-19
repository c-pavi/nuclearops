-- SOFE 3700U Data Management Systems
-- Phase II - Part C: Views
-- Project: NuclearOps - Nuclear Plant Maintenance and Outage Tracker
-- DBMS: PostgreSQL
--
-- Run schema.sql and sample_data.sql first, then run this file.
-- Each view is followed by a SELECT that shows its results.

-- View 1: Active work orders with their equipment and location
-- Requirement: computes a join of at least three tables
-- Tables joined: WORK_ORDER, EQUIPMENT, PLANT_SYSTEM, REACTOR_UNIT, STATION

DROP VIEW IF EXISTS ACTIVE_WORK_ORDERS;

CREATE VIEW ACTIVE_WORK_ORDERS AS
SELECT      WO.Work_order_id, WO.Title, WO.Priority, WO.Status, WO.Due_date,
            E.Tag_number, E.Name AS Equipment_name,
            S.Name AS Station_name, R.Unit_number
FROM        WORK_ORDER AS WO
    JOIN    EQUIPMENT AS E      ON WO.Equipment_id = E.Equipment_id
    JOIN    PLANT_SYSTEM AS PS  ON E.System_id = PS.System_id
    JOIN    REACTOR_UNIT AS R   ON PS.Unit_id = R.Unit_id
    JOIN    STATION AS S        ON R.Station_id = S.Station_id
WHERE       WO.Status IN ('Open', 'In Progress');

SELECT * FROM ACTIVE_WORK_ORDERS ORDER BY Due_date;


-- View 2: Worker(s) with the most active work orders
-- Requirement: nested query with the ANY or ALL operator and a GROUP BY clause

DROP VIEW IF EXISTS BUSIEST_WORKERS;

CREATE VIEW BUSIEST_WORKERS AS
SELECT      W.Worker_id, W.Fname, W.Lname, W.Trade, COUNT(*) AS Active_jobs
FROM        WORKER AS W
    JOIN    WORK_ORDER AS WO    ON W.Worker_id = WO.Worker_id
WHERE       WO.Status IN ('Open', 'In Progress')
GROUP BY    W.Worker_id, W.Fname, W.Lname, W.Trade
HAVING      COUNT(*) >= ALL ( SELECT    COUNT(*)
                              FROM      WORK_ORDER
                              WHERE     Status IN ('Open', 'In Progress')
                                        AND Worker_id IS NOT NULL
                              GROUP BY  Worker_id );

SELECT * FROM BUSIEST_WORKERS;


-- View 3: Equipment whose most recent inspection did not pass
-- Requirement: a correlated nested query

DROP VIEW IF EXISTS EQUIPMENT_NEEDING_ATTENTION;

CREATE VIEW EQUIPMENT_NEEDING_ATTENTION AS
SELECT      E.Equipment_id, E.Tag_number, E.Name, I.Inspection_date, I.Result, I.Notes
FROM        EQUIPMENT AS E
    JOIN    INSPECTION AS I     ON E.Equipment_id = I.Equipment_id
WHERE       I.Result <> 'Pass'
            AND I.Inspection_date = ( SELECT    MAX(I2.Inspection_date)
                                      FROM      INSPECTION AS I2
                                      WHERE     I2.Equipment_id = E.Equipment_id );

SELECT * FROM EQUIPMENT_NEEDING_ATTENTION;


-- View 4: All workers and all work orders, matched where possible
-- Requirement: uses a FULL JOIN

DROP VIEW IF EXISTS WORKER_ASSIGNMENTS;

CREATE VIEW WORKER_ASSIGNMENTS AS
SELECT      W.Worker_id, W.Fname, W.Lname,
            WO.Work_order_id, WO.Title, WO.Status
FROM        WORKER AS W
    FULL JOIN   WORK_ORDER AS WO    ON W.Worker_id = WO.Worker_id;

SELECT * FROM WORKER_ASSIGNMENTS ORDER BY Worker_id, Work_order_id;


-- View 5: Certified workers who are free to take a new job
-- Requirement: nested query using a set operation (EXCEPT)

DROP VIEW IF EXISTS AVAILABLE_WORKERS;

CREATE VIEW AVAILABLE_WORKERS AS
SELECT      W.Worker_id, W.Fname, W.Lname, W.Trade, S.Name AS Station_name, W.Cert_expiry
FROM        WORKER AS W
    JOIN    STATION AS S    ON W.Station_id = S.Station_id
WHERE       W.Cert_expiry >= CURRENT_DATE
            AND W.Worker_id IN ( SELECT  Worker_id
                                 FROM    WORKER
                                 EXCEPT
                                 SELECT  Worker_id
                                 FROM    WORK_ORDER
                                 WHERE   Status IN ('Open', 'In Progress') );

SELECT * FROM AVAILABLE_WORKERS;


-- View 6: Equipment that is overdue for inspection
-- Custom view: LEFT JOIN, MAX, GROUP BY and HAVING

DROP VIEW IF EXISTS OVERDUE_INSPECTIONS;

CREATE VIEW OVERDUE_INSPECTIONS AS
SELECT      E.Equipment_id, E.Tag_number, E.Name, E.Inspection_interval_days,
            MAX(I.Inspection_date) AS Last_inspection,
            MAX(I.Inspection_date) + E.Inspection_interval_days AS Next_due
FROM        EQUIPMENT AS E
    LEFT JOIN   INSPECTION AS I     ON E.Equipment_id = I.Equipment_id
GROUP BY    E.Equipment_id, E.Tag_number, E.Name, E.Inspection_interval_days
HAVING      MAX(I.Inspection_date) IS NULL
            OR MAX(I.Inspection_date) + E.Inspection_interval_days < CURRENT_DATE;

SELECT * FROM OVERDUE_INSPECTIONS ORDER BY Next_due;


-- View 7: Spare parts that need to be reordered
-- Custom view: simple selection with a comparison between two columns

DROP VIEW IF EXISTS LOW_STOCK_PARTS;

CREATE VIEW LOW_STOCK_PARTS AS
SELECT      Part_id, Part_number, Name, Qty_in_stock, Reorder_level,
            Reorder_level - Qty_in_stock AS Shortfall
FROM        SPARE_PART
WHERE       Qty_in_stock <= Reorder_level;

SELECT * FROM LOW_STOCK_PARTS ORDER BY Shortfall DESC;


-- View 8: Workers whose certification has expired or expires within 60 days
-- Custom view: join of two tables with date arithmetic

DROP VIEW IF EXISTS EXPIRING_CERTIFICATIONS;

CREATE VIEW EXPIRING_CERTIFICATIONS AS
SELECT      W.Worker_id, W.Fname, W.Lname, W.Trade, S.Name AS Station_name,
            W.Cert_expiry, W.Cert_expiry - CURRENT_DATE AS Days_left
FROM        WORKER AS W
    JOIN    STATION AS S    ON W.Station_id = S.Station_id
WHERE       W.Cert_expiry <= CURRENT_DATE + 60;

SELECT * FROM EXPIRING_CERTIFICATIONS ORDER BY Cert_expiry;


-- View 9: Planned vs. actual length of completed outages
-- Custom view: join of three tables with date arithmetic

DROP VIEW IF EXISTS OUTAGE_SUMMARY;

CREATE VIEW OUTAGE_SUMMARY AS
SELECT      O.Outage_id, S.Name AS Station_name, R.Unit_number, O.Outage_type,
            O.Start_date, O.Planned_end_date, O.Actual_end_date,
            O.Planned_end_date - O.Start_date AS Planned_days,
            O.Actual_end_date - O.Start_date AS Actual_days,
            O.Actual_end_date - O.Planned_end_date AS Days_late
FROM        OUTAGE AS O
    JOIN    REACTOR_UNIT AS R   ON O.Unit_id = R.Unit_id
    JOIN    STATION AS S        ON R.Station_id = S.Station_id
WHERE       O.Status = 'Completed';

SELECT * FROM OUTAGE_SUMMARY ORDER BY Start_date;


-- View 10: Number of unfinished work orders at each priority level
-- Custom view: aggregate function with GROUP BY

DROP VIEW IF EXISTS BACKLOG_BY_PRIORITY;

CREATE VIEW BACKLOG_BY_PRIORITY AS
SELECT      Priority, COUNT(*) AS Open_jobs
FROM        WORK_ORDER
WHERE       Status IN ('Open', 'In Progress')
GROUP BY    Priority;

SELECT * FROM BACKLOG_BY_PRIORITY ORDER BY Open_jobs DESC;


