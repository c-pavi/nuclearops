-- SOFE 3700U Data Management Systems
-- Phase II - Part B: Sample Data
-- Project: NuclearOps - Nuclear Plant Maintenance and Outage Tracker
-- DBMS: PostgreSQL
--
-- Run schema.sql first, then run this file.
-- Station names are real Canadian nuclear sites, but all other data
-- (workers, work orders, inspections, etc.) is made up for this project.
-- Dates are set around November 2026 so some inspections and work orders are overdue.

-- Clear any old data so this file can be run again
DELETE FROM USER_ACCOUNT;
DELETE FROM WEATHER_LOG;
DELETE FROM WORK_ORDER_PART;
DELETE FROM SPARE_PART;
DELETE FROM INSPECTION;
DELETE FROM WORK_ORDER;
DELETE FROM OUTAGE;
DELETE FROM WORKER;
DELETE FROM EQUIPMENT;
DELETE FROM PLANT_SYSTEM;
DELETE FROM REACTOR_UNIT;
DELETE FROM STATION;


-- STATION (6 rows)
INSERT INTO STATION (Station_id, Name, City, Province, Latitude, Longitude)
VALUES  (1, 'Pickering',     'Pickering',   'ON', 43.81188, -79.06612),
        (2, 'Darlington',    'Clarington',  'ON', 43.87250, -78.71972),
        (3, 'Bruce A',       'Tiverton',    'ON', 44.32528, -81.59944),
        (4, 'Bruce B',       'Tiverton',    'ON', 44.33056, -81.57944),
        (5, 'Point Lepreau', 'Saint John',  'NB', 45.06889, -66.45583),
        (6, 'Gentilly-2',    'Becancour',   'QC', 46.39556, -72.35722);


-- REACTOR_UNIT (8 rows)
INSERT INTO REACTOR_UNIT (Unit_id, Station_id, Unit_number, Reactor_type, Capacity_mw, Status)
VALUES  (1, 1, 1, 'CANDU', 515, 'Operating'),
        (2, 1, 5, 'CANDU', 516, 'In Outage'),
        (3, 2, 1, 'CANDU', 878, 'Operating'),
        (4, 2, 3, 'CANDU', 878, 'Refurbishment'),
        (5, 3, 3, 'CANDU', 830, 'Operating'),
        (6, 4, 6, 'CANDU', 817, 'In Outage'),
        (7, 5, 1, 'CANDU', 660, 'Operating'),
        (8, 6, 1, 'CANDU', 675, 'Shut Down');


-- PLANT_SYSTEM (8 rows)
INSERT INTO PLANT_SYSTEM (System_id, Unit_id, Name, Safety_related)
VALUES  (1, 1, 'Primary Heat Transport', TRUE),
        (2, 1, 'Feedwater',              FALSE),
        (3, 2, 'Emergency Core Cooling', TRUE),
        (4, 2, 'Moderator',              TRUE),
        (5, 3, 'Primary Heat Transport', TRUE),
        (6, 3, 'Turbine Generator',      FALSE),
        (7, 6, 'Service Water',          FALSE),
        (8, 7, 'Shutdown System',        TRUE);


-- EQUIPMENT (10 rows)
INSERT INTO EQUIPMENT (Equipment_id, System_id, Tag_number, Name, Equipment_type,
                       Manufacturer, Install_date, Inspection_interval_days)
VALUES  (1,  1, 'P1-PHT-P01', 'Main Coolant Pump 1',        'Pump',   'Byron Jackson', '1971-05-10', 180),
        (2,  1, 'P1-PHT-V12', 'PHT Isolation Valve 12',     'Valve',  'Velan',         '1971-05-10', 90),
        (3,  2, 'P1-FW-P02',  'Feedwater Pump 2',           'Pump',   'Sulzer',        '1985-03-22', 180),
        (4,  3, 'P5-ECC-V04', 'ECC Injection Valve 4',      'Valve',  'Velan',         '1983-07-01', 30),
        (5,  4, 'P5-MOD-HX1', 'Moderator Heat Exchanger 1', 'Heat Exchanger', 'Babcock', '1983-07-01', 365),
        (6,  5, 'D1-PHT-P03', 'Main Coolant Pump 3',        'Pump',   'Byron Jackson', '1990-11-14', 180),
        (7,  6, 'D1-TG-S07',  'Turbine Bearing Sensor 7',   'Sensor', 'Emerson',       '2016-04-18', 60),
        (8,  7, 'B6-SW-L08',  'Service Water Pipe Section 8', 'Pipe', 'Anvil',         '1987-09-30', 365),
        (9,  8, 'PL-SDS-M09', 'Shutdown Rod Drive Motor 9', 'Motor',  'ABB',           '2012-10-23', 90),
        (10, 3, 'P5-ECC-S10', 'ECC Pressure Sensor 10',     'Sensor', 'Rosemount',     '2024-02-12', 60);


-- WORKER (8 rows)
-- Workers 5, 7 and 8 have no work orders (useful for the FULL JOIN view)
-- Worker 4's certification has expired, and worker 2's expires soon
INSERT INTO WORKER (Worker_id, Station_id, Fname, Lname, Email, Trade, Cert_expiry)
VALUES  (1, 1, 'Sarah',  'Chen',     's.chen@nuclearops.ca',     'Mechanical', '2027-06-30'),
        (2, 1, 'Daniel', 'Okafor',   'd.okafor@nuclearops.ca',   'Electrical', '2026-11-30'),
        (3, 2, 'Priya',  'Sharma',   'p.sharma@nuclearops.ca',   'Controls',   '2027-03-15'),
        (4, 2, 'Marc',   'Tremblay', 'm.tremblay@nuclearops.ca', 'Mechanical', '2026-10-15'),
        (5, 3, 'Aisha',  'Rahman',   'a.rahman@nuclearops.ca',   'Inspection', '2027-09-01'),
        (6, 4, 'Liam',   'Murphy',   'l.murphy@nuclearops.ca',   'Electrical', '2027-01-20'),
        (7, 5, 'Emily',  'Gauthier', 'e.gauthier@nuclearops.ca', 'Mechanical', '2028-02-01'),
        (8, 2, 'Kevin',  'Singh',    'k.singh@nuclearops.ca',    'Controls',   '2026-12-10');


-- OUTAGE (7 rows)
-- Actual_end_date is NULL for outages that have not finished yet
INSERT INTO OUTAGE (Outage_id, Unit_id, Outage_type, Start_date, Planned_end_date, Actual_end_date, Status)
VALUES  (1, 2, 'Planned', '2026-09-14', '2026-12-15', NULL,         'In Progress'),
        (2, 6, 'Forced',  '2026-10-28', '2026-11-20', NULL,         'In Progress'),
        (3, 1, 'Planned', '2026-03-02', '2026-04-30', '2026-05-12', 'Completed'),
        (4, 3, 'Planned', '2025-09-08', '2025-11-07', '2025-11-03', 'Completed'),
        (5, 5, 'Forced',  '2026-06-10', '2026-06-20', '2026-06-24', 'Completed'),
        (6, 7, 'Planned', '2027-04-05', '2027-05-28', NULL,         'Scheduled'),
        (7, 4, 'Planned', '2026-02-01', '2029-06-30', NULL,         'In Progress');


-- WORK_ORDER (13 rows)
-- Work orders 5, 9 and 10 have no worker assigned (Worker_id is NULL)
-- Work orders 7, 11, 12 and 13 are not part of an outage (Outage_id is NULL)
-- Work orders 5 and 7 are past their due date and not completed
INSERT INTO WORK_ORDER (Work_order_id, Equipment_id, Outage_id, Worker_id, Title, Description,
                        Priority, Status, Created_date, Due_date, Completed_date)
VALUES  (1,  1,  3,    1,    'Replace pump seal',              'Seal leaking during last run',       'High',     'Completed',   '2026-02-15', '2026-04-15', '2026-04-10'),
        (2,  2,  3,    2,    'Rebuild valve actuator',         'Actuator slow to respond',           'Medium',   'Completed',   '2026-02-20', '2026-04-20', '2026-05-08'),
        (3,  4,  1,    1,    'Replace ECC valve packing',      'Failed last inspection',             'Critical', 'In Progress', '2026-09-01', '2026-11-30', NULL),
        (4,  5,  1,    2,    'Clean heat exchanger tubes',     'Reduced heat transfer',              'High',     'Open',        '2026-09-01', '2026-12-01', NULL),
        (5,  10, 1,    NULL, 'Calibrate pressure sensor',      'New sensor, never calibrated',       'High',     'Open',        '2026-10-01', '2026-11-01', NULL),
        (6,  6,  4,    3,    'Vibration analysis on pump 3',   'Routine outage check',               'Medium',   'Completed',   '2025-08-15', '2025-10-30', '2025-10-20'),
        (7,  7,  NULL, 3,    'Replace bearing temp sensor',    'Sensor reading high',                'Low',      'Open',        '2026-10-10', '2026-10-31', NULL),
        (8,  8,  2,    6,    'Repair service water pipe leak', 'Leak found during walkdown',         'Critical', 'In Progress', '2026-10-28', '2026-11-15', NULL),
        (9,  8,  2,    NULL, 'Pipe wall thickness check',      'Check pipe next to the leak',        'High',     'Open',        '2026-10-29', '2026-11-18', NULL),
        (10, 9,  6,    NULL, 'Overhaul shutdown rod motor',    'Planned for next outage',            'Medium',   'Open',        '2026-10-15', '2027-05-15', NULL),
        (11, 6,  NULL, 4,    'Lubricate coolant pump bearings','Done by another crew',               'Low',      'Cancelled',   '2026-07-01', '2026-07-31', NULL),
        (12, 6,  NULL, 3,    'Replace coolant pump coupling',  'Wear found on coupling',             'High',     'Open',        '2026-10-20', '2026-11-25', NULL),
        (13, 1,  NULL, 1,    'Inspect pump motor wiring',      'Follow up from seal replacement',    'Medium',   'Completed',   '2026-08-01', '2026-08-31', '2026-08-20');


-- INSPECTION (12 rows)
-- Equipment 2, 4 and 7 are overdue for inspection, and equipment 10 has never been inspected
INSERT INTO INSPECTION (Inspection_id, Equipment_id, Worker_id, Inspection_date, Result, Notes)
VALUES  (1,  1, 1, '2026-01-10', 'Pass',         'No issues'),
        (2,  1, 1, '2026-07-05', 'Pass',         'New seal working well'),
        (3,  2, 2, '2026-03-10', 'Needs Repair', 'Actuator response is slow'),
        (4,  2, 2, '2026-06-01', 'Pass',         'Actuator rebuilt'),
        (5,  3, 2, '2026-08-15', 'Pass',         'No issues'),
        (6,  4, 1, '2026-08-28', 'Fail',         'Packing leak on valve stem'),
        (7,  5, 2, '2026-09-05', 'Needs Repair', 'Tube fouling found'),
        (8,  6, 3, '2025-08-10', 'Needs Repair', 'High vibration'),
        (9,  6, 3, '2026-05-20', 'Pass',         'Vibration back to normal'),
        (10, 7, 4, '2026-07-15', 'Needs Repair', 'Reading drifting high'),
        (11, 8, 5, '2025-11-12', 'Pass',         'Wall thickness OK'),
        (12, 9, 7, '2026-09-20', 'Pass',         'No issues');


-- SPARE_PART (8 rows)
-- Parts 1, 3 and 5 are below their reorder level, and part 7 is at its reorder level
INSERT INTO SPARE_PART (Part_id, Part_number, Name, Qty_in_stock, Reorder_level, Unit_cost)
VALUES  (1, 'SP-1001', 'Pump mechanical seal',    4,  5,  1250.00),
        (2, 'SP-1002', 'Valve packing set',       20, 10, 85.50),
        (3, 'SP-1003', 'Valve actuator kit',      1,  2,  3400.00),
        (4, 'SP-2001', 'Pressure transmitter',    6,  3,  920.00),
        (5, 'SP-2002', 'RTD temperature sensor',  2,  4,  310.00),
        (6, 'SP-3001', 'Heat exchanger gasket',   12, 6,  145.00),
        (7, 'SP-3002', 'Pipe repair clamp',       3,  3,  560.00),
        (8, 'SP-4001', 'Motor bearing',           10, 4,  275.00);


-- WORK_ORDER_PART (10 rows)
INSERT INTO WORK_ORDER_PART (Work_order_id, Part_id, Qty_used)
VALUES  (1,  1, 2),
        (2,  3, 1),
        (2,  2, 1),
        (3,  2, 2),
        (4,  6, 4),
        (5,  4, 1),
        (6,  8, 2),
        (7,  5, 1),
        (8,  7, 2),
        (12, 1, 1);


-- WEATHER_LOG (8 rows)
INSERT INTO WEATHER_LOG (Weather_id, Outage_id, Recorded_at, Temperature_c, Wind_speed_kmh, Precip_mm, Conditions)
VALUES  (1, 1, '2026-09-15 08:00:00', 21.5, 14.0, 0.0, 'Clear'),
        (2, 1, '2026-10-15 08:00:00', 9.0,  22.5, 3.2, 'Rain'),
        (3, 1, '2026-11-04 08:00:00', 4.5,  30.0, 0.0, 'Cloudy'),
        (4, 2, '2026-10-28 12:00:00', 6.0,  41.0, 8.5, 'Rain'),
        (5, 2, '2026-11-03 12:00:00', 2.5,  35.5, 1.0, 'Snow'),
        (6, 3, '2026-03-05 09:00:00', -6.0, 25.0, 2.0, 'Snow'),
        (7, 3, '2026-04-20 09:00:00', 8.5,  18.0, 0.0, 'Clear'),
        (8, 5, '2026-06-12 14:00:00', 27.0, 12.0, 0.0, 'Clear');


-- USER_ACCOUNT (7 rows)
-- The password hashes are placeholders and will be replaced with real hashes in Phase III
INSERT INTO USER_ACCOUNT (User_id, Username, Password_hash, Role, Worker_id)
VALUES  (1, 'admin',       'placeholder_hash_1', 'admin', NULL),
        (2, 'schen',       'placeholder_hash_2', 'user',  1),
        (3, 'dokafor',     'placeholder_hash_3', 'user',  2),
        (4, 'psharma',     'placeholder_hash_4', 'admin', 3),
        (5, 'lmurphy',     'placeholder_hash_5', 'user',  6),
        (6, 'guest1',      'placeholder_hash_6', 'guest', NULL),
        (7, 'cnsc_viewer', 'placeholder_hash_7', 'guest', NULL);
