from flask import Flask, request, jsonify
from spellchecker import SpellChecker
import re
from better_profanity import profanity
from datetime import datetime
import requests
import nltk
from nltk import word_tokenize, pos_tag
import difflib
import PyPDF2


nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# @Author - Megha Sharma 
# Exercise 2 - Three Apis Analyze statement; Compare pdf statement; check endpoints 
# Submitting to Blaash.io


app = Flask(__name__)

spell = SpellChecker()

profanity.load_censor_words()  

@app.route('/analyze_statement', methods=['POST'])
def analyze_statement():
    statement = request.json.get('statement', '')

    words = statement.split()
    misspelled_words = spell.unknown(words)

    if profanity.contains_profanity(statement):
        profanity_detected = [word for word in words if profanity.contains_profanity(word)]
    else:
        profanity_detected = []
    tokens = word_tokenize(statement)
    position_tag = pos_tag(tokens)
    nouns = [word for word, pos in position_tag if pos in ['NN', 'NNS']]
    nouns_sorted = sorted(nouns, key=len)

    return jsonify({
        'misspelled_words': list(misspelled_words),
        'profanity_detected': profanity_detected,
        'nouns_sorted': nouns_sorted
    })

@app.route('/check_endpoint', methods=['POST'])
def check_endpoint():
    endpoint = request.json.get('endpoint', '')
    try:
        response = requests.get(endpoint)
        response_code = response.status_code
        is_alive = response.ok
    except requests.exceptions.RequestException:
        response_code = None
        is_alive = False
    
    return jsonify({
        'QueriedAt': datetime.now().isoformat(),
        'ResponseCode': response_code,
        'IsAlive': is_alive
    })

def read_pdf_text(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def compare_texts(text1, text2):
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))
    
    change_groups = {}
    paragraph_id = 0
    for line in diff:
        if line.startswith('+ ') or line.startswith('- '):
            paragraph_id += 1
            if paragraph_id not in change_groups:
                change_groups[paragraph_id] = []
            change_groups[paragraph_id].append(line)
    
    return change_groups

@app.route('/compare_pdfs', methods=['POST'])
def compare_pdfs():
    pdf1 = request.files['file1']
    pdf2 = request.files['file2']
    
    doc1 = read_pdf_text(pdf1)
    doc2 = read_pdf_text(pdf2)
    
    changes = compare_texts(doc1, doc2)
    
    return jsonify(changes)



@app.route('/test',methods=['GET'])
def test():
    return jsonify({
        'message': "working"
    })

if __name__ == '__main__':
    app.run(debug=True)

