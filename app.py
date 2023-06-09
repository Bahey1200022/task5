from flask import Flask , request, render_template,jsonify
import json
from flask_cors import CORS, cross_origin
import numpy as np
from logic import Logic
from scipy import signal
import scipy.signal

logic = Logic()


        

output= [0]
allpasszeros, allpasspoles= [],[]
filterangles, finalAngles, allPassAngles= [0],[0],[0]
totalzeros, totalpoles= [0],[0]


app = Flask(__name__) 

@app.route('/', methods= ['GET','POST'])
def home():
    return render_template('index.html')


@app.route('/getFilter', methods=['POST'])
@cross_origin()
def getFrequencyResponce():
    global filterangles, allPassAngles, totalzeros, totalpoles
    if request.method == 'POST':
        zerosAndPoles = json.loads(request.data)
        logic.zeros = logic.parseToComplex(zerosAndPoles['zeros'])
        logic.poles = logic.parseToComplex(zerosAndPoles['poles'])
        logic.gain = zerosAndPoles['gain']
        logic.b , logic.a  = scipy.signal.zpk2tf(logic.zeros, logic.poles, logic.gain) #transform to difference equation
        logic.filterOrder = max(len(logic.zeros), len(logic.poles))
        w, filterangles, magnitude = logic.frequencyResponse()
        filterangles= np.add(allPassAngles, filterangles)
    
        response_data = {
                'w': w.tolist(),
                'angels': filterangles.tolist(),
                'magnitude': magnitude.tolist()
            }
        # zero,pole,k= logic.getfrompair()
        # print(zero)
        # print(pole)
        totalzeros= logic.zeros
        totalpoles= logic.poles
        
    return jsonify(response_data)

@app.route('/getAllPassFilter', methods=['POST', 'GET'])
def getAllPassFilterData():
    count=0
    if request.method == 'POST':
        data = json.loads(request.data)
        logic.allPassCoeffients = data['a']
        for a in logic.allPassCoeffients:
            logic.allPassCoeffients[count]= logic.convert(a)
            count+=1
        w, filter_angles = logic.getAllPassFrequencyResponse()
        response_data = {
            'w': w.tolist(),
            'angels': filter_angles.tolist(),
        }
        return jsonify(response_data)
    else:
        return 'There is no Post request'
    
    
@app.route('/digitalFilter', methods=['POST'])   #filter reviewer function
def digitalFilter():
    jsonData = request.get_json()
    z = jsonData['zerosvalues']
    p = jsonData['polesvalues']
    flag = jsonData['flag']
    z = [complex(x[0], x[1]) for x in z]
    p = [complex(x[0], x[1]) for x in p]
    
    alp_review = Logic()
    alp_review.zeros = z
    alp_review.poles = p
    alp_review.gain = 1
    w, h_phase, magnitude = alp_review.frequencyResponse()

    
    return [w.tolist(),  h_phase.tolist()]     
    
    
@app.route('/getphase_correctors', methods=['POST'])
def modifiefilter():
    if request.method == 'POST':
        jsonData = request.get_json()
        z = jsonData['z']
        p = jsonData['p']
        z = [complex(x[0], x[1]) for x in z]
        p = [complex(x[0], x[1]) for x in p]
        logic.zeros=(logic.zeros)+z
        logic.poles=(logic.poles)+p
        logic.gain=1
        logic.b , logic.a  = scipy.signal.zpk2tf(logic.zeros, logic.poles, logic.gain) 
        logic.filterOrder = max(len(logic.zeros), len(logic.poles))
        w, h_phase, magnitude = logic.frequencyResponse()

    
        return [w.tolist(),  h_phase.tolist()]
        

        
@app.route('/delete', methods=['POST'])
def deletecomp():
    if request.method == 'POST':
        jsonData = request.get_json()
        zeros = jsonData['zeros']
        poles = jsonData['poles']

        print(zeros)
        print(poles)
        print(logic.zeros)
        print(logic.poles)


        # Delete zeros from logic.zeros
        logic.zeros = [zero for zero in logic.zeros if zero not in zeros]

        # Delete poles from logic.poles
        logic.poles = [pole for pole in logic.poles if pole not in poles]
        print(logic.zeros)
        print(logic.poles)
        

        w, h_phase, magnitude = logic.frequencyResponse()
        return [w.tolist(), h_phase.tolist()]
    

signal = [1 for i in range(15)]

@app.route('/applyFilter', methods=['POST'])
def applyFilter():
        jsonData = request.get_json()
        input_point = float(jsonData['signalPoint'])
        signal.append(input_point)
        if len(signal) >  2 * logic.filterOrder and len(signal)>50:
            del signal[0:logic.filterOrder]
        output_signal = logic.applyFilter(signal)
        output_point = output_signal[-1]
        
        return [float(output_point)] 


        

if __name__ == '__main__':
    app.run(debug=True)