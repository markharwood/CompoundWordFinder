from elasticsearch import helpers
from elasticsearch.client import Elasticsearch, utils
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import csv
import os
import math


es = Elasticsearch()

queriesFile="./data/queryVolumes.csv"
textFile="./data/product_descriptions.txt"



indexName="temp_phrases"
shingledField="text.shingled"
shingleFreeField="text"



def indexText():
    indexSettings = {
        "settings": {
            "index.number_of_replicas": 0,
            "index.number_of_shards": 1,
            "analysis": {
                "analyzer": {
                    "analyzer_shingled": {
                        "tokenizer": "standard",
                        "filter": [
                            # "apostrophe",
                            "lowercase",
                            "filter_shingle",
                            # "filter_light_english"
                        ]
                    },
                    "analyzer_unshingled": {
                        "tokenizer": "standard",
                        "filter": [
                            # "apostrophe",
                            "lowercase",
                            # "filter_light_english"
                        ]
                    }
                },
                "filter": {
                    "filter_shingle": {
                        "type": "shingle",
                        "max_shingle_size": 2,
                        "min_shingle_size": 2,
                        "filler_token": "",
                        "token_separator": "",
                        "output_unigrams": "false"
                    },
                    "filter_light_english":{
                        "type": "stemmer",
                        "name": "light_english"
                    }
                }
            }
        },
        "mappings": {
            "_doc": {
                "properties": {
                    "text": {
                        # The unshingled field
                        "type": "text",
                        "analyzer": "analyzer_unshingled",
                        "fields":{
                            "shingled":{
                                "type":"text",
                                "analyzer":"analyzer_shingled"
                            }
                        }
                    }
                }
            }
        }
    }
    es.indices.delete(index=indexName, ignore=[400, 404])
    es.indices.create(index=indexName, body=indexSettings)

    actions = []

    bytesRead=0

    st = os.stat(textFile)
    fileSize = st.st_size
    lastProgressMessage=""
    with open(textFile) as infile:
        for line in infile:
            bytesRead+=len(line)
            doc = {
                "text": line
            }
            action = {
                "_index": indexName,
                '_op_type': 'index',
                "_type": "_doc",
                "_source": doc
            }
            actions.append(action)
            percentComplete = int((float(bytesRead)/float(fileSize)) *100)
            progressMessage = "\t"+ str(percentComplete) + "% complete"
            if progressMessage!=lastProgressMessage:
                lastProgressMessage=progressMessage
                sys.stdout.write('\r')
                sys.stdout.write(progressMessage)
                sys.stdout.flush()

            if len(actions) >= 1000:
                helpers.bulk(es, actions)
                ## TO check for failures and take appropriate action
                del actions[0:len(actions)]

    if len(actions) >= 0:
        helpers.bulk(es, actions)
    print

checked=[]
phraseUseCounts={}

def analyzeSearchTerm(searchInput, searchesCount):
    analyzeRequest={
        "text": searchInput,
        "field": shingledField
    }
    tokens = es.transport.perform_request('POST', "/"+indexName+"/_analyze", body=analyzeRequest)["tokens"]

    shingles=[]
    termQueries=[]
    for token in tokens:
        if token["type"]!="shingle":
            continue
        tStr=token["token"]
        if tStr.isdigit():
            # All-number phrases make no sense eg 9/11 joined together as 911
            continue
        if tStr not in shingles:
            shingles.append(tStr)
            termQueries.append({"term":{shingledField:tStr}})



    if len(shingles)>0:
        q={
          "size": 0,
          "query": {
            "bool": {
              "should": termQueries
            }
          },
          "aggs": {
            "sample": {
              "sampler": {
                "shard_size": 100
              },
              "aggs": {
                "keyphrases": {
                  "significant_text": {
                    "field": shingledField,
                    #      A note on the usual significant_text settings designed to filter garbage:
                    #      Theoretically some rogue content with duplicated typos could pollute the discoveries
                    #      without the duplicate filter below. However this is mitigated by the fact we are only
                    #      analyzing popular queries which are therefore likely to be sane search terms.
                    #      For this reason, I've turned de-dup off and set min_doc_counts to minimum values.
                    # "filter_duplicate_text": True,
                    "min_doc_count":1,
                    "shard_min_doc_count":1,
                    "include": shingles
                  }
                }
              }
            }
          }
        }
        results= es.search(index=indexName, body=q)["aggregations"]["sample"]["keyphrases"]["buckets"]
        sigShingles = []
        sigShingleToSourceText={}
        if len(results)>0:
            for bucket in results:
                sigShingles.append(bucket["key"])
                # Find the associated
                for token in tokens:
                    if token["type"] != "shingle":
                        continue

                    tStr = token["token"]
                    if tStr in sigShingles:
                        start=token["start_offset"]
                        end=token["end_offset"]
                        sigShingleToSourceText[tStr]= searchInput[start:end]





            # Some additional analysis - output the phrase typos (eg "elastic search") when product is single term eg elasticsearch
            for phrase in sigShingles:
                if phrase not in checked:
                    checked.append(phrase)
                    q = {
                        "query": {
                            "term": {shingleFreeField: phrase}
                        }
                    }
                    results = es.search(index=indexName, body=q)
                    if results["hits"]["total"] >= 1 and phrase not in searchInput:
                        q = {
                            "query": {
                                "match_phrase": {shingleFreeField: sigShingleToSourceText[phrase]}
                            }
                        }
                        phraseResults = es.search(index=indexName, body=q)

                        phraseUseCounts[phrase] = {
                            "docText":phrase,
                            "queryText":sigShingleToSourceText[phrase],
                            "qf":0,
                            "df":results["hits"]["total"],
                            "dfp":phraseResults["hits"]["total"]
                        }

                if phrase in phraseUseCounts:
                    phraseUseCounts[phrase]["qf"] = phraseUseCounts[phrase]["qf"] +searchesCount



print "Indexing text..."
indexText()


print "Profiling queries"
st = os.stat(queriesFile)
fileSize = st.st_size
bytesRead =0
with open(queriesFile) as infile:
    for line in infile:
        if bytesRead == 0:
            bytesRead += len(line)
            continue
        bytesRead += len(line)
        row = csv.reader([line]).next()

        percentComplete = int((float(bytesRead) / float(fileSize)) * 100)
        progressMessage = "\t" + str(percentComplete) + "% complete"
        sys.stdout.write('\r')
        sys.stdout.write(progressMessage)
        sys.stdout.flush()
        analyzeSearchTerm(row[0].lower(), int(row[1]))
    print

# Used for sorting interesting compound words
def scoreShingleSignificance(x):
    # Take the square root of values to narrow gap between wildly popular things and things that occur only once
    compoundWordCount = math.sqrt(x["df"])
    phraseCount = math.sqrt(x["dfp"])
    compoundWordProbability = float(compoundWordCount)/float(compoundWordCount + phraseCount)
    # Sort by query volume multiplied by the probability search input is a compound word
    return math.sqrt(x["qf"])*compoundWordProbability

#  Sort the phrases by a combo of query popularity and likelihood of being a compound word - useful for reviewing as candidate synonym rules
sortedPhraseUseCounts=sorted(phraseUseCounts.values(), reverse=True, key=lambda x: scoreShingleSignificance(x))
print "queryText, QF, DFAsPhrase,  docShingle, DFAsShingle"
for phraseCount in sortedPhraseUseCounts:
    print phraseCount["queryText"]+ ",", str(phraseCount["qf"])+ ",",str(phraseCount["dfp"]), ",", phraseCount["docText"]+ ",",phraseCount["df"]

