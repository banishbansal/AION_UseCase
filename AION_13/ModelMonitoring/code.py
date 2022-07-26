#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This file is automatically generated by AION for AION_13_1 usecase.
File generation time: 2022-07-22 07:02:00
'''
#Standard Library modules
import logging
import sys
import json
import time
import platform
import tempfile
import shutil
import argparse
import sklearn
import pandas as pd
from pathlib import Path
#Third Party modules
from pathlib import Path

IOFiles = {
"log": "aion.log",
"trainingData":"rawData.dat",
"production": "production.json",
"prodGrndTruData":"prodDataGT.dat",
"prodData":"prodData.dat",
"monitoring":"monitoring.json"
}


def read_json(file_path):                    
    data = None                    
    with open(file_path,'r') as f:                    
        data = json.load(f)                    
    f.close()		
    return data
def write_json(data, file_path):                    
    with open(file_path,'w') as f:                    
        json.dump(data, f)	
    f.close()

                    
log = None                    
def set_logger(log_file, mode='a'):                    
    global log                    
    logging.basicConfig(filename=log_file, filemode=mode, format='%(asctime)s %(name)s- %(message)s', level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')                    
    log = logging.getLogger(Path(__file__).parent.name)                    
    return log                    
                    
def get_logger():                    
    return log

def is_drift_within_limits(production, current_matrices,scoring_criteria,threshold = 5):
    testscore = production['score']/100
    current_score = current_matrices[scoring_criteria]
    threshold_value = testscore * threshold / 100.0
    if current_score > (testscore - threshold_value) :
        return True
    else:
        return False

def get_metrices(actual_values, predicted_values):        
    from sklearn.metrics import accuracy_score
    from sklearn.metrics import precision_score
    from sklearn.metrics import recall_score
    from sklearn.metrics import f1_score
    result = {} 
    accuracy_score = accuracy_score(actual_values, predicted_values)        
    avg_precision = precision_score(actual_values, predicted_values,        
        average='macro')        
    avg_recall = recall_score(actual_values, predicted_values,        
        average='macro')        
    avg_f1 = f1_score(actual_values, predicted_values,        
        average='macro')        
        
    result['accuracy'] = accuracy_score        
    result['precision'] = avg_precision        
    result['recall'] = avg_recall        
    result['f1'] = avg_f1        
    return result            
            	
def monitoring(config):
    from input_drift import inputdrift
    if platform.system() == 'Windows':        
        targetPath = Path(config['targetPath'])
    else:        
        targetPath = Path('/aion')/config['targetPath']
    targetPath.mkdir(parents=True, exist_ok=True)	 	
    log_file = targetPath/IOFiles['log']
    logger = set_logger(log_file)
    output_json = {}
    trainingDataLocation = targetPath/IOFiles['trainingData']
    actual_data_path = targetPath/IOFiles['prodGrndTruData']
    predict_data_path = targetPath/IOFiles['prodData']	
    logger.info(f'Input Location External: {config["inputUriExternal"]}')
    trainingStatus = 'False'
    dataFileLocation = ''	
    driftStatus = 'No Drift'
    if trainingDataLocation.exists(): 	
        production= targetPath/IOFiles['production']
        if production.exists():        
            production = read_json(production)  
            if actual_data_path.exists() and predict_data_path.exists():
                predicted_data = pd.read_csv(predict_data_path)        		
                actual_data_path = pd.read_csv(actual_data_path)
                common_col = [k for k in predicted_data.columns.tolist() if k in actual_data_path.columns.tolist()]				
                mergedRes = pd.merge(actual_data_path, predicted_data, on =common_col,how = 'inner')
                currentPerformance = {} 			
                currentPerformance = get_metrices(mergedRes[config['target_feature']], mergedRes['prediction'])
                if is_drift_within_limits(production, currentPerformance,config['scoring_criteria']):
                    get_logger().info(f'OutputDrift: No output drift found')				
                    output_json.update({'outputDrift':'Model score is with in limits'}) 					
                else:
                    get_logger().info(f'OutputDrift: Found Output Drift')				
                    get_logger().info(f'Original Test Score: {performance["metrices"]["test_score"]}')					
                    get_logger().info(f'Current Score: {currentPerformance[performance["scoring_criteria"]]}')				
                    output_json.update({'outputDrift':{'Meassage': 'Model output is drifted','trainedScore':performance['metrices']['test_score'], 'currentScore':currentPerformance[performance['scoring_criteria']]}})
                    trainingStatus = 'True'
                    driftStatus = 'Output Drift'					
            else:
                get_logger().info(f'OutputDrift: Prod Data not found')			
                output_json.update({'outputDrift':'Prod Data not found'}) 
        else:
            get_logger().info(f'Last Time pipeline not executed completely')		
            output_json.update({'Msg':'Pipeline is not executed completely'})
            trainingStatus = 'True'
            if config['inputUriExternal']:		
                dataFileLocation = config['inputUriExternal']
            else:
                dataFileLocation = config['inputUri']			
				
			
        if trainingStatus == 'False':	       			
            historicaldataFrame=pd.read_csv(trainingDataLocation)        
            currentdataFrame=pd.read_csv(config['inputUriExternal']) 	
            inputdriftObj = inputdrift(config)
            dataalertcount,inputdrift_message = inputdriftObj.get_input_drift(currentdataFrame,historicaldataFrame)	

            if inputdrift_message == 'Model is working as expected':
                get_logger().info(f'InputDrift: No input drift found')			
                output_json.update({'Status':'SUCCESS','inputDrift':'Model is working as expected'})        
            else:        
                get_logger().info(f'InputDrift: Input drift found')			
                get_logger().info(f'Affected Columns {inputdrift_message}')			
                output_json.update({'inputDrift':{'Affected Columns':inputdrift_message}})        
                trainingStatus = 'True'
                if config['inputUriExternal']:
                    dataFileLocation = config['inputUriExternal']
                if actual_data_path.exists() and predict_data_path.exists():	
                    dataFileLocation = ''
                else:
                    raise ValueError(f'DataLocation Not Found')
                driftStatus = 'Input Drift'					
    else:
        get_logger().info(f'Pipeline Executing first Time')	
        output_json.update({'Msg':'Pipeline executing first time'}) 	
        trainingStatus = 'True'
        if config['inputUriExternal']:		
            dataFileLocation = config['inputUriExternal']
        else:
            dataFileLocation = config['inputUri']
    monitoring = targetPath/IOFiles['monitoring']
    if monitoring.exists():
        data = read_json(monitoring)
        runNo = int(data['runNo'])+1		
    else:
        runNo = 1
    monitoring_status = {'runNo':runNo,'dataLocation':dataFileLocation,'driftStatus':driftStatus} 		
    write_json(monitoring_status,targetPath/IOFiles['monitoring'])
    output = {'Status':'SUCCESS'}
    output.update(output_json)    	
    return(json.dumps(output))        
        
	
if __name__ == '__main__':        
    parser = argparse.ArgumentParser()        
    parser.add_argument('-i', '--inputUri', help='Training Data Location')

    args = parser.parse_args()        
    config_file = Path(__file__).parent/'config.json'        
    if not Path(config_file).exists():        
        raise ValueError(f'Config file is missing: {config_file}')        
    config = read_json(config_file) 	
    if args.inputUri:        
        if 	args.inputUri != '': 
            config['inputUriExternal'] = args.inputUri
        else:
            config['inputUriExternal'] = None
    else:
        config['inputUriExternal'] = None
    try:        
        print(monitoring(config))        
    except Exception as e:        
        if get_logger():
            get_logger().error(e, exc_info=True)
        status = {'Status':'Failure','Message':str(e)}        
        print(json.dumps(status))
