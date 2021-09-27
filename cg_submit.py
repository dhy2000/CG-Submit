'''
** CourseGrading Auto-Submit Script **
'''
import json
import requests
import time
import threading
import sys, os

# Global Variables
CONFIG_NAME = 'cg_config.json'
RESULT_REFRESH_INTERVAL = 3 # request newest status per 3 seconds.

# Configs
root_url = ""

user_agent = ""
user_name = ""
user_passwd = ""
user_id = ""
course_id = ""

submits = [] # (assignID, problemID)

submit_file = ""

save_result = False

# Request
request_headers = {}

# Cookies
JSESSIONID = ""

# Preparing
def start():
    try:
        with open(CONFIG_NAME, "r") as fp:
            cfg = fp.read()
            cfg = json.loads(cfg)
            return cfg
    except Exception:
        print("Error on parsing json-format configs.", file=sys.stderr)
        sys.exit(0)

def loadcfg(cfg: dict):
    global root_url
    global user_agent, user_name, user_passwd, user_id, course_id
    global submits, save_result
    try:
        root_url = cfg['root-url']
        user_agent = cfg['request']['User-Agent']
        user_name = cfg['login']['username']
        user_passwd = cfg['login']['password']
        user_id = cfg['login']['userID']
        course_id = cfg['login']['courseID']
        for submit in cfg['submit']:
            assignID = submit['assignID']
            problemID = submit['problemID']
            submits.append((assignID, problemID))
        if 'save-result' in cfg.keys():
            save_result = cfg['save-result']
    except Exception:  # KeyError
        print("Error on loading configs.", file=sys.stderr)
        sys.exit(0)

def readfile():
    if len(sys.argv) < 2:
        print("Please specify the file to submit.", file=sys.stderr)
        print("Usage: python -u cg_submit.py file.zip")
        sys.exit(0)
    global submit_file
    submit_file = sys.argv[1]
    # Test existance of the file
    if not os.path.exists(submit_file):
        print("Submit file not exist!", file=sys.stderr)
        sys.exit(0)
    if not os.path.isfile(submit_file):
        print("Please choose a **file** to submit.", file=sys.stderr)
        sys.exit(0)

# Connect and login
def connect():
    global root_url
    global user_agent, user_name, user_passwd, user_id, course_id
    global submits
    global request_headers
    global JSESSIONID

    request_headers = {
        "User-Agent": user_agent
    }

    # Connect and get JSESSIONID
    connect_url = root_url + "/indexcs/simple.jsp?loginErr=0"
    r = requests.get(connect_url, headers=request_headers)
    if r.status_code != 200:
        print("Connect website failed! Status = {0}".format(r.status_code))
        sys.exit(0)
    print("CourseGrading connect succeed!")
    JSESSIONID = r.cookies.get("JSESSIONID")
    print("JSESSIONID = {0}".format(JSESSIONID))
    request_headers['Cookie'] = "JSESSIONID={0};".format(JSESSIONID)

    # Login
    login_url = root_url + "/login/loginproc.jsp"
    login_postbody = {
        "IndexStyle": "1",
        "stid": user_name,
        "pwd": user_passwd
    }
    r = requests.post(login_url, data=login_postbody, headers=request_headers)
    if r.status_code != 200:
        print("Login failed by fatal errors. Status={0}".format(r.status_code), file=sys.stderr)
        sys.exit(0)
    if 'loginErr=1' in r.url:
        print("Login failed by wrong username or password.")
        sys.exit(0)
    print("Login succeed!".format(r.status_code))
    
    # Select Course
    course_url = root_url + "/courselist.jsp"
    course_params = {
        "courseID": course_id
    }
    r = requests.get(course_url, params=course_params, headers=request_headers)
    if r.status_code != 200:
        print("Select course error! Status={0}".format(r.status_code), file=sys.stderr)
        sys.exit(0)
    print("Course select done!")

def save_judge_result(prob: tuple, result: str):
    output_filename = "{0}_{1}.html".format(prob[0], prob[1])
    print("Detailed judge result of assign {0}, problem {1} is saved to {2}".format(prob[0], prob[1], output_filename))
    with open(output_filename, "w") as fp:
        print(result, file=fp)

def submit_one(prob: tuple):
    global root_url
    global user_id
    global request_headers, submit_file
    global save_result

    submit_url = root_url + "/assignment/showOJPProcessMsg.jsp"
    submit_params = {
        "assignID": prob[0],
        "problemID": prob[1],
        "doSubmit": "true",
        "wtime": "100"
    }
    submit_headers = request_headers.copy()
    submit_headers['X-Requested-With'] = 'XMLHttpRequest'
    submit_files = {'file': open(submit_file, 'rb')}

    print("Submitting {0} on assign {1}, problem {2}......".format(submit_file, prob[0], prob[1]))

    r = requests.post(submit_url, 
        params=submit_params, 
        headers=submit_headers, 
        files=submit_files)
    
    if r.status_code != 200:
        print("Submit failed. Status={0}".format(r.status_code), file=sys.stderr)
        return
    print("Submit done on assign {0}, problem {1}, waiting for judge result".format(prob[0], prob[1]))
    # Waiting for judge result
    query_param = {
        "assignID": prob[0],
        "problemID": prob[1],
        "userID": user_id
    }
    query_url = root_url + "/assignment/showOJPProcessJSON.jsp"
    judge_start = time.time()
    while True:
        time.sleep(RESULT_REFRESH_INTERVAL)
        r = requests.get(query_url, params=query_param, headers=request_headers)
        if r.status_code != 200:
            continue
        try:
            judge_status = r.json()
            is_working = judge_status[0]['ret']
            if (is_working == '1'):
                # Judge Done!
                judge_end = time.time()
                judge_timecost = judge_end - judge_start
                print("Judge on assign {0}, problem {1} done, cost {2:.3f} secs!".format(prob[0], prob[1], judge_timecost))
                if save_result:
                    judge_result = judge_status[1]['content']
                    save_judge_result(prob=prob, result=judge_result)
                return
        except Exception:
            print("Error on parsing json judge status!", file=sys.stderr)
            print(r.text)
            return

submit_threads = []

if __name__ == '__main__':
    cfg = start()
    loadcfg(cfg)
    readfile()

    if len(submits) == 0:
        print("Warning: nothing to submit.")
        sys.exit(0)

    connect()

    for prob in submits:
        th = threading.Thread(target=submit_one, args=(prob,))
        submit_threads.append(th)
        th.start()
    
    for th in submit_threads:
        th.join()