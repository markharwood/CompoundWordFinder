# CompoundWordFinder
This is a tool to find compound words commonly misspelled in queries (eg "elastic search").

The outputs would be of use in creating either:

* synonym rules for analyzers - e.g. "elastic search = elasticsearch" or
* rules for rewriting queries e.g. queries for "ted baker blue dress" would extract brandname "ted baker" as a "must" phrase and run the remaining query text using laxer operators

### Input files format



#### Query file 
CSV format with 2 columns:
1) query string e.g. fit bit
2) popularity

#### Document file
Plain text, one line per document e.g. a product description such as "fitbit"

### Running the code

* Unzip the example data files provided as part of this repo into the `data` directory:
* Run python FindCompoundWords.py (this is Python 2.7 compatible code)

A temporary index called `temp_phrases` is created to perform the analysis.

### Example output
The query strings that look to be compound words are printed, sorted by a combination of popularity and likelihood to be a compound word.


QueryText| Number of uses in queries| Number of uses as phrase in docs|  compound word (shingle)| Number of uses as compound word in docs
---| --| --| ---| ---
play station| 2182| 1 | playstation| 3817
skull candy| 1432| 1 | skullcandy| 314
blue tooth| 1102| 1 | bluetooth| 688
go pro| 1166| 1 | gopro| 101
sound bar| 1551| 18 | soundbar| 86
web cam| 1057| 12 | webcam| 109
hd tv| 584| 3 | hdtv| 2556
tom tom| 838| 17 | tomtom| 193
ear buds| 613| 6 | earbuds| 288
blue ray| 1848| 1 | blueray| 1
compact flash| 550| 1 | compactflash| 95
on star| 660| 1 | onstar| 15
mini dv| 462| 2 | minidv| 294
coffee maker| 563| 15 | coffeemaker| 270
anti virus| 573| 20 | antivirus| 132
nook color| 517| 3 | nookcolor| 26
dragon ball| 772| 301 | dragonball| 459
hero 2| 513| 10 | hero2| 34
ice maker| 513| 23 | icemaker| 66
go phone| 297| 2 | gophone| 39
32 gb| 235| 4 | 32gb| 298
fall out| 436| 22 | fallout| 73
tablet s| 268| 11 | tablets| 196
i home| 177| 1 | ihome| 98
psp go| 304| 3 | pspgo| 14
boom box| 211| 9 | boombox| 181
google tv| 2505| 12 | googletv| 1
sub woofer| 124| 2 | subwoofer| 861
leap frog| 127| 2 | leapfrog| 347
invisible shield| 143| 11 | invisibleshield| 279
big bang| 1033| 81 | bigbang| 11
flat screen| 827| 47 | flatscreen| 8
cd-r| 515| 213 | cdr| 72
smart start| 207| 6 | smartstart| 9
display port| 120| 5 | displayport| 33
4 s| 71| 4 | 4s| 356
ps 3| 67| 1 | ps3| 160
3 pc| 59| 2 | 3pc| 308
desk tops| 49| 0 | desktops| 52
hot spot| 142| 17 | hotspot| 31
back up| 224| 113 | backup| 65

...



