import time
import requests

def post_configure():
    url = "http://localhost:8080/configure"

    params = {
        "suite_id": "3a7ce19b-13d6-483b-8262-6ec1fd0ab927",
        "iut_provider": "default",
        "execution_space_provider": "default",
        "log_area_provider": "default",
        "dataset": {'exec_space_amount': 3, 'iut_amount': 3, 'logs_amount': 1}
    }

    r = requests.post(url, json=params)
    print(r.text)

def post_doit():
    url = "http://localhost:8080"

    params = {
        "suite_id": "3a7ce19b-13d6-483b-8262-6ec1fd0ab927",
    }

    r = requests.post(url, json=params)
    print(r.text)
    return r.json()["data"]["id"]

def get_env(environment_id):
    url = "http://localhost:8080"

    response = requests.get(url, params={"id": environment_id})
    return response

#configure
post_configure()
time.sleep(2)

#activate
env_id = post_doit()
time.sleep(10)

#Poll status and print when "SUCCESS"
while True:
    resp = get_env(env_id)
    if resp.json()["status"] == "SUCCESS":
        print(resp.text)
        break
