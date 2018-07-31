# Author: Da'Mya Campbell (damycamp@cisco.com) 
# File: devicestatus.py
# Date: June 2018 (c) Cisco Systems
# Description: Queries information from eITMS database and compares it to a list of devices used/ owned by Unified Performance 
# and determines which devices have incorrect ownership information. 

import json
import cx_Oracle
import csv

with open('/Volumes/local/unifiedperformance/damycamp/deviceinfotwo.json', 'r') as file:
    # extract serial numbers from DNAC JSON response
    data = json.load(file)
    serial_numbers = []
    for i in range(len(data['response'])):
        serial_numbers.append(data['response'][i]['serialNumber'])
    print(serial_numbers)
    up_devices = []
    for i in serial_numbers:
        up_devices.append("'"+i+"'")

    # connect to eITMS database
    con = cx_Oracle.connect('eitms_ro/eitms_ro123@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=sjc-dbdl-eitms.cisco.com)(PORT=1521))(CONNECT_DATA=(GLOBAL_NAME=eitmsstg.cisco.com)(SID=EITMSSTG)))')
    cur = con.cursor()
    sql_command = "SELECT asset_vw.building_name, asset_vw.lab_name, asset_vw.aisle_name, asset_vw.loc_in_aisle_name, "
    " asset_vw.serial_no, si_dept_vw.dept_name, asset_vw.functional_manager_userid, asset_vw.code" \
    " FROM asset_vw JOIN asset_location_vw ON asset_vw.serial_no = asset_location_vw.serial_no" \
    " JOIN si_dept_vw ON asset_vw.dept_no = si_dept_vw.dept_no WHERE asset_vw.building_name = 'RTP8M'" \
    " AND (asset_vw.floor = '1' OR asset_vw.floor = '3') AND (asset_vw.lab_name = 'Meadow-1' OR asset_vw.lab_name = 'Meadow 3')" \
    " AND (asset_vw.aisle_name = 'CC' OR asset_vw.aisle_name = 'D' OR asset_vw.aisle_name = 'DD' OR asset_vw.aisle_name = 'E')" \
    " AND asset_vw.serial_no IN (" + ', '.join(up_devices)+ ")"
    cur.execute(sql_command)
    results = cur.fetchall()
    outdated_devices = []
    print('The devices below need to be updated: ')
    for i in results:
        # convert nontypes to strings 
        i = list(i)
        for num in range(len(i)):
            if i[num] == None:
                i[num] = 'unknown'
        d = {
            'building': i[0],
            'lab': i[1],
            'row': i[2],
            'rack': i[3],
            'serial': i[4],
            'dept': i[5],
            'manager': i[6],
            'asset tag': i[7]
        }
        # determine what devices have incorrect ownership information and display current 
        if i[6] != 'mclaes' or i[5] != 'EN Eng Ent Routing - US':
            outdated_devices.append(d)   
        print('Device '+i[4]+' with asset tag: '+i[7]+' is currently owned by department '+i[5]+' and manager '+i[6]+'. The current location is Building: '+i[0]+', Lab: '+i[1]+', Row: '+i[2]+', Rack '+i[3])

    # create csv file to send to AMS
    csv_columns = ['building', 'lab', 'row', 'rack', 'serial', 'dept', 'manager', 'asset tag']
    csv_file = 'outdated_up_devices.csv'
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = csv_columns)
            writer.writeheader()
            for data in outdated_devices:
                writer.writerow(data)
    except IOError:
        print('I/O error')           