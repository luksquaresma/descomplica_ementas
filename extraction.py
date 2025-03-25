from auth import auth
from utils import *
from time import sleep
from tqdm import tqdm

import copy, multiprocessing, os, requests, tabula, warnings
import pandas as pd

warnings.filterwarnings("ignore")

# basic configuration from external file
with open("./config.json") as file:
    config = dict(json.load(file))

os.makedirs(config["local"]["path_log"].removesuffix(".log"), exist_ok=True) 
os.makedirs(config["local"]["path_result"], exist_ok=True) 
os.makedirs(config["local"]["path_session_data"], exist_ok=True) 

def reset_config(config):
    globals()["config"] = copy.deepcopy(config)

# = = = = = PREPARATION = = = = =

# - - - - - Destinations
# desired output files based on a input pdf file
def get_sources():
    df = tabula.read_pdf(
        config["hist_file"],
        pages="all",
        pandas_options={'header':None}
    )
    df = pd.concat(df)
    df = pd.DataFrame(df.values[1:], columns=df.values[0]).reset_index()
    return [
        (x[:4].zfill(4), x[7:]) # (code, name)
        for x in df["Disciplina"].values]

# raw sources overwriting
def set_sources():
    config["raw_source"] = [
        {
            "code": str(code),
            "name": str(name),
            "url": config["url_base"].replace(config["url_base_placehoder"], str(code))
        }
        for (code, name) in get_sources()
    ]
    with open("./config.json", "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    reset_config(config)
# - - - - -

# - - - - - Extraction
# single job - extraction routine
def extract_json_from_url(args):
    (job, cookies, trys, path_log, path_result, log_terminal_macro, log_terminal_micro) = args

    result_content = None
    atempts = 0
    suffix = f'- JOB {job["code"]}, NAME {job["name"]}'

    while atempts < trys and result_content == None:
        try:
            response = requests.request(method="GET", url=job["url"], verify=True, cookies=cookies, timeout=1e6)     
            if response.status_code == 200:
                try:
                    try:                                
                        with open(f'{path_result}{job["code"]}_{job["name"]}.pdf', 'wb') as f:
                            f.write(response.content)
                        log(f"Finished job. {suffix}", path_log, log_terminal=log_terminal_micro)    
                        break
                    except Exception as e:
                        log(f"Error saving JSON file: {suffix}\n{e}", path_log, log_terminal=log_terminal_macro)
                        if config["stop_if_error"]: raise
                except Exception as e:
                    log(f"Error parsing JSON results: {suffix}\n{e}", path_log, log_terminal=log_terminal_macro)
                    if config["stop_if_error"]: raise
        except Exception as e:
            log(f"Error performing request: {suffix}\n{e}", path_log, log_terminal=log_terminal_macro)
            sleep(1)
            if config["stop_if_error"]: raise
        atempts += 1
        if atempts == trys:
            log(f"Error performing request: {suffix}\nMaximun number of tries exeeded.", path_log, log_terminal=log_terminal_micro)
            

# interface - multiprocessing extraction
def extract(config, log_terminal_macro=config["terminal_log_macro"], log_terminal_micro=config["terminal_log_micro"]):
    setup = config["raw_source"]
    max_proc = multiprocessing.cpu_count()
    max_proc = config["max_proc"] if config["max_proc"] < max_proc else max_proc
    max_trys = config["max_get_trys"]
    # cookies = config["cookies"]
    cookies = auth(config["url_auth"], config["cookie_list"])

    path_log = config["local"]["path_log"]
    path_result = config["local"]["path_result"]
    prep_dir([get_dir_from_file_path(path_log), path_result])

    log(f"\n\n", path_log, log_terminal=log_terminal_macro)
    log(f"STARTING ALL EXTRACTION PROCESSES", path_log, log_terminal=log_terminal_macro)
    with multiprocessing.Pool(processes=(max_proc if len(setup) > max_proc else len(setup))) as pool:
        with tqdm(total=len(setup), position=0, 
                  leave=True, disable=(not log_terminal_macro)) as global_pbar:
            for _ in pool.imap_unordered(
                extract_json_from_url,
                [
                    (
                        job,
                        cookies,
                        max_trys,
                        path_log,
                        path_result,
                        log_terminal_macro,
                        log_terminal_micro    
                    )
                    for job in setup
                ],
                chunksize=1):
                global_pbar.update()
    log(f"FINISHED ALL EXTRACTION PROCESSES\n\n", path_log, log_terminal=log_terminal_macro)
# - - - - -
# = = = = =



# - - - - - Procedure call via config file
def perform(step):
    match step:
        case "overwride_sources": 
            set_sources()
        case "extraction": 
            extract(config)
# - - - - -


# = = = = = EXECUTION = = = = =
for (step, to_perform) in config["steps_to_perform"].items():
    log(f"STARTING ALL PROCESSES\n\n", config["local"]["path_log"], log_terminal=config["terminal_log_macro"])
    if to_perform: perform(step) # only works on ordered dictionaries (python >= 3.7)
    log(f"FINISHED ALL PROCESSES\n\n", config["local"]["path_log"], log_terminal=config["terminal_log_macro"])
    