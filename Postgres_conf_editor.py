import paramiko
import psycopg2
import easygui as eg
import sys


ch1=eg.msgbox(msg=" Welcome to Postgres Configuration Editor",title="Welcome",ok_button="Start")
if (ch1=='Start'):
    pass
else:
    sys.exit(0)

def check_none(var):
    if var is None:
        sys.exit(0)
    else:
        pass

msg = "Choose your desired Postgres Property to be changed"
title = "Postgres Configuration Editor"

msg1 = "\t\tEnter Server information \n [For reflecting changes, log in as postgres user]"
title1 = "Server Details"
fieldNames = ["Server IP","Username"]
fieldValues = []  # we start with blanks for the values
fieldValues = eg.multenterbox(msg1,title1, fieldNames)

while 1:
    if fieldValues == None: break
    errmsg = ""
    for i in range(len(fieldNames)):
      if fieldValues[i].strip() == "":
        errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
    if errmsg == "": break # no problems found
    fieldValues = eg.multenterbox(errmsg, title, fieldNames, fieldValues)
print ("Reply was:", fieldValues)


pwd1=eg.passwordbox(msg='Please Enter the Password For the Username : '+fieldValues[1], title='Password')

check_none(pwd1)


ip=fieldValues[0]
port=22
username=fieldValues[1]
password=pwd1



show_cmds = ["show data_directory","show shared_buffers","show huge_pages","show temp_buffers" ,"show max_prepared_transactions" ,"show work_mem" ,"show maintenance_work_mem" ,"show autovacuum_work_mem" ,"show max_stack_depth" ,"show dynamic_shared_memory_type"]
prop_exts_val = []
config_lines =[]

msg2 = "Enter Database information"
title2 = "DB Details"
fieldNames2 = ["DB Name","DB User"]
fieldValues2 = []  # we start with blanks for the values
fieldValues2 = eg.multenterbox(msg2,title2, fieldNames2)

while 1:
    if fieldValues2 == None: break
    errmsg = ""
    for i in range(len(fieldNames2)):
      if fieldValues2[i].strip() == "":
        errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames2[i])
    if errmsg == "": break # no problems found
    fieldValues2 = eg.multenterbox(errmsg, title2, fieldNames2, fieldValues2)
print ("Reply was:", fieldValues2)

pwd2=eg.passwordbox(msg='Please Enter the Password For the DB  User : '+fieldValues2[1], title='Password')

check_none(pwd2)

conn1 = psycopg2.connect(database=fieldValues2[0], user = fieldValues2[1], password = pwd2, host = fieldValues[0], port = "5432")
curs1=conn1.cursor()

for i in show_cmds:
    curs1.execute(i)
    prop_exts_val.append(curs1.fetchone()[0])

pro_dict = dict(zip(show_cmds,prop_exts_val))
print(pro_dict)
    
print("Data Directory of the sever "+ ip + " is "+prop_exts_val[0])

cmd='cat '+prop_exts_val[0]+'/postgresql.conf | sed -e "/max_coneections/p"' 

ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(ip,port,username,password)

stdin,stdout,stderr=ssh.exec_command("awk '/MemTotal/ {print $2}' /proc/meminfo")
outlines=stdout.readlines()
sys_mem=''.join(outlines)

print(sys_mem)

sys_mem_40 = str((int(sys_mem)* 0.4)/1000000)[0:2]+ 'GB'
sys_mem_5 = str((int(sys_mem) * 0.05)/1000000)[0:2]+ 'GB'

for i in show_cmds:
    stdin,stdout,stderr=ssh.exec_command('cat ' + prop_exts_val[0] +'/postgresql.conf | sed -n "/'+i.replace("show ","")+'/p "')
    outlines=stdout.readlines()
    resp=''.join(outlines)
    config_lines.append(resp.splitlines()[0])

del config_lines[0]
print(config_lines)
print(len(config_lines))

choices = ["shared_buffers","huge_pages","temp_buffers" ,"max_prepared_transactions" ,"work_mem" ,"maintenance_work_mem" ,"autovacuum_work_mem" ,"max_stack_depth" ,"dynamic_shared_memory_type"]
rcomm = [sys_mem_40.replace(".","")+" (Max 40% of system memory)","try","8-10 MB","60","Define value based on Explain analyze | Recommended to be greater than maintenance_work_mem.",sys_mem_5.replace(".","")+" (5% system memory)","Disable when loading bulk volume of data","2 MB | should be always less than 6MB","Posix"]

choic_rcom_dict = dict(zip(choices,rcomm))
prop_lines_d = dict(zip(choices,config_lines))
op ={}
final_op = {}

def fn():
            choice = eg.choicebox(msg, title,choices)
            if choice in choices:
                c =['Continue','Cancel','Restart']
                host_v1=eg.enterbox(msg='Current Value = '+pro_dict['show '+choice]+'\nRecommendation : '+choic_rcom_dict[choice] +'\n\n Enter The New Value along with memory size if needed', title=choice,)
                if host_v1.strip() == '' :
                    fn()
                else:
                    bb=eg.buttonbox(title='Action',choices =c)
                    if bb == 'Continue':
                        op[choice]=host_v1
                        fn()        
                    if bb == 'Cancel':
                        fn()
                    if bb == 'Restart':
                        op[choice]=host_v1
                        print(op)
                        for i,j in op.items():
                            source_line = prop_lines_d[i]
                            ext_value = pro_dict['show '+i]
                            new_value = op[i]
                            print(ext_value)
                            print(new_value)
                            rep_line = source_line.replace(ext_value,new_value,1)
                            final_op[source_line] = rep_line
                        for i,j in final_op.items():
                            print( i +'\n'+ j)
                            stdin,stdout,stderr=ssh.exec_command("sed -i 's/"+i+"/"+j+"/g' "+prop_exts_val[0]+'/postgresql.conf')
                        #rst_d=eg.enterbox(msg='Enter Path to Postgres bin', title='Postgres Directory')
                        #check_none(rst_d)
                        #stdin,stdout,stderr=ssh.exec_command('cd '+rst_d+'\./pg_ctl restart -D '+prop_exts_val[0])
                        #print('Restart Completed')
                        #eg.msgbox(msg="Postgres Restart Initiated Sucessful",title="Done",ok_button="Start")
                        eg.msgbox("Application Developed by Seshadri of TCS Optumera Base Product DB Team",title="About",ok_button='Close')




    
                            

fn()
	


