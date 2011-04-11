"""
Guyfinder.py
Jeremy B. Merrill
March 27, 2011
Find all instances of "guy" and "you guys" in a provided HTML document (intended for Friends transcripts)
Also, to the best extent possible, return the speaker and relevant context for determining the referent.

"""

import re
import string
import csv
import sys
import pprint
import getopt
import MySQLdb

BACK_SIZE = 8
FORE_SIZE = 3

def processTranscript(transcript):
    """ Return a list of tokens of guy in the provided transcript (all one string).

    Before processing, blank lines are removed
    The list that is returned has five elements
        1. The full line
        2. The speaker.
        3. Whether the token is a "you guys" token ( => true) or some other use of "guy" ( => false)
        4. A guess (if I get around to implementing it) who the referent(s) is/are.
        5. The surrounding lines for context for manual referent coding.
    """

    paragraphs = transcript.split("</p>")
    paragraphs = [re.sub(r'\r\n\r\n',"\n",x) for x in paragraphs]
    listofguytokens = []

    for i,paragraph in enumerate(paragraphs):
        guytoken = {}
        speaker = ""
        youguys = None
        context = None

        paragraph = re.sub('<p align="left">',"",paragraph)
        paragraph = re.sub('<p>',"",paragraph)
        
        guyre = re.compile(r"guy", re.I)
        match = guyre.search(paragraph) #is there a token of guy in the paragraph?
        if match:
            #find the speaker
            speakerre = re.compile(r"<b>([A-Z ]*):</b> ",re.I) #match 01[0-9]{2}.html
            speakermatchobj = speakerre.search(paragraph)
            speakerre_strong = re.compile(r"<strong>([A-Z ]*):?</strong>:? ",re.I) #match 10[0-9]{2}.html
            speakermatchobj_strong = speakerre_strong.search(paragraph)
            if speakermatchobj or speakermatchobj_strong:
                try:
                    speaker = speakermatchobj.group(1)
                except AttributeError:
                    speaker = speakermatchobj_strong.group(1)
               
                youguysre = re.compile(r"you guys", re.I)
                if not youguysre.search(paragraph):
                    youguys = False
                else:
                    youguys = True

                #create the token dict to be coded by the user.
                context = paragraphs[max(1, i-BACK_SIZE):min(i+FORE_SIZE, len(paragraphs))]

                for j,contextline in enumerate(context):
                    context[j] = re.sub("<[^>]*>","",contextline) #strip html
                
                guytoken = {"paragraph":re.sub("<[^>]*>","",paragraph), "speaker":speaker, "youguys":youguys, "context":context}

                #ask the user to code the token as Female, Mixed, Male
                prettyprint(guytoken)

                listofguytokens.append(guytoken)
                
                #deal with multiple tokens in a line?
    return listofguytokens

def prettyprint(token):
    """ Prettily print a single token object.

        E.g. Chandler, "you guys"
    """
    output = token["speaker"] + ", "
    if token["youguys"]:
        output += "\"you guys\"\n"
    else:
        output += "\"guy\"\n"

    contextstr = ""
    for paragraph in token['context']:
        contextstr += paragraph

    for i,line in enumerate(contextstr.strip("\n").split("\n")):
        #print """xxx  """ + token["paragraph"][1:12].strip()
        #print """xxx  """ + line[0:10].strip() #11 for season 1
        if (line[0:10].strip() == token["paragraph"][1:12].strip()): #fix >>> thing
            output += ">>>\t" + re.sub("\n","",line) + "\n"
        else:
            output += "\t" + re.sub("\n","",line) + "\n"
        
    print output.strip("\n")

def writeToCSV(outputfilename, inputfilename, listoftokens):
    f = open(outputfilename, "a")
    csvwriter = csv.writer(f, delimiter='$', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for token in listoftokens:
        modtoken = [inputfilename]
        # uytoken = {"paragraph":re.sub("<[^>]*>","",paragraph), "speaker":speaker, "youguys":youguys, "context":context}
        modtoken.append(token["speaker"])
        if token["youguys"]:
            modtoken.append("you guys")
        else:
            modtoken.append("guy")

        escparagraph = re.sub("\n","",re.sub("\r\n","",token["paragraph"]))
        modtoken.append(escparagraph)
        print modtoken
        csvwriter.writerow(modtoken)
    f.close()



##########################################
try:
    inputfilename = sys.argv[1]
except IndexError:
    inputfilename = "friendsalltranscripts/0101.html"
try:
    outputfilename = sys.argv[2]
except IndexError:
    outputfilename = "defaultoutput.csv"

f = open(inputfilename)
transcript = f.read() #instead of readlines, I could just read the whole thing, then separate based on <p>,</p> tags
listoftokens = processTranscript(transcript)
print len(listoftokens)

writeToCSV(outputfilename, inputfilename, listoftokens)

print "Done with %s", inputfilename
